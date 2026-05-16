"""One-frame retarget solve from Work Pose and Mapping Table."""

from __future__ import annotations

from dataclasses import dataclass

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


def solve_active_profile_one_frame(context, depsgraph=None, update_view_layer: bool = True) -> SolveResult:
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
    )


def solve_profile_one_frame(
    context,
    profile,
    source_armature: Object,
    target_armature: Object,
    depsgraph=None,
    update_view_layer: bool = True,
) -> SolveResult:
    if source_armature.mode == "EDIT" or target_armature.mode == "EDIT":
        return _error_result("Leave armature edit mode before solving.")

    plan = runtime_plan.build_runtime_plan(profile, source_armature, target_armature)
    if not plan.rows and any(message.severity == "ERROR" for message in plan.messages):
        return SolveResult(
            written_targets=0,
            written_target_names=(),
            skipped_rows=plan.skipped_rows,
            skipped_links=plan.skipped_links,
            messages=plan.messages,
        )

    if update_view_layer:
        context.view_layer.update()
    depsgraph = depsgraph or context.evaluated_depsgraph_get()
    evaluated_source = source_armature.evaluated_get(depsgraph)
    target_writes: dict[str, Matrix] = {}
    messages: list[state.ValidationMessage] = list(plan.messages)
    skipped_rows = 0
    skipped_links = 0

    for row in plan.rows:
        source_pose_bone = evaluated_source.pose.bones.get(row.source_bone_name)
        if source_pose_bone is None:
            skipped_rows += 1
            messages.append(state.ValidationMessage("ERROR", f"Invalid source bone: {row.source_bone_name}"))
            continue

        source_delta = source_pose_bone.matrix.copy() @ row.source_work_pose_matrix.inverted_safe()
        for target_channel in row.target_channels:
            target_writes[target_channel.bone_name] = source_delta @ target_channel.bind_matrix

    written_target_names = [
        target_bone_name
        for target_bone_name in runtime_plan.target_write_order(target_armature, target_writes)
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
    if valid_target_writes:
        pose_matrices.apply_pose_matrix_map(
            context,
            target_armature,
            valid_target_writes,
            update_view_layer=update_view_layer,
        )
    elif update_view_layer:
        context.view_layer.update()
    if not messages:
        messages.append(state.ValidationMessage("INFO", f"Solved {len(written_target_names)} target channels."))

    return SolveResult(
        written_targets=len(written_target_names),
        written_target_names=tuple(written_target_names),
        skipped_rows=plan.skipped_rows + skipped_rows,
        skipped_links=plan.skipped_links + skipped_links,
        messages=messages,
    )


def _error_result(message: str) -> SolveResult:
    return SolveResult(
        written_targets=0,
        written_target_names=(),
        skipped_rows=0,
        skipped_links=0,
        messages=[state.ValidationMessage("ERROR", message)],
    )


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
