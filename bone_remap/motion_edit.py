"""Source Action edit context helpers."""

from __future__ import annotations

import bpy
from bpy.types import Object, Operator

from . import live_preview, state, work_pose, work_pose_layer
from .registration import register_classes, unregister_classes


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


def ensure_source_action_edit_context(context, profile, source_armature: Object):
    if work_pose.has_saved_work_pose(profile):
        work_pose_layer.ensure_work_pose_layer(context, profile, source_armature)
    action = ensure_motion_action(profile, source_armature)
    live_preview.solve_if_enabled(context, reason="source_action_edit_context")
    return action


class BRM_OT_motion_action_new(Operator):
    bl_idname = "bone_remap.motion_action_new"
    bl_label = "New Source Action"
    bl_description = "Create an empty source Motion Action and make it active"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_motion_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        action = bpy.data.actions.new(name=f"{source.name}_Motion")
        action.use_fake_user = True
        profile.active_motion_action = action
        self.report({"INFO"}, f"Created Source Action: {action.name}.")
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
        duplicate.use_fake_user = True
        source.animation_data_create().action = duplicate
        profile.active_motion_action = duplicate
        self.report({"INFO"}, f"Duplicated Source Action: {duplicate.name}.")
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_motion_action_new,
    BRM_OT_motion_action_duplicate,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
