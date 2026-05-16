"""One-frame retarget solve from Work Pose and Mapping Table."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from time import perf_counter

import bpy
from bpy.types import Object, Operator
from mathutils import Matrix

from . import pose_matrices, runtime_plan, state
from .registration import register_classes, unregister_classes


@dataclass(frozen=True)
class SolveResult:
    written_targets: int
    written_target_names: tuple[str, ...]
    skipped_rows: int
    skipped_links: int
    messages: list[state.ValidationMessage]
    timings: dict[str, float]
    source_pose_signature: dict[str, Matrix] | None = None


def solve_active_profile_one_frame(
    context,
    depsgraph=None,
    update_view_layer: bool = True,
    source_bone_names: Iterable[str] | None = None,
) -> SolveResult:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return _error_result("Active Retarget Profile needs valid Source and Target Armatures.")

    return solve_profile_one_frame(
        context,
        active_context.profile,
        active_context.source_armature,
        active_context.target_armature,
        depsgraph=depsgraph,
        update_view_layer=update_view_layer,
        source_bone_names=source_bone_names,
    )


def solve_profile_one_frame(
    context,
    profile,
    source_armature: Object,
    target_armature: Object,
    depsgraph=None,
    update_view_layer: bool = True,
    source_bone_names: Iterable[str] | None = None,
) -> SolveResult:
    total_started_at = perf_counter()
    if source_armature.mode == "EDIT" or target_armature.mode == "EDIT":
        return _error_result("Leave armature edit mode before solving.", total_started_at)
    from . import motion_edit

    motion_edit.bind_active_source_action(profile, source_armature)

    plan_started_at = perf_counter()
    plan = runtime_plan.build_runtime_plan(profile, source_armature, target_armature)
    plan_ms = _elapsed_ms(plan_started_at)
    if not plan.rows and any(message.severity == "ERROR" for message in plan.messages):
        return SolveResult(
            written_targets=0,
            written_target_names=(),
            skipped_rows=plan.skipped_rows,
            skipped_links=plan.skipped_links,
            messages=plan.messages,
            timings=_timings(
                total_started_at,
                build_plan_ms=plan_ms,
            ),
        )

    view_update_ms = 0.0
    if update_view_layer:
        update_started_at = perf_counter()
        context.view_layer.update()
        view_update_ms += _elapsed_ms(update_started_at)
    source_eval_started_at = perf_counter()
    depsgraph = depsgraph or context.evaluated_depsgraph_get()
    evaluated_source = source_armature.evaluated_get(depsgraph)
    source_eval_ms = _elapsed_ms(source_eval_started_at)

    scope_started_at = perf_counter()
    source_bone_name_scope = None if source_bone_names is None else set(source_bone_names)
    scoped_source_count = 0 if source_bone_name_scope is None else len(source_bone_name_scope)
    rows_to_solve = _rows_for_source_scope(plan.rows, target_armature, source_bone_name_scope, plan.mapped_target_names)
    scope_ms = _elapsed_ms(scope_started_at)

    target_writes: dict[str, Matrix] = {}
    messages: list[state.ValidationMessage] = list(plan.messages)
    skipped_rows = 0
    skipped_links = 0

    compute_started_at = perf_counter()
    source_pose_signature = {} if source_bone_name_scope is None else None
    for row in rows_to_solve:
        source_pose_bone = evaluated_source.pose.bones.get(row.source_bone_name)
        if source_pose_bone is None:
            skipped_rows += 1
            messages.append(state.ValidationMessage("ERROR", f"Invalid source bone: {row.source_bone_name}"))
            continue

        source_matrix = source_pose_bone.matrix.copy()
        if source_pose_signature is not None:
            source_pose_signature[row.source_bone_name] = source_matrix
        source_delta = source_matrix @ row.source_work_pose_matrix.inverted_safe()
        for target_channel in row.target_channels:
            target_writes[target_channel.bone_name] = source_delta @ target_channel.bind_matrix
    compute_ms = _elapsed_ms(compute_started_at)

    order_started_at = perf_counter()
    target_write_order = (
        plan.mapped_target_write_order
        if source_bone_name_scope is None
        else runtime_plan.target_write_order(target_armature, target_writes)
    )
    written_target_names = [
        target_bone_name
        for target_bone_name in target_write_order
        if target_bone_name in target_writes
        if target_armature.pose.bones.get(target_bone_name) is not None
    ]
    skipped_links += len(target_writes) - len(written_target_names)
    for target_bone_name in target_writes:
        if target_armature.pose.bones.get(target_bone_name) is None:
            messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {target_bone_name}"))

    valid_target_writes = {
        target_bone_name: target_writes[target_bone_name]
        for target_bone_name in written_target_names
    }
    order_filter_ms = _elapsed_ms(order_started_at)

    apply_ms = 0.0
    apply_detail_timings: dict[str, float] = {}
    if valid_target_writes:
        apply_started_at = perf_counter()
        pose_matrices.apply_pose_matrix_map(
            context,
            target_armature,
            valid_target_writes,
            update_view_layer=update_view_layer,
            timings=apply_detail_timings,
            ordered_bone_names=written_target_names,
        )
        apply_ms = _elapsed_ms(apply_started_at)
    elif update_view_layer:
        update_started_at = perf_counter()
        context.view_layer.update()
        view_update_ms += _elapsed_ms(update_started_at)
    if not messages:
        messages.append(state.ValidationMessage("INFO", f"Solved {len(written_target_names)} target channels."))

    return SolveResult(
        written_targets=len(written_target_names),
        written_target_names=tuple(written_target_names),
        skipped_rows=plan.skipped_rows + skipped_rows,
        skipped_links=plan.skipped_links + skipped_links,
        messages=messages,
        timings=_timings(
            total_started_at,
            build_plan_ms=plan_ms,
            view_update_ms=view_update_ms,
            source_eval_ms=source_eval_ms,
            scope_ms=scope_ms,
            compute_ms=compute_ms,
            order_filter_ms=order_filter_ms,
            apply_ms=apply_ms,
            **apply_detail_timings,
            full_rows=float(len(plan.rows)),
            solved_rows=float(len(rows_to_solve)),
            scoped_sources=float(scoped_source_count),
            target_writes=float(len(target_writes)),
            valid_target_writes=float(len(valid_target_writes)),
            partial=0.0 if source_bone_name_scope is None else 1.0,
        ),
        source_pose_signature=source_pose_signature,
    )


def _rows_for_source_scope(
    rows: tuple[runtime_plan.RuntimePlanRow, ...],
    target_armature: Object,
    source_bone_names: set[str] | None,
    mapped_target_names: tuple[str, ...],
) -> tuple[runtime_plan.RuntimePlanRow, ...]:
    if source_bone_names is None:
        return rows
    if not source_bone_names:
        return ()

    mapped_target_set = set(mapped_target_names)
    direct_target_names = {
        target_channel.bone_name
        for row in rows
        if row.source_bone_name in source_bone_names
        for target_channel in row.target_channels
        if target_channel.bone_name
    }
    if not direct_target_names:
        return ()

    affected_target_names = set(
        runtime_plan.target_descendant_names(
            target_armature,
            direct_target_names,
            mapped_target_set,
        )
    )
    if not affected_target_names:
        return ()

    scoped_rows = []
    for row in rows:
        if row.source_bone_name in source_bone_names:
            scoped_rows.append(row)
            continue

        filtered_target_channels = tuple(
            target_channel
            for target_channel in row.target_channels
            if target_channel.bone_name in affected_target_names
        )
        if filtered_target_channels:
            scoped_rows.append(
                runtime_plan.RuntimePlanRow(
                    source_bone_name=row.source_bone_name,
                    source_work_pose_matrix=row.source_work_pose_matrix,
                    target_channels=filtered_target_channels,
                )
            )

    return tuple(scoped_rows)


def _error_result(message: str, started_at=None) -> SolveResult:
    started_at = started_at or perf_counter()
    return SolveResult(
        written_targets=0,
        written_target_names=(),
        skipped_rows=0,
        skipped_links=0,
        messages=[state.ValidationMessage("ERROR", message)],
        timings=_timings(started_at),
    )


def _elapsed_ms(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000.0


def _timings(started_at: float, **entries: float) -> dict[str, float]:
    timings = dict(entries)
    timings["total_ms"] = _elapsed_ms(started_at)
    return timings


class BRM_OT_solve_one_frame(Operator):
    bl_idname = "bone_remap.solve_one_frame"
    bl_label = "Solve One Frame"
    bl_description = "Solve the current frame from saved Work Pose and Mapping Table"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = solve_active_profile_one_frame(context)
        has_error = False
        for message in result.messages:
            report_type = {"ERROR"} if message.severity == "ERROR" else {"WARNING"} if message.severity == "WARNING" else {"INFO"}
            has_error = has_error or message.severity == "ERROR"
            self.report(report_type, message.text)

        if result.written_targets > 0:
            self.report({"INFO"}, f"Wrote {result.written_targets} target pose matrices.")

        return {"CANCELLED"} if has_error else {"FINISHED"}


_CLASSES = (
    BRM_OT_solve_one_frame,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
