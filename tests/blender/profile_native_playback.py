"""Profile native Blender frame evaluation for the active source armature.

Run:
    blender.exe path/to/file.blend --background --python tests/blender/profile_native_playback.py
"""

from __future__ import annotations

import statistics
import time

import bpy


SAMPLE_COUNT = 24


def main() -> None:
    scene = bpy.context.scene
    source = _source_armature(scene)
    if source is None:
        print("[BRM-NATIVE] no source armature found")
        return

    action = _source_action(source)
    frames = _sample_frames(scene, action)
    source_meshes = _armature_meshes(source)
    all_meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    source_constraints = [constraint for pose_bone in source.pose.bones for constraint in pose_bone.constraints]

    print("[BRM-NATIVE] file=", bpy.data.filepath)
    print("[BRM-NATIVE] scene_objects=", len(scene.objects), "mesh_objects=", len(all_meshes))
    print(
        "[BRM-NATIVE] source=",
        source.name,
        "bones=",
        len(source.pose.bones),
        "constraints=",
        len(source_constraints),
    )
    print(
        "[BRM-NATIVE] source_action=",
        action.name if action else None,
        "range=",
        tuple(round(value, 3) for value in action.frame_range) if action else None,
        "fcurves=",
        _action_fcurve_count(action),
        "keyframes=",
        _action_keyframe_count(action),
    )
    print(
        "[BRM-NATIVE] source_meshes=",
        len(source_meshes),
        "source_vertices=",
        sum(len(obj.data.vertices) for obj in source_meshes),
        "source_vertex_groups=",
        sum(len(obj.vertex_groups) for obj in source_meshes),
    )

    original_frame = scene.frame_current
    original_live_states = _set_bone_remap_live(False)
    original_source_action = source.animation_data.action if source.animation_data else None
    original_constraint_mutes = [(constraint, constraint.mute) for constraint in source_constraints]
    original_source_mesh_visibility = _visibility_state(source_meshes)
    original_source_mesh_modifiers = _modifier_state(source_meshes)

    try:
        _measure("current_scene_live_off", scene, frames)

        _set_hidden(source_meshes, True)
        _measure("source_meshes_hidden", scene, frames)
        _restore_visibility(original_source_mesh_visibility)

        _set_armature_modifiers_enabled(source_meshes, source, False)
        _measure("source_armature_modifiers_off", scene, frames)
        _restore_modifiers(original_source_mesh_modifiers)

        for constraint in source_constraints:
            constraint.mute = True
        _measure("source_constraints_muted", scene, frames)
        _restore_constraint_mutes(original_constraint_mutes)

        if source.animation_data is not None:
            source.animation_data.action = None
            _measure("source_action_none", scene, frames)
            source.animation_data.action = original_source_action

        _measure("restored_current_scene", scene, frames)
    finally:
        _restore_live_states(original_live_states)
        _restore_visibility(original_source_mesh_visibility)
        _restore_modifiers(original_source_mesh_modifiers)
        _restore_constraint_mutes(original_constraint_mutes)
        if source.animation_data is not None:
            source.animation_data.action = original_source_action
        scene.frame_set(original_frame)
        bpy.context.view_layer.update()


def _source_armature(scene):
    profile_source = _profile_source_armature(scene)
    if profile_source is not None:
        return profile_source

    active = bpy.context.view_layer.objects.active
    if active is not None and active.type == "ARMATURE":
        return active

    armatures = [obj for obj in scene.objects if obj.type == "ARMATURE"]
    for armature in armatures:
        if _source_action(armature) is not None:
            return armature
    return armatures[0] if armatures else None


def _profile_source_armature(scene):
    try:
        import Bone_Remap.bone_remap.state as state
    except Exception:
        try:
            import bone_remap.state as state
        except Exception:
            return None

    try:
        active_context = state.get_active_profile_context(scene)
    except Exception:
        return None
    return active_context.source_armature


def _set_bone_remap_live(enabled: bool):
    states = []
    for scene in bpy.data.scenes:
        profiles = getattr(scene, "brm_retarget_profiles", None)
        if profiles is None:
            continue
        for profile in profiles:
            if hasattr(profile, "live_preview_enabled"):
                states.append((profile, bool(profile.live_preview_enabled)))
                profile.live_preview_enabled = enabled
    return states


def _restore_live_states(states) -> None:
    for profile, enabled in states:
        profile.live_preview_enabled = enabled


def _source_action(source):
    animation_data = source.animation_data
    return animation_data.action if animation_data is not None else None


def _sample_frames(scene, action):
    if action is None:
        start = int(scene.frame_start)
        end = int(scene.frame_end)
    else:
        start = int(action.frame_range[0])
        end = int(action.frame_range[1])
    if end < start:
        end = start

    span = max(1, end - start)
    step = max(1, span // max(1, SAMPLE_COUNT - 1))
    frames = list(range(start, end + 1, step))[:SAMPLE_COUNT]
    return frames or [start]


def _measure(label: str, scene, frames) -> None:
    times = []
    for frame in frames:
        started_at = time.perf_counter()
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        times.append((time.perf_counter() - started_at) * 1000.0)
    print(
        "[BRM-NATIVE]",
        label,
        "samples=",
        len(times),
        "avg_ms=",
        round(statistics.fmean(times), 3),
        "median_ms=",
        round(statistics.median(times), 3),
        "min_ms=",
        round(min(times), 3),
        "max_ms=",
        round(max(times), 3),
        "approx_fps=",
        round(1000.0 / statistics.fmean(times), 3) if statistics.fmean(times) > 0 else 0.0,
    )


def _armature_meshes(armature):
    meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and getattr(modifier, "object", None) == armature:
                meshes.append(obj)
                break
    return meshes


def _action_fcurves(action) -> list:
    if action is None:
        return []
    try:
        return list(action.fcurves)
    except Exception:
        pass

    fcurves = []
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            channelbag = getattr(strip, "channelbag", None)
            if channelbag is not None:
                fcurves.extend(getattr(channelbag, "fcurves", ()))
    return fcurves


def _action_fcurve_count(action) -> int:
    return len(_action_fcurves(action))


def _action_keyframe_count(action) -> int:
    return sum(len(fcurve.keyframe_points) for fcurve in _action_fcurves(action))


def _visibility_state(objects):
    return [(obj, obj.hide_viewport, obj.hide_get()) for obj in objects]


def _restore_visibility(states) -> None:
    for obj, hide_viewport, hide_get in states:
        obj.hide_viewport = hide_viewport
        obj.hide_set(hide_get)


def _set_hidden(objects, hidden: bool) -> None:
    for obj in objects:
        obj.hide_viewport = hidden
        obj.hide_set(hidden)
    bpy.context.view_layer.update()


def _modifier_state(objects):
    states = []
    for obj in objects:
        for modifier in obj.modifiers:
            states.append((modifier, modifier.show_viewport))
    return states


def _restore_modifiers(states) -> None:
    for modifier, show_viewport in states:
        modifier.show_viewport = show_viewport
    bpy.context.view_layer.update()


def _set_armature_modifiers_enabled(objects, armature, enabled: bool) -> None:
    for obj in objects:
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and getattr(modifier, "object", None) == armature:
                modifier.show_viewport = enabled
    bpy.context.view_layer.update()


def _restore_constraint_mutes(states) -> None:
    for constraint, mute in states:
        constraint.mute = mute
    bpy.context.view_layer.update()


if __name__ == "__main__":
    main()
