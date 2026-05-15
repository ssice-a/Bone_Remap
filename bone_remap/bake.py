"""Bake current live retargeting result to a target action."""

from __future__ import annotations

import bpy
from bpy.types import Operator

from . import live_preview, motion_edit, runtime_plan, state


def bake_active_profile(context):
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    target = active_context.target_armature
    target_bone_names = runtime_plan.mapped_target_names(profile)
    if not target_bone_names:
        return 0, "Mapping Table has no mapped target channels."

    frame_range = _bake_frame_range(profile, active_context.source_armature)
    if frame_range is None:
        return 0, "Bake needs an active Motion Action range or an explicit Bake Range Override."

    frame_start, frame_end = frame_range
    if frame_end < frame_start:
        return 0, "Bake frame range is invalid."

    action = _target_bake_action(profile, target)
    target.animation_data_create().action = action
    if profile.bake_overwrite_existing:
        _clear_bake_scope(action, target_bone_names, frame_start, frame_end)

    scene = context.scene
    original_frame = scene.frame_current
    written_keys = 0
    try:
        for frame in range(frame_start, frame_end + 1):
            scene.frame_set(frame)
            live_preview.solve_now(context, reason="bake")
            written_keys += _insert_target_keys(target, target_bone_names, frame)
    finally:
        scene.frame_set(original_frame)

    profile.bake_last_result = f"Baked {len(target_bone_names)} target channels over {frame_start}-{frame_end}"
    return written_keys, profile.bake_last_result


def _bake_frame_range(profile, source_armature):
    if profile.bake_use_range_override:
        return profile.bake_frame_start, profile.bake_frame_end

    action = motion_edit.active_motion_action(profile, source_armature)
    if action is None:
        return None

    start, end = action.frame_range
    start = int(start)
    end = int(end)
    if end < start:
        return None
    return start, end


def _target_bake_action(profile, target_armature):
    animation_data = target_armature.animation_data_create()
    if profile.bake_overwrite_existing and animation_data.action is not None:
        return animation_data.action

    action = bpy.data.actions.new(name=f"{target_armature.name}_BakedRetarget")
    action.use_fake_user = True
    return action


def _clear_bake_scope(action, target_bone_names: list[str], frame_start: int, frame_end: int) -> None:
    scoped_paths = set()
    for bone_name in target_bone_names:
        prefix = f'pose.bones["{bone_name}"].'
        scoped_paths.add(prefix + "location")
        scoped_paths.add(prefix + "rotation_euler")
        scoped_paths.add(prefix + "rotation_quaternion")
        scoped_paths.add(prefix + "rotation_axis_angle")
        scoped_paths.add(prefix + "scale")

    for fcurve in list(action.fcurves):
        if fcurve.data_path not in scoped_paths:
            continue
        for keyframe in list(fcurve.keyframe_points):
            frame = keyframe.co.x
            if frame_start <= frame <= frame_end:
                fcurve.keyframe_points.remove(keyframe, fast=True)
        if len(fcurve.keyframe_points) == 0:
            action.fcurves.remove(fcurve)
        else:
            fcurve.update()


def _insert_target_keys(target_armature, target_bone_names: list[str], frame: int) -> int:
    inserted = 0
    for bone_name in target_bone_names:
        pose_bone = target_armature.pose.bones.get(bone_name)
        if pose_bone is None:
            continue

        pose_bone.keyframe_insert(data_path="location", frame=frame)
        if pose_bone.rotation_mode == "QUATERNION":
            pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        elif pose_bone.rotation_mode == "AXIS_ANGLE":
            pose_bone.keyframe_insert(data_path="rotation_axis_angle", frame=frame)
        else:
            pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)
        pose_bone.keyframe_insert(data_path="scale", frame=frame)
        inserted += 1
    return inserted


class BRM_OT_bake_live_result(Operator):
    bl_idname = "bone_remap.bake_live_result"
    bl_label = "Bake Live Result"
    bl_description = "Bake the current visible live retargeting result to a target action"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        written_keys, message = bake_active_profile(context)
        if written_keys == 0:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_bake_live_result,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
