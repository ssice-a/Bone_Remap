"""One-frame retarget solve from Work Pose and Mapping Table."""

from __future__ import annotations

from dataclasses import dataclass

import bpy
from bpy.types import Object, Operator
from mathutils import Matrix

from . import state, work_pose


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
    if not work_pose.has_saved_work_pose(profile):
        return _error_result("Save Work Pose before solving.")
    if not profile.mapping_rows:
        return _error_result("Mapping Table is empty.")

    if source_armature.mode == "EDIT" or target_armature.mode == "EDIT":
        return _error_result("Leave armature edit mode before solving.")

    work_pose_matrices = _work_pose_matrix_by_bone(profile)
    if not work_pose_matrices:
        return _error_result("Saved Work Pose has no matrices.")

    if update_view_layer:
        context.view_layer.update()
    depsgraph = depsgraph or context.evaluated_depsgraph_get()
    evaluated_source = source_armature.evaluated_get(depsgraph)
    target_writes: dict[str, Matrix] = {}
    messages: list[state.ValidationMessage] = []
    skipped_rows = 0
    skipped_links = 0

    for row in profile.mapping_rows:
        source_pose_bone = evaluated_source.pose.bones.get(row.source_bone_name)
        source_work_pose_matrix = work_pose_matrices.get(row.source_bone_name)

        if source_pose_bone is None:
            skipped_rows += 1
            messages.append(state.ValidationMessage("ERROR", f"Invalid source bone: {row.source_bone_name}"))
            continue
        if source_work_pose_matrix is None:
            skipped_rows += 1
            messages.append(state.ValidationMessage("ERROR", f"Missing Work Pose matrix: {row.source_bone_name}"))
            continue
        if not row.target_links:
            skipped_rows += 1
            messages.append(state.ValidationMessage("WARNING", f"Unmapped row: {row.source_bone_name}"))
            continue

        source_delta = source_pose_bone.matrix.copy() @ source_work_pose_matrix.inverted_safe()
        for link in row.target_links:
            target_bind_matrix = target_bind_matrix_for_bone(target_armature, link.target_bone_name, profile)
            if target_bind_matrix is None:
                skipped_links += 1
                messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {link.target_bone_name}"))
                continue

            target_writes[link.target_bone_name] = source_delta @ target_bind_matrix

    written_target_names = []
    for target_bone_name in target_write_order(target_armature, target_writes):
        target_pose_bone = target_armature.pose.bones.get(target_bone_name)
        if target_pose_bone is None:
            skipped_links += 1
            messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {target_bone_name}"))
            continue
        target_pose_bone.matrix = target_writes[target_bone_name]
        written_target_names.append(target_bone_name)

    if update_view_layer:
        context.view_layer.update()
    if not messages:
        messages.append(state.ValidationMessage("INFO", f"Solved {len(written_target_names)} target channels."))

    return SolveResult(
        written_targets=len(written_target_names),
        written_target_names=tuple(written_target_names),
        skipped_rows=skipped_rows,
        skipped_links=skipped_links,
        messages=messages,
    )


def _work_pose_matrix_by_bone(profile) -> dict[str, Matrix]:
    return {
        item.bone_name: work_pose.matrix_from_flat(item.matrix)
        for item in profile.work_pose_matrices
        if item.bone_name
    }


def target_bind_matrix_for_bone(target_armature: Object, target_bone_name: str, profile=None) -> Matrix | None:
    if profile is not None:
        for item in profile.target_bind_matrices:
            if item.target_bone_name == target_bone_name:
                return work_pose.matrix_from_flat(item.matrix)

    target_bone = target_armature.data.bones.get(target_bone_name)
    if target_bone is None:
        return None
    return target_bone.matrix_local.copy()


def target_write_order(target_armature: Object, target_writes: dict[str, Matrix]) -> list[str]:
    return sorted(target_writes, key=lambda bone_name: _bone_depth(target_armature, bone_name))


def _bone_depth(target_armature: Object, bone_name: str) -> int:
    bone = target_armature.data.bones.get(bone_name)
    depth = 0
    while bone is not None and bone.parent is not None:
        depth += 1
        bone = bone.parent
    return depth


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
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
