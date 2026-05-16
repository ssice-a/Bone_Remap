"""Blender-native Work Pose Layer management."""

from __future__ import annotations

import bpy
from bpy.types import Action, NlaTrack, Object
from mathutils import Matrix

from . import action_slots, pose_matrices, work_pose


ACTION_PREFIX = "BRM_WorkPose"
TRACK_NAME = "BRM Work Pose Layer"
STRIP_NAME = "BRM Work Pose"
ACTION_FRAME_START = 1
ACTION_FRAME_END = 2


def ensure_work_pose_layer(context, profile, source_armature: Object) -> int:
    """Create or update the source-visible Work Pose Layer from saved matrices."""

    if not work_pose.has_saved_work_pose(profile):
        return 0

    animation_data = source_armature.animation_data_create()
    old_action = profile.work_pose_action
    action = _create_work_pose_action(profile, source_armature)
    _rewrite_work_pose_action(context, profile, source_armature, action)
    _ensure_nla_strip(animation_data, action, context.scene.frame_start, context.scene.frame_end)
    _remove_generated_action(old_action, keep=action)
    context.view_layer.update()
    return len(profile.work_pose_matrices)


def remove_work_pose_layer(profile, source_armature: Object) -> bool:
    """Remove the generated Work Pose Layer strip from the source armature."""

    animation_data = source_armature.animation_data
    removed = False
    if animation_data is not None:
        for track in list(animation_data.nla_tracks):
            if track.name != TRACK_NAME:
                continue
            for strip in list(track.strips):
                if strip.name == STRIP_NAME:
                    track.strips.remove(strip)
                    removed = True
            if not track.strips:
                animation_data.nla_tracks.remove(track)

    action = profile.work_pose_action
    profile.work_pose_action = None
    _remove_generated_action(action, keep=None)
    return removed


def _create_work_pose_action(profile, source_armature: Object) -> Action:
    action = bpy.data.actions.new(name=f"{ACTION_PREFIX}_{source_armature.name}_{profile.name}")
    action.use_fake_user = True
    profile.work_pose_action = action
    return action


def _rewrite_work_pose_action(context, profile, source_armature: Object, action: Action) -> None:
    _clear_action(action)
    pose_matrix_map = work_pose.profile_work_pose_matrix_map(profile)
    basis_matrix_map = pose_matrices.basis_matrix_map_from_pose_matrices(source_armature, pose_matrix_map)
    animation_data = source_armature.animation_data_create()
    original_action = animation_data.action
    original_action_slot = getattr(animation_data, "action_slot", None)
    original_pose = _capture_pose_matrices(source_armature)
    original_nla_mutes = [(track, track.mute) for track in animation_data.nla_tracks]

    try:
        for track in animation_data.nla_tracks:
            track.mute = True
        animation_data.action = action
        work_pose.reset_source_pose_to_rest(context, source_armature)
        _apply_basis_matrices(source_armature, basis_matrix_map)
        context.view_layer.update()
        for frame in (ACTION_FRAME_START, ACTION_FRAME_END):
            _key_pose_transforms(source_armature, basis_matrix_map.keys(), frame)
    finally:
        animation_data.action = original_action
        if original_action is None:
            action_slots.clear_action_slot(animation_data)
        else:
            action_slots.sync_action_slot(animation_data, original_action_slot)
        for track, mute in original_nla_mutes:
            track.mute = mute
        _restore_pose_matrices(context, source_armature, original_pose)


def _remove_generated_action(action: Action | None, keep: Action | None) -> None:
    if action is None or action == keep:
        return
    if not action.name.startswith(ACTION_PREFIX):
        return
    if action.name in bpy.data.actions:
        bpy.data.actions.remove(action)


def _ensure_nla_strip(animation_data, action: Action, frame_start: int, frame_end: int) -> None:
    _set_use_nla(animation_data, True)
    track = _find_or_create_track(animation_data)
    strip = _find_strip(track)
    if strip is None:
        strip = track.strips.new(STRIP_NAME, frame_start, action)

    strip.action = action
    action_slots.sync_action_slot(strip)
    strip.frame_start = frame_start
    strip.frame_end = max(frame_end, frame_start + 1)
    strip.action_frame_start = ACTION_FRAME_START
    strip.action_frame_end = ACTION_FRAME_END
    strip.influence = 1.0
    strip.mute = False
    _set_strip_enum(strip, "blend_type", "COMBINE")
    _set_strip_enum(strip, "extrapolation", "HOLD_FORWARD")


def _find_or_create_track(animation_data) -> NlaTrack:
    for track in animation_data.nla_tracks:
        if track.name == TRACK_NAME:
            track.mute = False
            return track
    track = animation_data.nla_tracks.new()
    track.name = TRACK_NAME
    track.mute = False
    return track


def _find_strip(track: NlaTrack):
    for strip in track.strips:
        if strip.name == STRIP_NAME:
            return strip
    return None


def _set_strip_enum(strip, attr: str, value: str) -> None:
    try:
        setattr(strip, attr, value)
    except TypeError:
        pass


def _set_use_nla(animation_data, enabled: bool) -> None:
    if hasattr(animation_data, "use_nla"):
        animation_data.use_nla = bool(enabled)


def _clear_action(action: Action) -> None:
    fcurves = getattr(action, "fcurves", None)
    if fcurves is None:
        return
    while fcurves:
        fcurves.remove(fcurves[0])


def _apply_basis_matrices(source_armature: Object, basis_matrix_map: dict[str, Matrix]) -> None:
    for data_bone in pose_matrices.iter_data_bones_depth_first(source_armature):
        pose_bone = source_armature.pose.bones.get(data_bone.name)
        basis_matrix = basis_matrix_map.get(data_bone.name)
        if pose_bone is not None and basis_matrix is not None:
            pose_bone.matrix_basis = basis_matrix


def _key_pose_transforms(source_armature: Object, bone_names, frame: int) -> None:
    for bone_name in bone_names:
        pose_bone = source_armature.pose.bones.get(bone_name)
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


def _capture_pose_matrices(source_armature: Object) -> dict[str, tuple[float, ...]]:
    return {
        pose_bone.name: work_pose.flatten_matrix(pose_bone.matrix)
        for pose_bone in source_armature.pose.bones
    }


def _restore_pose_matrices(context, source_armature: Object, matrices: dict[str, tuple[float, ...]]) -> None:
    matrix_by_bone_name = {
        bone_name: work_pose.matrix_from_flat(matrix)
        for bone_name, matrix in matrices.items()
    }
    pose_matrices.apply_pose_matrix_map(context, source_armature, matrix_by_bone_name)
