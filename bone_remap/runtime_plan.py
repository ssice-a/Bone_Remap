"""Derived runtime scope for retarget solve, preview, bake, and cleanup."""

from __future__ import annotations

from collections import Counter
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
    target_channels: tuple[TargetChannelPlan, ...]


@dataclass(frozen=True)
class RuntimePlan:
    rows: tuple[RuntimePlanRow, ...]
    mapped_target_names: tuple[str, ...]
    skipped_rows: int
    skipped_links: int
    messages: list[state.ValidationMessage]


def build_runtime_plan(profile, source_armature: Object, target_armature: Object) -> RuntimePlan:
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
            target_bind_matrix = target_bind_matrix_for_bone(target_armature, link.target_bone_name, profile)
            if target_bind_matrix is None:
                skipped_links += 1
                messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {link.target_bone_name}"))
                continue
            target_channels.append(TargetChannelPlan(link.target_bone_name, target_bind_matrix))

        if target_channels:
            rows.append(RuntimePlanRow(source_bone_name, source_work_pose_matrix, tuple(target_channels)))

    return RuntimePlan(
        rows=tuple(rows),
        mapped_target_names=tuple(mapped_target_names(profile)),
        skipped_rows=skipped_rows,
        skipped_links=skipped_links,
        messages=messages,
    )


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


def target_bind_matrix_for_bone(target_armature: Object, target_bone_name: str, profile=None) -> Matrix | None:
    if not _is_armature(target_armature):
        return None

    target_bone = target_armature.data.bones.get(target_bone_name)
    if target_bone is None:
        return None

    if profile is not None:
        for item in profile.target_bind_matrices:
            if item.target_bone_name == target_bone_name:
                return work_pose.matrix_from_flat(item.matrix)

    return target_bone.matrix_local.copy()


def target_write_order(target_armature: Object, target_bone_names: Iterable[str]) -> list[str]:
    return sorted(target_bone_names, key=lambda bone_name: _bone_depth(target_armature, bone_name))


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
        mapped_target_names=tuple(mapped_target_names(profile)),
        skipped_rows=0,
        skipped_links=0,
        messages=messages,
    )


def _is_armature(obj) -> bool:
    return obj is not None and obj.type == "ARMATURE"


def _bone_depth(target_armature: Object, bone_name: str) -> int:
    bone = target_armature.data.bones.get(bone_name) if _is_armature(target_armature) else None
    depth = 0
    while bone is not None and bone.parent is not None:
        depth += 1
        bone = bone.parent
    return depth
