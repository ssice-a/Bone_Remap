"""Automatic Live Preview around the one-frame solver."""

from __future__ import annotations

from time import perf_counter

import bpy
from bpy.app.handlers import persistent
from bpy.types import Object, Operator

from . import pose_matrices, runtime_plan, solver, state
from .registration import register_classes, unregister_classes


_IS_SOLVING = False
_MATRIX_EPSILON = 1e-6
_LAST_SOURCE_SIGNATURES: dict[tuple[int, int, int], dict[str, object | None]] = {}


def is_enabled(profile) -> bool:
    return bool(profile is not None and profile.live_preview_enabled)


def solve_if_enabled(
    context,
    reason: str = "manual",
    depsgraph=None,
    update_view_layer: bool = True,
    source_bone_names: tuple[str, ...] | None = None,
    pre_solve_timings: dict[str, float] | None = None,
    cache_source_signature: bool = True,
):
    profile = state.get_active_profile(context.scene)
    if not is_enabled(profile):
        return None
    return solve_now(
        context,
        reason=reason,
        depsgraph=depsgraph,
        update_view_layer=update_view_layer,
        source_bone_names=source_bone_names,
        pre_solve_timings=pre_solve_timings,
        cache_source_signature=cache_source_signature,
    )


def solve_now(
    context,
    reason: str = "manual",
    depsgraph=None,
    update_view_layer: bool = True,
    source_bone_names: tuple[str, ...] | None = None,
    pre_solve_timings: dict[str, float] | None = None,
    cache_source_signature: bool = True,
):
    global _IS_SOLVING

    if _IS_SOLVING:
        return None

    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return None

    _IS_SOLVING = True
    try:
        result = solver.solve_active_profile_one_frame(
            context,
            depsgraph=depsgraph,
            update_view_layer=update_view_layer,
            source_bone_names=source_bone_names,
        )
        if pre_solve_timings:
            result.timings.update(pre_solve_timings)
        if cache_source_signature:
            cache_started_at = perf_counter()
            _cache_source_signature(active_context, depsgraph or context.evaluated_depsgraph_get())
            result.timings["source_cache_ms"] = (perf_counter() - cache_started_at) * 1000.0
        else:
            result.timings["source_cache_ms"] = 0.0
        result.timings["total_with_gate_ms"] = (
            result.timings.get("total_ms", 0.0)
            + result.timings.get("source_compare_ms", 0.0)
            + result.timings.get("source_cache_ms", 0.0)
        )
        _record_live_result(active_context.profile, result, reason, replace_written_targets=source_bone_names is None)
        return result
    finally:
        _IS_SOLVING = False


def _record_live_result(profile, result: solver.SolveResult, reason: str, replace_written_targets: bool = True) -> None:
    if replace_written_targets:
        profile.live_preview_last_written_targets.clear()

    existing_names = {item.target_bone_name for item in profile.live_preview_last_written_targets if item.target_bone_name}
    for target_bone_name in result.written_target_names:
        if target_bone_name in existing_names:
            continue
        item = profile.live_preview_last_written_targets.add()
        item.target_bone_name = target_bone_name
        existing_names.add(target_bone_name)

    errors = [message.text for message in result.messages if message.severity == "ERROR"]
    if errors:
        profile.live_preview_last_result = errors[0]
    else:
        profile.live_preview_last_result = _format_live_result(reason, result)
    if getattr(profile, "live_preview_perf_logging", False):
        print(_format_console_perf_result(reason, result), flush=True)


def _format_live_result(reason: str, result: solver.SolveResult) -> str:
    timings = result.timings
    total_ms = timings.get("total_with_gate_ms", timings.get("total_ms", 0.0))
    scope = "partial" if timings.get("partial", 0.0) else "full"
    return (
        f"{reason}: {scope} {result.written_targets} targets "
        f"{total_ms:.1f}ms "
        f"gate={timings.get('source_compare_ms', 0.0):.1f} "
        f"cache={timings.get('source_cache_ms', 0.0):.1f} "
        f"plan={timings.get('build_plan_ms', 0.0):.1f} "
        f"eval={timings.get('source_eval_ms', 0.0):.1f} "
        f"scope={timings.get('scope_ms', 0.0):.1f} "
        f"calc={timings.get('compute_ms', 0.0):.1f} "
        f"order={timings.get('order_filter_ms', 0.0):.1f} "
        f"apply={timings.get('apply_ms', 0.0):.1f} "
        f"rows={int(timings.get('solved_rows', 0.0))}/{int(timings.get('full_rows', 0.0))}"
    )


def _format_console_perf_result(reason: str, result: solver.SolveResult) -> str:
    timings = result.timings
    total_ms = timings.get("total_with_gate_ms", timings.get("total_ms", 0.0))
    scope = "partial" if timings.get("partial", 0.0) else "full"
    fields = {
        "reason": reason,
        "scope": scope,
        "written": result.written_targets,
        "total_ms": f"{total_ms:.3f}",
        "gate_ms": f"{timings.get('source_compare_ms', 0.0):.3f}",
        "cache_ms": f"{timings.get('source_cache_ms', 0.0):.3f}",
        "plan_ms": f"{timings.get('build_plan_ms', 0.0):.3f}",
        "eval_ms": f"{timings.get('source_eval_ms', 0.0):.3f}",
        "scope_ms": f"{timings.get('scope_ms', 0.0):.3f}",
        "calc_ms": f"{timings.get('compute_ms', 0.0):.3f}",
        "order_ms": f"{timings.get('order_filter_ms', 0.0):.3f}",
        "apply_ms": f"{timings.get('apply_ms', 0.0):.3f}",
        "apply_select_ms": f"{timings.get('apply_select_ms', 0.0):.3f}",
        "apply_parent_ms": f"{timings.get('apply_parent_capture_ms', 0.0):.3f}",
        "apply_basis_ms": f"{timings.get('apply_basis_ms', 0.0):.3f}",
        "apply_write_ms": f"{timings.get('apply_write_ms', 0.0):.3f}",
        "view_update_ms": f"{timings.get('view_update_ms', 0.0):.3f}",
        "rows": f"{int(timings.get('solved_rows', 0.0))}/{int(timings.get('full_rows', 0.0))}",
        "targets": f"{int(timings.get('valid_target_writes', 0.0))}/{int(timings.get('target_writes', 0.0))}",
        "scoped_sources": int(timings.get("scoped_sources", 0.0)),
        "skipped_rows": result.skipped_rows,
        "skipped_links": result.skipped_links,
    }
    payload = " ".join(f"{key}={value}" for key, value in fields.items())
    return f"[BRM-PERF] {payload}"


def clear_live_preview(context, profile, target_armature: Object) -> tuple[int, list[state.ValidationMessage]]:
    target_bone_names = _last_live_written_target_names(profile)
    if not target_bone_names:
        target_bone_names = runtime_plan.mapped_target_names(profile)

    reset_count, messages = reset_target_channels_to_bind(context, target_armature, target_bone_names)
    profile.live_preview_last_written_targets.clear()
    profile.live_preview_last_result = f"clear: reset {reset_count} target channels"
    return reset_count, messages


def cleanup_removed_target_links(context, profile, target_armature: Object, target_bone_names: list[str]) -> int:
    removed_names = [
        name for name in runtime_plan.unique_names(target_bone_names)
        if not runtime_plan.target_is_mapped(profile, name)
    ]
    reset_count, _messages = reset_target_channels_to_bind(context, target_armature, removed_names)
    _remove_last_live_written_targets(profile, removed_names)
    if reset_count:
        profile.live_preview_last_result = f"removed-link cleanup: reset {reset_count} target channels"
    return reset_count


def reset_target_channels_to_bind(
    context,
    target_armature: Object,
    target_bone_names: list[str],
) -> tuple[int, list[state.ValidationMessage]]:
    messages: list[state.ValidationMessage] = []
    if target_armature is None or target_armature.type != "ARMATURE":
        return 0, [state.ValidationMessage("ERROR", "Target Armature is not assigned or invalid.")]
    if target_armature.mode == "EDIT":
        return 0, [state.ValidationMessage("ERROR", "Leave target armature edit mode before clearing live preview.")]

    profile = state.get_active_profile(context.scene)
    target_writes = {}
    target_bind_matrices = runtime_plan.target_bind_matrix_by_bone(profile)
    for target_bone_name in runtime_plan.unique_names(target_bone_names):
        bind_matrix = runtime_plan.target_bind_matrix_for_bone(
            target_armature,
            target_bone_name,
            profile,
            target_bind_matrices,
        )
        if bind_matrix is None:
            messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {target_bone_name}"))
            continue
        target_writes[target_bone_name] = bind_matrix

    valid_target_writes = {}
    for target_bone_name in runtime_plan.target_write_order(target_armature, target_writes):
        if target_armature.pose.bones.get(target_bone_name) is None:
            messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {target_bone_name}"))
            continue
        valid_target_writes[target_bone_name] = target_writes[target_bone_name]

    written = pose_matrices.apply_pose_matrix_map(context, target_armature, valid_target_writes)

    if not messages:
        messages.append(state.ValidationMessage("INFO", f"Reset {written} target channels to bind/rest."))
    return written, messages


def _last_live_written_target_names(profile) -> list[str]:
    return [item.target_bone_name for item in profile.live_preview_last_written_targets if item.target_bone_name]


def _remove_last_live_written_targets(profile, target_bone_names: list[str]) -> None:
    removed_names = set(target_bone_names)
    if not removed_names:
        return

    for index in range(len(profile.live_preview_last_written_targets) - 1, -1, -1):
        if profile.live_preview_last_written_targets[index].target_bone_name in removed_names:
            profile.live_preview_last_written_targets.remove(index)


def _current_context_for_scene(scene):
    context = bpy.context
    if context is None or context.scene != scene:
        return None
    return context


def _depsgraph_update_relevant(scene, depsgraph) -> bool:
    profile = state.get_active_profile(scene)
    if not is_enabled(profile):
        return False

    source = profile.source_armature
    if source is None:
        return False

    source_data = source.data
    for update in depsgraph.updates:
        updated_id = update.id
        if _same_id(updated_id, source) or _same_id(updated_id, source_data):
            return True

    return False


def _same_id(candidate, expected) -> bool:
    if candidate is None or expected is None:
        return False
    return candidate == expected or getattr(candidate, "original", None) == expected


@persistent
def _frame_change_post(scene, _depsgraph=None):
    context = _current_context_for_scene(scene)
    if context is None:
        return
    solve_if_enabled(context, reason="frame_change", update_view_layer=False)


@persistent
def _depsgraph_update_post(scene, depsgraph):
    if not _depsgraph_update_relevant(scene, depsgraph):
        return

    context = _current_context_for_scene(scene)
    if context is None:
        return
    active_context = state.get_active_profile_context(scene)
    if active_context is None:
        return
    compare_started_at = perf_counter()
    changed_source_bone_names = _source_bone_names_changed(active_context, depsgraph)
    source_compare_ms = (perf_counter() - compare_started_at) * 1000.0
    if not changed_source_bone_names:
        return
    solve_if_enabled(
        context,
        reason="depsgraph_update",
        depsgraph=depsgraph,
        update_view_layer=False,
        source_bone_names=changed_source_bone_names,
        pre_solve_timings={"source_compare_ms": source_compare_ms},
        cache_source_signature=False,
    )


def _append_once(handler_list, handler) -> None:
    if handler not in handler_list:
        handler_list.append(handler)


def _remove_if_present(handler_list, handler) -> None:
    while handler in handler_list:
        handler_list.remove(handler)


def _source_signature_key(active_context) -> tuple[int, int, int]:
    return (
        active_context.profile.as_pointer(),
        active_context.source_armature.as_pointer(),
        active_context.target_armature.as_pointer(),
    )


def _source_pose_signature(active_context, depsgraph) -> dict[str, object | None]:
    source_armature = active_context.source_armature
    evaluated_source = source_armature.evaluated_get(depsgraph)
    bone_names = sorted(
        {
            row.source_bone_name
            for row in active_context.profile.mapping_rows
            if row.source_bone_name
        }
    )
    signature: dict[str, object | None] = {}
    for bone_name in bone_names:
        pose_bone = evaluated_source.pose.bones.get(bone_name)
        if pose_bone is None:
            signature[bone_name] = None
            continue
        signature[bone_name] = pose_bone.matrix.copy()
    return signature


def _cache_source_signature(active_context, depsgraph) -> None:
    _LAST_SOURCE_SIGNATURES[_source_signature_key(active_context)] = _source_pose_signature(active_context, depsgraph)


def _source_bone_names_changed(active_context, depsgraph) -> tuple[str, ...]:
    signature_key = _source_signature_key(active_context)
    current_signature = _source_pose_signature(active_context, depsgraph)
    previous_signature = _LAST_SOURCE_SIGNATURES.get(signature_key)
    if previous_signature is None:
        _LAST_SOURCE_SIGNATURES[signature_key] = current_signature
        return tuple(sorted(current_signature.keys()))

    changed_names = tuple(
        bone_name
        for bone_name in sorted(current_signature.keys())
        if _signature_matrix_changed(
            current_signature.get(bone_name),
            previous_signature.get(bone_name),
        )
    )
    if changed_names:
        _LAST_SOURCE_SIGNATURES[signature_key] = current_signature
    return changed_names


def _signature_matrix_changed(current, previous) -> bool:
    if current is None or previous is None:
        return current is not previous

    for row_index in range(4):
        current_row = current[row_index]
        previous_row = previous[row_index]
        for column_index in range(4):
            if abs(current_row[column_index] - previous_row[column_index]) > _MATRIX_EPSILON:
                return True
    return False


def _enable_live_preview(context, profile):
    profile.live_preview_enabled = True
    result = solve_now(context, reason="enabled")
    if _initial_solve_failed(result):
        profile.live_preview_enabled = False
    return result


def _disable_live_preview(profile) -> None:
    profile.live_preview_enabled = False
    profile.live_preview_last_result = "disabled; target pose left unchanged"


def _initial_solve_failed(result) -> bool:
    if result is None:
        return True
    return result.written_targets <= 0 or any(message.severity == "ERROR" for message in result.messages)


def _report_initial_solve_failure(operator, result) -> None:
    if result is None:
        operator.report({"ERROR"}, "Solve did not run.")
        return

    for message in result.messages:
        if message.severity == "ERROR":
            operator.report({"ERROR"}, message.text)
            return

    operator.report({"WARNING"}, "Solve wrote 0 target channels. Add Target Links to the Mapping Table first.")


class BRM_OT_live_preview_enable(Operator):
    bl_idname = "bone_remap.live_preview_enable"
    bl_label = "Enable Live Preview"
    bl_description = "Enable automatic Live Preview for the Active Retarget Profile"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        result = _enable_live_preview(context, profile)
        if _initial_solve_failed(result):
            _report_initial_solve_failure(self, result)
            return {"CANCELLED"}
        if result is not None and result.written_targets > 0:
            self.report({"INFO"}, f"Live Preview enabled; wrote {result.written_targets} target channels.")
        else:
            self.report({"INFO"}, "Live Preview enabled.")
        return {"FINISHED"}


class BRM_OT_live_preview_disable(Operator):
    bl_idname = "bone_remap.live_preview_disable"
    bl_label = "Disable Live Preview"
    bl_description = "Disable automatic Live Preview without clearing the Target Armature pose"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        _disable_live_preview(profile)
        self.report({"INFO"}, "Live Preview disabled; Target Armature pose left unchanged.")
        return {"FINISHED"}


class BRM_OT_live_preview_toggle(Operator):
    bl_idname = "bone_remap.live_preview_toggle"
    bl_label = "Solve"
    bl_description = "Toggle live retarget solving for the Active Retarget Profile"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        if profile.live_preview_enabled:
            _disable_live_preview(profile)
            self.report({"INFO"}, "Solve disabled; Target Armature pose left unchanged.")
            return {"FINISHED"}

        result = _enable_live_preview(context, profile)
        if _initial_solve_failed(result):
            _report_initial_solve_failure(self, result)
            return {"CANCELLED"}
        if result is not None and result.written_targets > 0:
            self.report({"INFO"}, f"Solve enabled; wrote {result.written_targets} target channels.")
        else:
            self.report({"INFO"}, "Solve enabled.")
        return {"FINISHED"}


class BRM_OT_live_preview_clear(Operator):
    bl_idname = "bone_remap.live_preview_clear"
    bl_label = "Clear Live Preview"
    bl_description = "Reset last live-written target channels to bind/rest without changing retarget setup"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_context = state.get_active_profile_context(context.scene)
        if active_context is None:
            self.report({"ERROR"}, "Active Retarget Profile needs valid Source and Target Armatures.")
            return {"CANCELLED"}

        reset_count, messages = clear_live_preview(
            context,
            active_context.profile,
            active_context.target_armature,
        )
        has_error = False
        for message in messages:
            report_type = {"ERROR"} if message.severity == "ERROR" else {"WARNING"} if message.severity == "WARNING" else {"INFO"}
            has_error = has_error or message.severity == "ERROR"
            self.report(report_type, message.text)

        if reset_count > 0:
            self.report({"INFO"}, f"Cleared {reset_count} live target channels.")
        return {"CANCELLED"} if has_error else {"FINISHED"}


_CLASSES = (
    BRM_OT_live_preview_enable,
    BRM_OT_live_preview_disable,
    BRM_OT_live_preview_toggle,
    BRM_OT_live_preview_clear,
)


def register():
    register_classes(_CLASSES)

    _append_once(bpy.app.handlers.frame_change_post, _frame_change_post)
    _append_once(bpy.app.handlers.depsgraph_update_post, _depsgraph_update_post)


def unregister():
    _remove_if_present(bpy.app.handlers.depsgraph_update_post, _depsgraph_update_post)
    _remove_if_present(bpy.app.handlers.frame_change_post, _frame_change_post)

    unregister_classes(_CLASSES)
