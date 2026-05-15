"""Motion Edit Mode entrypoints for Blender-native source action editing."""

from __future__ import annotations

import bpy
from bpy.types import Object, Operator

from . import live_preview, state


def ensure_motion_action(profile, source_armature: Object):
    animation_data = source_armature.animation_data_create()
    action = profile.active_motion_action or animation_data.action
    if action is None:
        action = bpy.data.actions.new(name=f"{source_armature.name}_Motion")
    animation_data.action = action
    profile.active_motion_action = action
    return action


def active_motion_action(profile, source_armature: Object):
    if profile.active_motion_action is not None:
        return profile.active_motion_action
    animation_data = source_armature.animation_data
    if animation_data is not None:
        return animation_data.action
    return None


def _active_motion_source(context):
    profile = state.get_active_profile(context.scene)
    if profile is None:
        return None, None, "No Active Retarget Profile."

    source = profile.source_armature
    if source is None or source.type != "ARMATURE":
        return None, None, "Source Armature is not assigned or invalid."

    return profile, source, None


def _activate_source_pose_mode(context, source_armature: Object) -> None:
    active_object = context.view_layer.objects.active
    if active_object is not None and active_object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    source_armature.select_set(True)
    context.view_layer.objects.active = source_armature
    bpy.ops.object.mode_set(mode="POSE")


class BRM_OT_motion_edit_enter(Operator):
    bl_idname = "bone_remap.motion_edit_enter"
    bl_label = "Enter Motion Edit Mode"
    bl_description = "Edit the source Motion Action with Blender-native keying under the saved Work Pose context"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_motion_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        action = ensure_motion_action(profile, source)
        profile.motion_editing = True
        profile.live_preview_enabled = True
        _activate_source_pose_mode(context, source)
        live_preview.solve_if_enabled(context, reason="motion_edit_enter")
        self.report({"INFO"}, f"Motion Edit Mode uses {action.name}.")
        return {"FINISHED"}


class BRM_OT_motion_edit_exit(Operator):
    bl_idname = "bone_remap.motion_edit_exit"
    bl_label = "Exit Motion Edit Mode"
    bl_description = "Leave Motion Edit Mode without changing the active Motion Action"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        profile.motion_editing = False
        self.report({"INFO"}, "Exited Motion Edit Mode.")
        return {"FINISHED"}


class BRM_OT_motion_action_duplicate(Operator):
    bl_idname = "bone_remap.motion_action_duplicate"
    bl_label = "Duplicate Motion Action"
    bl_description = "Duplicate the active source Motion Action and edit the duplicate"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_motion_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        action = active_motion_action(profile, source)
        if action is None:
            action = ensure_motion_action(profile, source)

        duplicate = action.copy()
        duplicate.name = f"{action.name}_Copy"
        source.animation_data_create().action = duplicate
        profile.active_motion_action = duplicate
        self.report({"INFO"}, f"Duplicated Motion Action: {duplicate.name}.")
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_motion_edit_enter,
    BRM_OT_motion_edit_exit,
    BRM_OT_motion_action_duplicate,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
