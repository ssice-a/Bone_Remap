"""Optional target-side calibration commands."""

from __future__ import annotations

import bpy
from bpy.types import Operator
from mathutils import Vector

from . import mapping, state, work_pose


def channel_align_active_profile(context) -> tuple[int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    if not work_pose.has_saved_work_pose(profile):
        return 0, "Channel Alignment requires a saved Work Pose."

    source_heads = {
        item.bone_name: work_pose.matrix_from_flat(item.matrix).translation.copy()
        for item in profile.work_pose_matrices
    }
    target = active_context.target_armature
    mapped_pairs = [
        (row.source_bone_name, link.target_bone_name)
        for row in profile.mapping_rows
        for link in row.target_links
    ]
    if not mapped_pairs:
        return 0, "Mapping Table has no mapped target channels."

    original_active = context.view_layer.objects.active
    original_mode = original_active.mode if original_active is not None else "OBJECT"
    if original_active is not None and original_mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    moved = 0
    try:
        for source_bone_name, target_bone_name in mapped_pairs:
            new_head = source_heads.get(source_bone_name)
            edit_bone = target.data.edit_bones.get(target_bone_name)
            if new_head is None or edit_bone is None:
                continue

            old_vector = edit_bone.tail - edit_bone.head
            edit_bone.head = Vector((new_head.x, new_head.y, new_head.z))
            edit_bone.tail = edit_bone.head + old_vector
            moved += 1
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
        if original_active is not None:
            context.view_layer.objects.active = original_active
            if original_mode != "OBJECT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except RuntimeError:
                    pass

    return moved, f"Aligned {moved} mapped target channel heads."


def refresh_target_bind_active_profile(context) -> tuple[int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    target = active_context.target_armature
    target_names = mapping.mapped_target_names(profile)
    if not target_names:
        return 0, "Mapping Table has no mapped target channels."

    for target_bone_name in target_names:
        target_bone = target.data.bones.get(target_bone_name)
        if target_bone is None:
            continue
        item = _find_or_create_target_bind(profile, target_bone_name)
        item.matrix = work_pose.flatten_matrix(target_bone.matrix_local)

    _solve_live_preview_if_enabled(context)
    return len(target_names), f"Refreshed target bind/reference for {len(target_names)} mapped channels."


def _find_or_create_target_bind(profile, target_bone_name: str):
    for item in profile.target_bind_matrices:
        if item.target_bone_name == target_bone_name:
            return item
    item = profile.target_bind_matrices.add()
    item.target_bone_name = target_bone_name
    return item


def _solve_live_preview_if_enabled(context) -> None:
    from . import live_preview

    live_preview.solve_if_enabled(context, reason="target_bind_refresh")


class BRM_OT_channel_align_heads(Operator):
    bl_idname = "bone_remap.channel_align_heads"
    bl_label = "Align Target Heads"
    bl_description = "Move mapped target bone heads to source Work Pose control-frame pivots"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        count, message = channel_align_active_profile(context)
        if count == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


class BRM_OT_target_bind_refresh(Operator):
    bl_idname = "bone_remap.target_bind_refresh"
    bl_label = "Refresh Target Bind"
    bl_description = "Store current mapped target bind/reference matrices after explicit target calibration"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        count, message = refresh_target_bind_active_profile(context)
        if count == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_channel_align_heads,
    BRM_OT_target_bind_refresh,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
