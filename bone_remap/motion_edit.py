"""Source Action edit context helpers."""

from __future__ import annotations

import bpy
from bpy.types import Object, Operator

from . import action_slots, live_preview, state, work_pose, work_pose_layer
from .registration import register_classes, unregister_classes


def _source_action_items(source_armature: Object):
    return getattr(source_armature, "brm_source_actions", None)


def _active_source_action_index(source_armature: Object) -> int:
    return int(getattr(source_armature, "brm_active_source_action_index", -1))


def _find_source_action_index(source_armature: Object, action) -> int:
    source_actions = _source_action_items(source_armature)
    if source_actions is None or action is None:
        return -1
    for index, item in enumerate(source_actions):
        if item.action == action:
            return index
    return -1


def _selected_source_action(source_armature: Object):
    source_actions = _source_action_items(source_armature)
    index = _active_source_action_index(source_armature)
    if source_actions is None or not (0 <= index < len(source_actions)):
        return None
    return source_actions[index].action


def _select_source_action_index(source_armature: Object, index: int) -> None:
    source_armature.brm_active_source_action_index = index


def add_source_action(context, profile, source_armature: Object, action) -> int:
    source_actions = _source_action_items(source_armature)
    if source_actions is None or action is None:
        return -1

    index = _find_source_action_index(source_armature, action)
    if index < 0:
        item = source_actions.add()
        item.action = action
        index = len(source_actions) - 1

    try:
        action.use_fake_user = True
    except Exception:
        pass

    _select_source_action_index(source_armature, index)
    if profile.active_motion_action != action:
        profile.active_motion_action = action
    return index


def bind_active_source_action(profile, source_armature: Object, context=None, fast_if_unchanged: bool = False):
    action = _selected_source_action(source_armature) or profile.active_motion_action
    if action is None:
        return None

    animation_data = source_armature.animation_data
    if (
        fast_if_unchanged
        and animation_data is not None
        and animation_data.action == action
        and getattr(animation_data, "action_slot", None) is not None
    ):
        return action

    animation_data = source_armature.animation_data_create()
    changed = animation_data.action != action
    if changed:
        action_slots.clear_action_slot(animation_data)
        animation_data.action = action
    old_slot = getattr(animation_data, "action_slot", None)
    action_slots.sync_action_slot(animation_data)
    changed = changed or getattr(animation_data, "action_slot", None) != old_slot
    if context is not None and changed:
        context.view_layer.update()
    return action


def ensure_motion_action(profile, source_armature: Object):
    animation_data = source_armature.animation_data_create()
    action = _selected_source_action(source_armature) or profile.active_motion_action or animation_data.action
    if action is None:
        action = bpy.data.actions.new(name=f"{source_armature.name}_Motion")
    bind_active_source_action(profile, source_armature)
    if animation_data.action is None:
        animation_data.action = action
        action_slots.sync_action_slot(animation_data)
    profile.active_motion_action = action
    return action


def active_motion_action(profile, source_armature: Object):
    action = _selected_source_action(source_armature)
    if action is not None:
        return action
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


class BRM_OT_motion_action_add_current(Operator):
    bl_idname = "bone_remap.motion_action_add_current"
    bl_label = "Add Current Source Action"
    bl_description = "Add the Source Armature's current Action to Source Actions and make it active"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_motion_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        animation_data = source.animation_data
        action = animation_data.action if animation_data is not None else None
        if action is None:
            self.report({"ERROR"}, "Source Armature has no current Action.")
            return {"CANCELLED"}

        add_source_action(context, profile, source, action)
        self.report({"INFO"}, f"Active Source Action: {action.name}.")
        return {"FINISHED"}


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
        add_source_action(context, profile, source, action)
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
            self.report({"ERROR"}, "No Active Source Action to duplicate.")
            return {"CANCELLED"}

        duplicate = action.copy()
        duplicate.name = f"{action.name}_Copy"
        duplicate.use_fake_user = True
        add_source_action(context, profile, source, duplicate)
        self.report({"INFO"}, f"Duplicated Source Action: {duplicate.name}.")
        return {"FINISHED"}


class BRM_OT_motion_action_remove(Operator):
    bl_idname = "bone_remap.motion_action_remove"
    bl_label = "Remove Source Action"
    bl_description = "Remove the selected Source Action row without deleting the Blender Action datablock"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_motion_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        source_actions = _source_action_items(source)
        index = _active_source_action_index(source)
        if source_actions is None or not (0 <= index < len(source_actions)):
            self.report({"ERROR"}, "No selected Source Action row.")
            return {"CANCELLED"}

        removed_action = source_actions[index].action
        source_actions.remove(index)

        if len(source_actions) == 0:
            source.brm_active_source_action_index = -1
            profile.active_motion_action = None
            source.animation_data_create().action = None
            context.view_layer.update()
            live_preview.solve_if_enabled(context, reason="source_action_remove")
        else:
            _select_source_action_index(source, min(index, len(source_actions) - 1))

        removed_name = removed_action.name if removed_action is not None else "Missing Action"
        self.report({"INFO"}, f"Removed Source Action row: {removed_name}.")
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_motion_action_add_current,
    BRM_OT_motion_action_new,
    BRM_OT_motion_action_duplicate,
    BRM_OT_motion_action_remove,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
