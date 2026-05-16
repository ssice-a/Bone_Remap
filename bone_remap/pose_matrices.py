"""Hierarchy-safe pose matrix application helpers."""

from __future__ import annotations

from collections.abc import Iterable
from time import perf_counter

from bpy.types import Object
from mathutils import Matrix


def capture_pose_matrix_map(armature: Object, bone_names: Iterable[str] | None = None) -> dict[str, Matrix]:
    if bone_names is None:
        return {
            pose_bone.name: pose_bone.matrix.copy()
            for pose_bone in armature.pose.bones
        }

    captured = {}
    for bone_name in bone_names:
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            continue
        captured[bone_name] = pose_bone.matrix.copy()
    return captured


def apply_pose_matrix_map(
    context,
    armature: Object,
    pose_matrix_map: dict[str, Matrix],
    update_view_layer: bool = True,
    timings: dict[str, float] | None = None,
    ordered_bone_names: Iterable[str] | None = None,
) -> int:
    """Apply final visible pose matrices by writing each bone's local basis.

    `pose_matrix_map` is expressed in armature object space. Parent bones present in
    the map are treated as planned writes; missing parents use the armature's
    current pose, so partial mapped target writes remain absolute and predictable.
    """

    select_started_at = perf_counter()
    data_bones = tuple(
        _iter_named_data_bones_in_order(armature, ordered_bone_names)
        if ordered_bone_names is not None
        else iter_data_bones_depth_first(armature, pose_matrix_map.keys())
    )
    _record_timing(timings, "apply_select_ms", select_started_at)

    parent_started_at = perf_counter()
    fallback_parent_names = set()
    for data_bone in data_bones:
        parent = data_bone.parent
        if parent is not None and parent.name not in pose_matrix_map:
            fallback_parent_names.add(parent.name)

    current_pose_matrix_map = capture_pose_matrix_map(armature, fallback_parent_names)
    _record_timing(timings, "apply_parent_capture_ms", parent_started_at)

    basis_started_at = perf_counter()
    basis_matrix_map = basis_matrix_map_from_pose_matrices(
        armature,
        pose_matrix_map,
        current_pose_matrix_map,
        data_bones=data_bones,
    )
    _record_timing(timings, "apply_basis_ms", basis_started_at)

    write_started_at = perf_counter()
    applied = 0
    for data_bone in data_bones:
        basis_matrix = basis_matrix_map.get(data_bone.name)
        pose_bone = armature.pose.bones.get(data_bone.name)
        if basis_matrix is None or pose_bone is None:
            continue
        pose_bone.matrix_basis = basis_matrix
        applied += 1
    _record_timing(timings, "apply_write_ms", write_started_at)

    if applied and update_view_layer:
        update_started_at = perf_counter()
        context.view_layer.update()
        _record_timing(timings, "apply_view_update_ms", update_started_at)
    return applied


def basis_matrix_map_from_pose_matrices(
    armature: Object,
    pose_matrix_map: dict[str, Matrix],
    fallback_parent_pose_matrix_map: dict[str, Matrix] | None = None,
    data_bones: Iterable | None = None,
) -> dict[str, Matrix]:
    basis_matrix_map = {}
    fallback_parent_pose_matrix_map = fallback_parent_pose_matrix_map or {}
    data_bones = data_bones or iter_data_bones_depth_first(armature, pose_matrix_map.keys())

    for data_bone in data_bones:
        pose_matrix = pose_matrix_map.get(data_bone.name)
        if pose_matrix is None:
            continue

        kwargs = {}
        if data_bone.parent is not None:
            kwargs["parent_matrix"] = pose_matrix_map.get(
                data_bone.parent.name,
                fallback_parent_pose_matrix_map.get(
                    data_bone.parent.name,
                    data_bone.parent.matrix_local.copy(),
                ),
            )
            kwargs["parent_matrix_local"] = data_bone.parent.matrix_local.copy()

        basis_matrix_map[data_bone.name] = data_bone.convert_local_to_pose(
            pose_matrix,
            data_bone.matrix_local.copy(),
            invert=True,
            **kwargs,
        )

    return basis_matrix_map


def _record_timing(timings: dict[str, float] | None, key: str, started_at: float) -> None:
    if timings is not None:
        timings[key] = (perf_counter() - started_at) * 1000.0


def iter_data_bones_depth_first(armature: Object, bone_names: Iterable[str] | None = None):
    if bone_names is not None:
        yield from _iter_named_data_bones_depth_first(armature, bone_names)
        return

    for data_bone in armature.data.bones:
        if data_bone.parent is None:
            yield from _walk_data_bone_tree(data_bone)


def _iter_named_data_bones_depth_first(armature: Object, bone_names: Iterable[str]):
    depth_cache: dict[str, int] = {}
    data_bones = []
    seen = set()

    for bone_name in bone_names:
        if bone_name in seen:
            continue
        seen.add(bone_name)

        data_bone = armature.data.bones.get(bone_name)
        if data_bone is not None:
            data_bones.append(data_bone)

    for data_bone in sorted(data_bones, key=lambda bone: _cached_data_bone_depth(bone, depth_cache)):
        yield data_bone


def _iter_named_data_bones_in_order(armature: Object, bone_names: Iterable[str]):
    seen = set()
    for bone_name in bone_names:
        if bone_name in seen:
            continue
        seen.add(bone_name)

        data_bone = armature.data.bones.get(bone_name)
        if data_bone is not None:
            yield data_bone


def _cached_data_bone_depth(data_bone, depth_cache: dict[str, int]) -> int:
    cached_depth = depth_cache.get(data_bone.name)
    if cached_depth is not None:
        return cached_depth

    if data_bone.parent is None:
        depth_cache[data_bone.name] = 0
        return 0

    depth = 1 + _cached_data_bone_depth(data_bone.parent, depth_cache)
    depth_cache[data_bone.name] = depth
    return depth


def _walk_data_bone_tree(data_bone):
    yield data_bone
    for child_bone in data_bone.children:
        yield from _walk_data_bone_tree(child_bone)
