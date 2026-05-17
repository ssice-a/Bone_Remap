"""Derived runtime scope for retarget solve, preview, bake, and cleanup."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from bpy.types import Object
from mathutils import Matrix

from . import state, work_pose


@dataclass(frozen=True)
class TargetChannelPlan:
    bone_name: str
    bind_matrix: Matrix


@dataclass(frozen=True)
class RuntimePlanRow:
    source_bone_name: str
    source_work_pose_matrix: Matrix
    source_work_pose_inverse: Matrix
    target_channels: tuple[TargetChannelPlan, ...]


@dataclass(frozen=True)
class RuntimePlan:
    rows: tuple[RuntimePlanRow, ...]
    mapped_source_names: tuple[str, ...]
    mapped_target_names: tuple[str, ...]
    mapped_target_write_order: tuple[str, ...]
    scoped_rows_by_source: dict[str, tuple[RuntimePlanRow, ...]]
    scoped_target_write_order_by_source: dict[str, tuple[str, ...]]
    affected_target_names_by_source: dict[str, frozenset[str]]
    skipped_rows: int
    skipped_links: int
    messages: list[state.ValidationMessage]


_RUNTIME_PLAN_CACHE: dict[tuple[int, int, int, int, int, int], RuntimePlan] = {}


def invalidate_runtime_plan(profile) -> None:
    if profile is None:
        return

    profile_pointer = profile.as_pointer()
    for cache_key in list(_RUNTIME_PLAN_CACHE):
        if cache_key[0] == profile_pointer:
            del _RUNTIME_PLAN_CACHE[cache_key]

    if hasattr(profile, "runtime_plan_revision"):
        profile.runtime_plan_revision += 1


def clear_runtime_plan_cache() -> None:
    _RUNTIME_PLAN_CACHE.clear()


def build_runtime_plan(profile, source_armature: Object, target_armature: Object) -> RuntimePlan:
    cache_key = _runtime_plan_cache_key(profile, source_armature, target_armature)
    cached_plan = _RUNTIME_PLAN_CACHE.get(cache_key)
    if cached_plan is not None:
        return cached_plan

    plan = _build_runtime_plan(profile, source_armature, target_armature)
    _RUNTIME_PLAN_CACHE[cache_key] = plan
    return plan


def _build_runtime_plan(profile, source_armature: Object, target_armature: Object) -> RuntimePlan:
    messages: list[state.ValidationMessage] = []
    rows: list[RuntimePlanRow] = []
    skipped_rows = 0
    skipped_links = 0

    if not work_pose.has_saved_work_pose(profile):
        return _empty_plan(profile, [state.ValidationMessage("ERROR", "Save Work Pose before solving.")])
    if not profile.mapping_rows:
        return _empty_plan(profile, [state.ValidationMessage("ERROR", "Mapping Table is empty.")])

    work_pose_matrices = work_pose_matrix_by_bone(profile)
    if not work_pose_matrices:
        return _empty_plan(profile, [state.ValidationMessage("ERROR", "Saved Work Pose has no matrices.")])

    source_bones = {bone.name for bone in source_armature.pose.bones} if _is_armature(source_armature) else set()
    target_bind_matrices = target_bind_matrix_by_bone(profile)

    for mapping_row in profile.mapping_rows:
        source_bone_name = mapping_row.source_bone_name
        source_work_pose_matrix = work_pose_matrices.get(source_bone_name)

        if source_bone_name not in source_bones:
            skipped_rows += 1
            messages.append(state.ValidationMessage("ERROR", f"Invalid source bone: {source_bone_name}"))
            continue
        if source_work_pose_matrix is None:
            skipped_rows += 1
            messages.append(state.ValidationMessage("ERROR", f"Missing Work Pose matrix: {source_bone_name}"))
            continue
        if not mapping_row.target_links:
            skipped_rows += 1
            messages.append(state.ValidationMessage("WARNING", f"Unmapped row: {source_bone_name}"))
            continue

        target_channels = []
        for link in mapping_row.target_links:
            target_bone = target_armature.data.bones.get(link.target_bone_name) if _is_armature(target_armature) else None
            if target_bone is None:
                skipped_links += 1
                messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {link.target_bone_name}"))
                continue
            target_bind_matrix = target_bind_matrices.get(link.target_bone_name, target_bone.matrix_local.copy())
            target_channels.append(TargetChannelPlan(link.target_bone_name, target_bind_matrix))

        if target_channels:
            rows.append(
                RuntimePlanRow(
                    source_bone_name,
                    source_work_pose_matrix,
                    source_work_pose_matrix.inverted_safe(),
                    tuple(target_channels),
                )
            )

    mapped_names = tuple(mapped_target_names(profile))
    mapped_write_order = tuple(target_write_order(target_armature, mapped_names))
    scoped_rows_by_source, scoped_target_write_order_by_source, affected_target_names_by_source = _build_source_scopes(
        target_armature,
        tuple(rows),
        mapped_names,
        mapped_write_order,
    )
    return RuntimePlan(
        rows=tuple(rows),
        mapped_source_names=tuple(unique_names(row.source_bone_name for row in rows)),
        mapped_target_names=mapped_names,
        mapped_target_write_order=mapped_write_order,
        scoped_rows_by_source=scoped_rows_by_source,
        scoped_target_write_order_by_source=scoped_target_write_order_by_source,
        affected_target_names_by_source=affected_target_names_by_source,
        skipped_rows=skipped_rows,
        skipped_links=skipped_links,
        messages=messages,
    )


def solve_scope_for_sources(plan: RuntimePlan, source_bone_names: Iterable[str]) -> tuple[tuple[RuntimePlanRow, ...], tuple[str, ...]]:
    source_scope = tuple(unique_names(source_bone_names))
    if not source_scope:
        return (), ()

    if len(source_scope) == 1:
        source_bone_name = source_scope[0]
        return (
            plan.scoped_rows_by_source.get(source_bone_name, ()),
            plan.scoped_target_write_order_by_source.get(source_bone_name, ()),
        )

    if len(source_scope) >= len(plan.mapped_source_names) and set(source_scope).issuperset(plan.mapped_source_names):
        return plan.rows, plan.mapped_target_write_order

    scoped_source_names = set(source_scope)
    affected_target_names: set[str] = set()
    for source_bone_name in source_scope:
        affected_target_names.update(plan.affected_target_names_by_source.get(source_bone_name, ()))
    if not affected_target_names:
        return (), ()

    scoped_rows = []
    for row in plan.rows:
        if row.source_bone_name in scoped_source_names:
            scoped_rows.append(row)
            continue

        filtered_channels = tuple(
            target_channel
            for target_channel in row.target_channels
            if target_channel.bone_name in affected_target_names
        )
        if filtered_channels:
            scoped_rows.append(
                RuntimePlanRow(
                    row.source_bone_name,
                    row.source_work_pose_matrix,
                    row.source_work_pose_inverse,
                    filtered_channels,
                )
            )

    scoped_order = tuple(
        target_bone_name
        for target_bone_name in plan.mapped_target_write_order
        if target_bone_name in affected_target_names
    )
    return tuple(scoped_rows), scoped_order


def _runtime_plan_cache_key(profile, source_armature: Object, target_armature: Object) -> tuple[int, int, int, int, int, int]:
    return (
        profile.as_pointer(),
        int(getattr(profile, "runtime_plan_revision", 0)),
        source_armature.as_pointer(),
        source_armature.data.as_pointer(),
        target_armature.as_pointer(),
        target_armature.data.as_pointer(),
    )


def _build_source_scopes(
    target_armature: Object,
    rows: tuple[RuntimePlanRow, ...],
    mapped_target_names: tuple[str, ...],
    mapped_target_write_order: tuple[str, ...],
) -> tuple[
    dict[str, tuple[RuntimePlanRow, ...]],
    dict[str, tuple[str, ...]],
    dict[str, frozenset[str]],
]:
    direct_target_names_by_source: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        direct_target_names_by_source[row.source_bone_name].extend(
            target_channel.bone_name
            for target_channel in row.target_channels
            if target_channel.bone_name
        )

    mapped_target_set = set(mapped_target_names)
    scoped_rows_by_source: dict[str, tuple[RuntimePlanRow, ...]] = {}
    scoped_target_write_order_by_source: dict[str, tuple[str, ...]] = {}
    affected_target_names_by_source: dict[str, frozenset[str]] = {}

    for source_bone_name, direct_target_names in direct_target_names_by_source.items():
        affected_target_names = frozenset(
            target_descendant_names(
                target_armature,
                direct_target_names,
                mapped_target_set,
            )
        )
        affected_target_names_by_source[source_bone_name] = affected_target_names
        scoped_rows = []
        for row in rows:
            if row.source_bone_name == source_bone_name:
                scoped_rows.append(row)
                continue

            filtered_channels = tuple(
                target_channel
                for target_channel in row.target_channels
                if target_channel.bone_name in affected_target_names
            )
            if filtered_channels:
                scoped_rows.append(
                    RuntimePlanRow(
                        row.source_bone_name,
                        row.source_work_pose_matrix,
                        row.source_work_pose_inverse,
                        filtered_channels,
                    )
                )

        scoped_rows_by_source[source_bone_name] = tuple(scoped_rows)
        scoped_target_write_order_by_source[source_bone_name] = tuple(
            target_bone_name
            for target_bone_name in mapped_target_write_order
            if target_bone_name in affected_target_names
        )

    return scoped_rows_by_source, scoped_target_write_order_by_source, affected_target_names_by_source


def mapping_health_messages(profile, source_armature: Object | None, target_armature: Object | None) -> list[state.ValidationMessage]:
    messages: list[state.ValidationMessage] = []
    duplicate_counts = Counter()

    source_bones = {bone.name for bone in source_armature.pose.bones} if _is_armature(source_armature) else set()
    target_bones = {bone.name for bone in target_armature.pose.bones} if _is_armature(target_armature) else set()

    for mapping_row in profile.mapping_rows:
        if not mapping_row.target_links:
            messages.append(state.ValidationMessage("WARNING", f"Unmapped row: {mapping_row.source_bone_name}"))

        if mapping_row.source_bone_name not in source_bones:
            messages.append(state.ValidationMessage("ERROR", f"Invalid source bone: {mapping_row.source_bone_name}"))

        for link in mapping_row.target_links:
            duplicate_counts[link.target_bone_name] += 1
            if link.target_bone_name not in target_bones:
                messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {link.target_bone_name}"))

    for target_bone_name, count in duplicate_counts.items():
        if count > 1:
            messages.append(state.ValidationMessage("ERROR", f"Duplicate target assignment: {target_bone_name}"))

    if not profile.mapping_rows:
        messages.append(state.ValidationMessage("INFO", "Mapping Table is empty."))
    elif not messages:
        messages.append(state.ValidationMessage("INFO", "Mapping Table is healthy."))

    return messages


def mapped_target_names(profile) -> list[str]:
    return unique_names([
        link.target_bone_name
        for mapping_row in profile.mapping_rows
        for link in mapping_row.target_links
        if link.target_bone_name
    ])


def target_is_mapped(profile, target_bone_name: str) -> bool:
    return any(
        link.target_bone_name == target_bone_name
        for mapping_row in profile.mapping_rows
        for link in mapping_row.target_links
    )


def work_pose_matrix_by_bone(profile) -> dict[str, Matrix]:
    return {
        item.bone_name: work_pose.matrix_from_flat(item.matrix)
        for item in profile.work_pose_matrices
        if item.bone_name
    }


def target_bind_matrix_by_bone(profile) -> dict[str, Matrix]:
    if profile is None:
        return {}
    return {
        item.target_bone_name: work_pose.matrix_from_flat(item.matrix)
        for item in profile.target_bind_matrices
        if item.target_bone_name
    }


def target_bind_matrix_for_bone(
    target_armature: Object,
    target_bone_name: str,
    profile=None,
    target_bind_matrices: dict[str, Matrix] | None = None,
) -> Matrix | None:
    if not _is_armature(target_armature):
        return None

    target_bone = target_armature.data.bones.get(target_bone_name)
    if target_bone is None:
        return None

    if profile is not None or target_bind_matrices is not None:
        target_bind_matrices = target_bind_matrices or target_bind_matrix_by_bone(profile)
        target_bind_matrix = target_bind_matrices.get(target_bone_name)
        if target_bind_matrix is not None:
            return target_bind_matrix

    return target_bone.matrix_local.copy()


def target_write_order(target_armature: Object, target_bone_names: Iterable[str]) -> list[str]:
    depth_cache: dict[str, int] = {}
    return sorted(target_bone_names, key=lambda bone_name: _cached_bone_depth(target_armature, bone_name, depth_cache))


def target_descendant_names(
    target_armature: Object,
    root_target_names: Iterable[str],
    mapped_target_names: Iterable[str] | None = None,
) -> list[str]:
    if not _is_armature(target_armature):
        return []

    mapped_names = set(mapped_target_names) if mapped_target_names is not None else None
    seen: set[str] = set()
    ordered: list[str] = []
    stack = list(unique_names(root_target_names))

    while stack:
        bone_name = stack.pop()
        if bone_name in seen:
            continue
        seen.add(bone_name)

        if mapped_names is None or bone_name in mapped_names:
            ordered.append(bone_name)

        bone = target_armature.data.bones.get(bone_name)
        if bone is None:
            continue
        for child_bone in bone.children:
            stack.append(child_bone.name)

    return ordered


def unique_names(names: Iterable[str]) -> list[str]:
    seen = set()
    unique = []
    for name in names:
        if name and name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


def _empty_plan(profile, messages: list[state.ValidationMessage]) -> RuntimePlan:
    return RuntimePlan(
        rows=(),
        mapped_source_names=(),
        mapped_target_names=tuple(mapped_target_names(profile)),
        mapped_target_write_order=(),
        scoped_rows_by_source={},
        scoped_target_write_order_by_source={},
        affected_target_names_by_source={},
        skipped_rows=0,
        skipped_links=0,
        messages=messages,
    )


def _is_armature(obj) -> bool:
    return obj is not None and obj.type == "ARMATURE"


def _cached_bone_depth(target_armature: Object, bone_name: str, depth_cache: dict[str, int]) -> int:
    cached_depth = depth_cache.get(bone_name)
    if cached_depth is not None:
        return cached_depth

    bone = target_armature.data.bones.get(bone_name) if _is_armature(target_armature) else None
    if bone is None or bone.parent is None:
        depth_cache[bone_name] = 0
        return 0

    depth = 1 + _cached_bone_depth(target_armature, bone.parent.name, depth_cache)
    depth_cache[bone_name] = depth
    return depth
