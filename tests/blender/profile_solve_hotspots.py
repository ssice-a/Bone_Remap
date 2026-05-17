"""Profile Bone Remap live solve hotspots inside Blender.

Run:
    blender.exe path/to/file.blend --background --python tests/blender/profile_solve_hotspots.py
"""

from __future__ import annotations

import importlib
import statistics
import time
from array import array

import bpy


SAMPLE_COUNT = 24


def main() -> None:
    modules = _import_bone_remap_modules()
    if modules is None:
        print("[BRM-HOTSPOT] Bone_Remap modules are not importable")
        return

    state, solver, live_preview, pose_matrices, motion_edit = modules
    scene = bpy.context.scene
    active_context = state.get_active_profile_context(scene)
    if active_context is None:
        print("[BRM-HOTSPOT] no active valid profile")
        return

    profile = active_context.profile
    source = active_context.source_armature
    target = active_context.target_armature
    action = motion_edit.active_motion_action(profile, source)
    frames = _sample_frames(scene, action)

    print("[BRM-HOTSPOT] file=", bpy.data.filepath)
    print(
        "[BRM-HOTSPOT] profile=",
        profile.name,
        "source=",
        source.name,
        "target=",
        target.name,
        "source_bones=",
        len(source.pose.bones),
        "target_bones=",
        len(target.pose.bones),
        "mapping_rows=",
        len(profile.mapping_rows),
        "mapped_targets=",
        sum(len(row.target_links) for row in profile.mapping_rows),
    )
    print(
        "[BRM-HOTSPOT] action=",
        action.name if action else None,
        "range=",
        tuple(round(value, 3) for value in action.frame_range) if action else None,
        "samples=",
        len(frames),
    )
    print("[BRM-HOTSPOT] modules=", solver.__file__, pose_matrices.__file__)

    original_frame = scene.frame_current
    original_live_enabled = bool(profile.live_preview_enabled)
    original_perf_logging = bool(getattr(profile, "live_preview_perf_logging", False))
    original_record_live_result = live_preview._record_live_result
    original_apply_pose_matrix_map = pose_matrices.apply_pose_matrix_map
    original_solver_solve_profile_one_frame = solver.solve_profile_one_frame
    original_is_animation_playing = live_preview._is_animation_playing
    original_bind_active_source_action = motion_edit.bind_active_source_action

    try:
        profile.live_preview_perf_logging = False
        profile.live_preview_enabled = False
        live_preview._is_animation_playing = lambda _context: True
        _clear_source_signature_cache(live_preview)
        _measure_frame_eval("native_live_off", scene, frames)

        motion_edit.bind_active_source_action(profile, source, bpy.context)
        _measure_frame_eval("source_action_bound_live_off", scene, frames)

        motion_edit.bind_active_source_action = lambda *_args, **_kwargs: action
        pose_matrices.apply_pose_matrix_map = _make_compute_only_apply(pose_matrices)
        live_preview._record_live_result = _record_live_result_noop
        _measure_handler_solve(
            "handler_compute_only_no_bind_no_status",
            scene,
            frames,
            profile,
            live_preview,
            solver,
            original_solver_solve_profile_one_frame,
        )

        motion_edit.bind_active_source_action = original_bind_active_source_action
        pose_matrices.apply_pose_matrix_map = _make_compute_only_apply(pose_matrices)
        live_preview._record_live_result = _record_live_result_noop
        _measure_handler_solve(
            "handler_compute_only_no_status",
            scene,
            frames,
            profile,
            live_preview,
            solver,
            original_solver_solve_profile_one_frame,
        )

        pose_matrices.apply_pose_matrix_map = original_apply_pose_matrix_map
        live_preview._record_live_result = original_record_live_result
        _measure_handler_solve(
            "handler_loop_write_status",
            scene,
            frames,
            profile,
            live_preview,
            solver,
            original_solver_solve_profile_one_frame,
        )

        live_preview._record_live_result = _record_live_result_noop
        pose_matrices.apply_pose_matrix_map = original_apply_pose_matrix_map
        _measure_handler_solve(
            "handler_loop_write_no_status",
            scene,
            frames,
            profile,
            live_preview,
            solver,
            original_solver_solve_profile_one_frame,
        )

        pose_matrices.apply_pose_matrix_map = _make_batch_apply(pose_matrices)
        _measure_handler_solve(
            "handler_batch_foreach_set_no_status",
            scene,
            frames,
            profile,
            live_preview,
            solver,
            original_solver_solve_profile_one_frame,
        )

        profile.live_preview_enabled = False
        live_preview._record_live_result = original_record_live_result
        pose_matrices.apply_pose_matrix_map = _make_compute_only_apply(pose_matrices)
        _measure_manual_solve("manual_compute_only", scene, frames, solver, profile, source, target)

        pose_matrices.apply_pose_matrix_map = original_apply_pose_matrix_map
        _measure_manual_solve("manual_loop_write", scene, frames, solver, profile, source, target)

        pose_matrices.apply_pose_matrix_map = _make_batch_apply(pose_matrices)
        _measure_manual_solve("manual_batch_foreach_set", scene, frames, solver, profile, source, target)
    finally:
        profile.live_preview_enabled = original_live_enabled
        profile.live_preview_perf_logging = original_perf_logging
        live_preview._record_live_result = original_record_live_result
        pose_matrices.apply_pose_matrix_map = original_apply_pose_matrix_map
        solver.solve_profile_one_frame = original_solver_solve_profile_one_frame
        live_preview._is_animation_playing = original_is_animation_playing
        motion_edit.bind_active_source_action = original_bind_active_source_action
        scene.frame_set(original_frame)
        bpy.context.view_layer.update()


def _import_bone_remap_modules():
    prefixes = ("Bone_Remap.bone_remap", "bone_remap")
    for prefix in prefixes:
        try:
            return (
                importlib.import_module(f"{prefix}.state"),
                importlib.import_module(f"{prefix}.solver"),
                importlib.import_module(f"{prefix}.live_preview"),
                importlib.import_module(f"{prefix}.pose_matrices"),
                importlib.import_module(f"{prefix}.motion_edit"),
            )
        except Exception:
            continue
    return None


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
    return list(range(start, end + 1, step))[:SAMPLE_COUNT] or [start]


def _measure_frame_eval(label: str, scene, frames) -> None:
    times = []
    for frame in frames:
        started_at = time.perf_counter()
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        times.append((time.perf_counter() - started_at) * 1000.0)
    _print_summary(label, times, [])


def _measure_manual_solve(label: str, scene, frames, solver, profile, source, target) -> None:
    times = []
    timing_rows = []
    for frame in frames:
        started_at = time.perf_counter()
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        result = solver.solve_profile_one_frame(
            bpy.context,
            profile,
            source,
            target,
            update_view_layer=False,
        )
        bpy.context.view_layer.update()
        times.append((time.perf_counter() - started_at) * 1000.0)
        timing_rows.append(result.timings)
    _print_summary(label, times, timing_rows)


def _measure_handler_solve(
    label: str,
    scene,
    frames,
    profile,
    live_preview,
    solver,
    original_solver_solve_profile_one_frame,
) -> None:
    times = []
    timing_rows = []

    def counted_solve_profile_one_frame(*args, **kwargs):
        result = original_solver_solve_profile_one_frame(*args, **kwargs)
        timing_rows.append(result.timings)
        return result

    solver.solve_profile_one_frame = counted_solve_profile_one_frame
    profile.live_preview_enabled = True
    _clear_source_signature_cache(live_preview)
    try:
        for frame in frames:
            started_at = time.perf_counter()
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            times.append((time.perf_counter() - started_at) * 1000.0)
    finally:
        profile.live_preview_enabled = False
        solver.solve_profile_one_frame = original_solver_solve_profile_one_frame
        _clear_source_signature_cache(live_preview)
    _print_summary(label, times, timing_rows)


def _make_compute_only_apply(pose_matrices):
    def apply_pose_matrix_map(
        context,
        armature,
        pose_matrix_map,
        update_view_layer=True,
        timings=None,
        ordered_bone_names=None,
    ):
        del context
        del update_view_layer
        select_started_at = time.perf_counter()
        data_bones = tuple(
            pose_matrices._iter_named_data_bones_in_order(armature, ordered_bone_names)
            if ordered_bone_names is not None
            else pose_matrices.iter_data_bones_depth_first(armature, pose_matrix_map.keys())
        )
        _record_timing(timings, "apply_select_ms", select_started_at)

        parent_started_at = time.perf_counter()
        fallback_parent_names = {
            data_bone.parent.name
            for data_bone in data_bones
            if data_bone.parent is not None and data_bone.parent.name not in pose_matrix_map
        }
        current_pose_matrix_map = pose_matrices.capture_pose_matrix_map(armature, fallback_parent_names)
        _record_timing(timings, "apply_parent_capture_ms", parent_started_at)

        basis_started_at = time.perf_counter()
        basis_matrix_map = pose_matrices.basis_matrix_map_from_pose_matrices(
            armature,
            pose_matrix_map,
            current_pose_matrix_map,
            data_bones=data_bones,
        )
        _record_timing(timings, "apply_basis_ms", basis_started_at)
        if timings is not None:
            timings["apply_write_ms"] = 0.0
            timings["apply_compute_only"] = 1.0
        return len(basis_matrix_map)

    return apply_pose_matrix_map


def _make_batch_apply(pose_matrices):
    index_cache = {}

    def apply_pose_matrix_map(
        context,
        armature,
        pose_matrix_map,
        update_view_layer=True,
        timings=None,
        ordered_bone_names=None,
    ):
        select_started_at = time.perf_counter()
        data_bones = tuple(
            pose_matrices._iter_named_data_bones_in_order(armature, ordered_bone_names)
            if ordered_bone_names is not None
            else pose_matrices.iter_data_bones_depth_first(armature, pose_matrix_map.keys())
        )
        _record_timing(timings, "apply_select_ms", select_started_at)

        parent_started_at = time.perf_counter()
        fallback_parent_names = {
            data_bone.parent.name
            for data_bone in data_bones
            if data_bone.parent is not None and data_bone.parent.name not in pose_matrix_map
        }
        current_pose_matrix_map = pose_matrices.capture_pose_matrix_map(armature, fallback_parent_names)
        _record_timing(timings, "apply_parent_capture_ms", parent_started_at)

        basis_started_at = time.perf_counter()
        basis_matrix_map = pose_matrices.basis_matrix_map_from_pose_matrices(
            armature,
            pose_matrix_map,
            current_pose_matrix_map,
            data_bones=data_bones,
        )
        _record_timing(timings, "apply_basis_ms", basis_started_at)

        write_started_at = time.perf_counter()
        pose_bones = armature.pose.bones
        cache_key = (armature.as_pointer(), len(pose_bones))
        name_to_index = index_cache.get(cache_key)
        if name_to_index is None:
            name_to_index = {pose_bone.name: index for index, pose_bone in enumerate(pose_bones)}
            index_cache[cache_key] = name_to_index

        flat = array("f", [0.0]) * (len(pose_bones) * 16)
        get_started_at = time.perf_counter()
        pose_bones.foreach_get("matrix_basis", flat)
        _record_timing(timings, "apply_foreach_get_ms", get_started_at)

        applied = 0
        for data_bone in data_bones:
            basis_matrix = basis_matrix_map.get(data_bone.name)
            index = name_to_index.get(data_bone.name)
            if basis_matrix is None or index is None:
                continue
            offset = index * 16
            for row_index in range(4):
                row = basis_matrix[row_index]
                flat[offset + row_index * 4 + 0] = row[0]
                flat[offset + row_index * 4 + 1] = row[1]
                flat[offset + row_index * 4 + 2] = row[2]
                flat[offset + row_index * 4 + 3] = row[3]
            applied += 1

        set_started_at = time.perf_counter()
        pose_bones.foreach_set("matrix_basis", flat)
        _record_timing(timings, "apply_foreach_set_ms", set_started_at)
        _record_timing(timings, "apply_write_ms", write_started_at)

        if applied and update_view_layer:
            update_started_at = time.perf_counter()
            context.view_layer.update()
            _record_timing(timings, "apply_view_update_ms", update_started_at)
        return applied

    return apply_pose_matrix_map


def _record_live_result_noop(*args, **kwargs) -> None:
    del args
    del kwargs


def _clear_source_signature_cache(live_preview) -> None:
    cache = getattr(live_preview, "_LAST_SOURCE_SIGNATURES", None)
    if cache is not None:
        cache.clear()


def _record_timing(timings: dict[str, float] | None, key: str, started_at: float) -> None:
    if timings is not None:
        timings[key] = (time.perf_counter() - started_at) * 1000.0


def _print_summary(label: str, times: list[float], timing_rows: list[dict[str, float]]) -> None:
    if not times:
        print("[BRM-HOTSPOT]", label, "no samples")
        return

    avg_ms = statistics.fmean(times)
    print(
        "[BRM-HOTSPOT]",
        label,
        "samples=",
        len(times),
        "avg_ms=",
        round(avg_ms, 3),
        "median_ms=",
        round(statistics.median(times), 3),
        "min_ms=",
        round(min(times), 3),
        "max_ms=",
        round(max(times), 3),
        "approx_fps=",
        round(1000.0 / avg_ms, 3) if avg_ms > 0 else 0.0,
    )
    if timing_rows:
        keys = (
            "total_ms",
            "source_compare_ms",
            "source_cache_ms",
            "build_plan_ms",
            "view_update_ms",
            "source_eval_ms",
            "scope_ms",
            "compute_ms",
            "order_filter_ms",
            "apply_ms",
            "apply_select_ms",
            "apply_parent_capture_ms",
            "apply_basis_ms",
            "apply_write_ms",
            "apply_foreach_get_ms",
            "apply_foreach_set_ms",
            "solved_rows",
            "valid_target_writes",
        )
        payload = []
        for key in keys:
            values = [row[key] for row in timing_rows if key in row]
            if values:
                payload.append(f"{key}={statistics.fmean(values):.3f}")
        print("[BRM-HOTSPOT]", label, "solve_calls=", len(timing_rows), "timings", " ".join(payload))


if __name__ == "__main__":
    main()
