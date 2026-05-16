"""Hierarchy-safe pose matrix application helpers."""

from __future__ import annotations

from bpy.types import Object
from mathutils import Matrix


def capture_pose_matrix_map(armature: Object) -> dict[str, Matrix]:
    return {
        pose_bone.name: pose_bone.matrix.copy()
        for pose_bone in armature.pose.bones
    }


def apply_pose_matrix_map(
    context,
    armature: Object,
    pose_matrix_map: dict[str, Matrix],
    update_view_layer: bool = True,
) -> int:
    """Apply final visible pose matrices by writing each bone's local basis.

    `pose_matrix_map` is expressed in armature object space. Parent bones present in
    the map are treated as planned writes; missing parents use the armature's
    current pose, so partial mapped target writes remain absolute and predictable.
    """

    current_pose_matrix_map = capture_pose_matrix_map(armature)
    basis_matrix_map = basis_matrix_map_from_pose_matrices(
        armature,
        pose_matrix_map,
        current_pose_matrix_map,
    )

    applied = 0
    for data_bone in iter_data_bones_depth_first(armature):
        basis_matrix = basis_matrix_map.get(data_bone.name)
        pose_bone = armature.pose.bones.get(data_bone.name)
        if basis_matrix is None or pose_bone is None:
            continue
        pose_bone.matrix_basis = basis_matrix
        applied += 1

    if applied and update_view_layer:
        context.view_layer.update()
    return applied


def basis_matrix_map_from_pose_matrices(
    armature: Object,
    pose_matrix_map: dict[str, Matrix],
    fallback_parent_pose_matrix_map: dict[str, Matrix] | None = None,
) -> dict[str, Matrix]:
    basis_matrix_map = {}
    fallback_parent_pose_matrix_map = fallback_parent_pose_matrix_map or {}

    for data_bone in iter_data_bones_depth_first(armature):
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


def iter_data_bones_depth_first(armature: Object):
    for data_bone in armature.data.bones:
        if data_bone.parent is None:
            yield from _walk_data_bone_tree(data_bone)


def _walk_data_bone_tree(data_bone):
    yield data_bone
    for child_bone in data_bone.children:
        yield from _walk_data_bone_tree(child_bone)
