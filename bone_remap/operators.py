"""Operators for the Bone Remap workbench shell."""

from __future__ import annotations

import bpy
from bpy.types import Operator

from . import state
from .registration import register_classes, unregister_classes


def _active_armature(context):
    selected_armatures = [obj for obj in context.selected_objects if obj.type == "ARMATURE"]
    if len(selected_armatures) == 1:
        return selected_armatures[0]

    obj = context.view_layer.objects.active or context.object
    if obj is not None and obj.type == "ARMATURE":
        return obj
    return None


class BRM_OT_profile_add(Operator):
    bl_idname = "bone_remap.profile_add"
    bl_label = "Add Retarget Profile"
    bl_description = "Create a Retarget Profile and make it active"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.create_profile(context.scene)
        self.report({"INFO"}, f"Created {profile.name}")
        return {"FINISHED"}


class BRM_OT_profile_remove(Operator):
    bl_idname = "bone_remap.profile_remove"
    bl_label = "Remove Retarget Profile"
    bl_description = "Remove the active Retarget Profile"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not state.remove_active_profile(context.scene):
            self.report({"WARNING"}, "No Active Retarget Profile to remove.")
            return {"CANCELLED"}

        self.report({"INFO"}, "Removed Active Retarget Profile.")
        return {"FINISHED"}


class BRM_OT_set_source_from_active(Operator):
    bl_idname = "bone_remap.set_source_from_active"
    bl_label = "Set Source From Selection"
    bl_description = "Assign the selected armature as the Source Armature; if multiple armatures are selected, use the active one"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        armature = _active_armature(context)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}
        if armature is None:
            self.report({"ERROR"}, "Active object is not an armature.")
            return {"CANCELLED"}

        previous_source = profile.source_armature
        if previous_source is not None and previous_source != armature:
            _remove_work_pose_layer(profile, previous_source)
        profile.source_armature = armature
        _invalidate_runtime_plan(profile)
        _solve_live_preview_if_enabled(context, reason="source_changed")
        self.report({"INFO"}, f"Source Armature set to {armature.name}")
        return {"FINISHED"}


class BRM_OT_set_target_from_active(Operator):
    bl_idname = "bone_remap.set_target_from_active"
    bl_label = "Set Target From Selection"
    bl_description = "Assign the selected armature as the Target Armature; if multiple armatures are selected, use the active one"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        armature = _active_armature(context)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}
        if armature is None:
            self.report({"ERROR"}, "Active object is not an armature.")
            return {"CANCELLED"}

        profile.target_armature = armature
        _invalidate_runtime_plan(profile)
        _solve_live_preview_if_enabled(context, reason="target_changed")
        self.report({"INFO"}, f"Target Armature set to {armature.name}")
        return {"FINISHED"}


def _solve_live_preview_if_enabled(context, reason: str) -> None:
    from . import live_preview

    live_preview.solve_if_enabled(context, reason=reason)


def _remove_work_pose_layer(profile, source_armature) -> None:
    from . import work_pose_layer

    work_pose_layer.remove_work_pose_layer(profile, source_armature)


def _invalidate_runtime_plan(profile) -> None:
    from . import runtime_plan

    runtime_plan.invalidate_runtime_plan(profile)


class BRM_OT_report_active_profile(Operator):
    bl_idname = "bone_remap.report_active_profile"
    bl_label = "Report Active Profile"
    bl_description = "Report whether the Active Retarget Profile is usable by core commands"
    bl_options = {"REGISTER"}

    def execute(self, context):
        active_context = state.get_active_profile_context(context.scene)
        if active_context is not None:
            self.report(
                {"INFO"},
                (
                    f"Active Profile {active_context.profile.name}: "
                    f"{active_context.source_armature.name} -> {active_context.target_armature.name}"
                ),
            )
            return {"FINISHED"}

        messages = state.validate_active_profile(context.scene)
        has_error = False
        for message in messages:
            report_type = {"ERROR"} if message.severity == "ERROR" else {"INFO"}
            has_error = has_error or message.severity == "ERROR"
            self.report(report_type, message.text)

        return {"CANCELLED"} if has_error else {"FINISHED"}


_CLASSES = (
    BRM_OT_profile_add,
    BRM_OT_profile_remove,
    BRM_OT_set_source_from_active,
    BRM_OT_set_target_from_active,
    BRM_OT_report_active_profile,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
