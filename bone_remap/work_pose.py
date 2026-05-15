"""Work Pose edit, capture, and restore workflow."""

from dataclasses import dataclass

import bpy
from bpy.props import EnumProperty
from bpy.types import NlaTrack, Object, Operator
from mathutils import Matrix

from . import state


@dataclass
class WorkPoseEditSession:
    had_animation_data: bool
    original_action: object | None
    original_nla_mutes: list[tuple[NlaTrack, bool]]
    original_pose_matrices: dict[str, tuple[float, ...]]


_EDIT_SESSIONS: dict[tuple[int, int, int], WorkPoseEditSession] = {}


def has_saved_work_pose(profile) -> bool:
    return bool(profile.work_pose_saved and len(profile.work_pose_matrices) > 0)


def capture_work_pose(context, profile, source_armature: Object) -> int:
    """Store evaluated Work Pose matrices for all visible source pose bones."""

    context.view_layer.update()
    evaluated_source = source_armature.evaluated_get(context.evaluated_depsgraph_get())

    profile.work_pose_matrices.clear()
    for pose_bone in _iter_visible_pose_bones(evaluated_source):
        item = profile.work_pose_matrices.add()
        item.bone_name = pose_bone.name
        item.matrix = flatten_matrix(pose_bone.matrix)

    profile.work_pose_saved = len(profile.work_pose_matrices) > 0
    return len(profile.work_pose_matrices)


def apply_saved_work_pose(context, profile, source_armature: Object) -> int:
    """Apply saved Work Pose matrices to the source armature pose bones."""

    reset_source_pose_to_rest(context, source_armature)
    matrix_by_bone_name = profile_work_pose_matrix_map(profile)
    return apply_pose_matrix_map(context, source_armature, matrix_by_bone_name)


def reset_source_pose_to_rest(context, source_armature: Object) -> None:
    """Clear pose transforms without touching source edit-mode bones."""

    for pose_bone in source_armature.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        if pose_bone.rotation_mode == "QUATERNION":
            pose_bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        elif pose_bone.rotation_mode == "AXIS_ANGLE":
            pose_bone.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        else:
            pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)

    context.view_layer.update()


def is_work_pose_editing(context, profile, source_armature: Object) -> bool:
    return _session_key(context, profile, source_armature) in _EDIT_SESSIONS


def classification_summary(profile) -> tuple[int, int, int]:
    input_count = 0
    output_count = 0
    ambiguous_count = 0
    for item in profile.classification_report:
        if item.classification == "INPUT":
            input_count += 1
        elif item.classification == "AMBIGUOUS_OUTPUT":
            ambiguous_count += 1
        else:
            output_count += 1
    return input_count, output_count, ambiguous_count


def _begin_edit_session(context, profile, source_armature: Object) -> None:
    key = _session_key(context, profile, source_armature)
    if key in _EDIT_SESSIONS:
        return

    animation_data = source_armature.animation_data
    original_action = animation_data.action if animation_data is not None else None
    original_nla_mutes = []

    if animation_data is not None:
        animation_data.action = None
        for track in animation_data.nla_tracks:
            original_nla_mutes.append((track, track.mute))
            track.mute = True

    _EDIT_SESSIONS[key] = WorkPoseEditSession(
        had_animation_data=animation_data is not None,
        original_action=original_action,
        original_nla_mutes=original_nla_mutes,
        original_pose_matrices=_capture_current_pose_matrices(source_armature),
    )
    profile.work_pose_editing = True


def _get_edit_session(context, profile, source_armature: Object) -> WorkPoseEditSession | None:
    return _EDIT_SESSIONS.get(_session_key(context, profile, source_armature))


def _finish_edit_session(context, profile, source_armature: Object, restore_pose: bool) -> None:
    key = _session_key(context, profile, source_armature)
    session = _EDIT_SESSIONS.pop(key, None)

    if session is not None and restore_pose:
        _apply_pose_matrices(context, source_armature, session.original_pose_matrices)

    if session is not None and session.had_animation_data:
        animation_data = source_armature.animation_data_create()
        animation_data.action = session.original_action
        for track, mute in session.original_nla_mutes:
            track.mute = mute

    profile.work_pose_editing = False
    context.view_layer.update()


def _capture_current_pose_matrices(source_armature: Object) -> dict[str, tuple[float, ...]]:
    return {
        pose_bone.name: flatten_matrix(pose_bone.matrix)
        for pose_bone in source_armature.pose.bones
    }


def _apply_pose_matrices(context, source_armature: Object, matrices: dict[str, tuple[float, ...]]) -> None:
    matrix_by_bone_name = {
        bone_name: matrix_from_flat(matrix)
        for bone_name, matrix in matrices.items()
    }
    apply_pose_matrix_map(context, source_armature, matrix_by_bone_name)


def _classify_work_pose_changes(profile, source_armature: Object, snapshot_matrices: dict[str, tuple[float, ...]]) -> None:
    changed_bone_names = _changed_source_channels(source_armature, snapshot_matrices)
    solver_input_names = _source_solver_input_bone_names(source_armature)
    mapped_source_names = {row.source_bone_name for row in profile.mapping_rows}
    overrides = {
        item.bone_name: item.classification
        for item in profile.classification_overrides
        if item.bone_name
    }

    profile.classification_report.clear()
    profile.input_compensations.clear()

    for bone_name in changed_bone_names:
        pose_bone = source_armature.pose.bones.get(bone_name)
        if pose_bone is None:
            continue

        override = overrides.get(bone_name)
        if override == "INPUT":
            classification = "INPUT"
            reason = "User override: Input Compensation"
        elif override == "OUTPUT":
            classification = "OUTPUT"
            reason = "User override: Output Compensation"
        elif bone_name in solver_input_names:
            classification = "INPUT"
            reason = "Referenced by visible source constraints as a solver input"
        elif bone_name in mapped_source_names:
            classification = "OUTPUT"
            reason = "Mapped source bone uses Work Pose Matrix as output baseline"
        else:
            classification = "AMBIGUOUS_OUTPUT"
            reason = "Ambiguous source channel; defaulting to Output Compensation"

        report_item = profile.classification_report.add()
        report_item.bone_name = bone_name
        report_item.classification = classification
        report_item.reason = reason

        if classification == "INPUT":
            item = profile.input_compensations.add()
            item.bone_name = bone_name
            item.matrix = flatten_matrix(pose_bone.matrix)


def _changed_source_channels(source_armature: Object, snapshot_matrices: dict[str, tuple[float, ...]]) -> list[str]:
    changed = []
    for pose_bone in source_armature.pose.bones:
        previous = snapshot_matrices.get(pose_bone.name)
        if previous is None:
            changed.append(pose_bone.name)
            continue
        current = flatten_matrix(pose_bone.matrix)
        if _matrix_changed(current, previous):
            changed.append(pose_bone.name)
    return changed


def _matrix_changed(current: tuple[float, ...], previous: tuple[float, ...], epsilon: float = 1.0e-5) -> bool:
    return any(abs(current_value - previous_value) > epsilon for current_value, previous_value in zip(current, previous))


def _source_solver_input_bone_names(source_armature: Object) -> set[str]:
    names = set()
    for pose_bone in source_armature.pose.bones:
        for constraint in pose_bone.constraints:
            target = getattr(constraint, "target", None)
            subtarget = getattr(constraint, "subtarget", "")
            if target == source_armature and subtarget:
                names.add(subtarget)

            pole_target = getattr(constraint, "pole_target", None)
            pole_subtarget = getattr(constraint, "pole_subtarget", "")
            if pole_target == source_armature and pole_subtarget:
                names.add(pole_subtarget)
    return names


def _iter_visible_pose_bones(source_armature: Object):
    for pose_bone in source_armature.pose.bones:
        if getattr(pose_bone.bone, "hide", False):
            continue
        yield pose_bone


def profile_work_pose_matrix_map(profile) -> dict[str, Matrix]:
    return {
        item.bone_name: matrix_from_flat(item.matrix)
        for item in profile.work_pose_matrices
        if item.bone_name
    }


def basis_matrix_map_from_pose_matrices(source_armature: Object, pose_matrix_map: dict[str, Matrix]) -> dict[str, Matrix]:
    basis_matrix_map = {}
    for data_bone in _iter_data_bones_depth_first(source_armature):
        pose_matrix = pose_matrix_map.get(data_bone.name)
        if pose_matrix is None:
            continue

        kwargs = {}
        if data_bone.parent is not None:
            kwargs["parent_matrix"] = pose_matrix_map.get(
                data_bone.parent.name,
                data_bone.parent.matrix_local.copy(),
            )
            kwargs["parent_matrix_local"] = data_bone.parent.matrix_local.copy()

        basis_matrix_map[data_bone.name] = data_bone.convert_local_to_pose(
            pose_matrix,
            data_bone.matrix_local.copy(),
            invert=True,
            **kwargs,
        )
    return basis_matrix_map


def apply_pose_matrix_map(context, source_armature: Object, pose_matrix_map: dict[str, Matrix]) -> int:
    basis_matrix_map = basis_matrix_map_from_pose_matrices(source_armature, pose_matrix_map)
    applied = 0
    for data_bone in _iter_data_bones_depth_first(source_armature):
        pose_bone = source_armature.pose.bones.get(data_bone.name)
        basis_matrix = basis_matrix_map.get(data_bone.name)
        if pose_bone is not None and basis_matrix is not None:
            pose_bone.matrix_basis = basis_matrix
            applied += 1
    context.view_layer.update()
    return applied


def _iter_data_bones_depth_first(source_armature: Object):
    for data_bone in source_armature.data.bones:
        if data_bone.parent is None:
            yield from _walk_data_bone_tree(data_bone)


def _walk_data_bone_tree(data_bone):
    yield data_bone
    for child_bone in data_bone.children:
        yield from _walk_data_bone_tree(child_bone)


def flatten_matrix(matrix: Matrix) -> tuple[float, ...]:
    return tuple(value for row in matrix for value in row)


def matrix_from_flat(values) -> Matrix:
    return Matrix((
        values[0:4],
        values[4:8],
        values[8:12],
        values[12:16],
    ))


def _session_key(context, profile, source_armature: Object) -> tuple[int, int, int]:
    return (context.scene.as_pointer(), profile.as_pointer(), source_armature.as_pointer())


def _active_work_pose_source(context):
    profile = state.get_active_profile(context.scene)
    if profile is None:
        return None, None, "No Active Retarget Profile."

    source = profile.source_armature
    if source is None:
        return None, None, "Source Armature is not assigned."
    if source.type != "ARMATURE":
        return None, None, "Source Armature reference is not an armature."

    return profile, source, None


def _activate_source_pose_mode(context, source_armature: Object) -> None:
    active_object = context.view_layer.objects.active
    if active_object is not None and active_object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    source_armature.select_set(True)
    context.view_layer.objects.active = source_armature
    bpy.ops.object.mode_set(mode="POSE")


class BRM_OT_work_pose_enter(Operator):
    bl_idname = "bone_remap.work_pose_enter"
    bl_label = "Enter Work Pose Edit"
    bl_description = "Enter Work Pose Edit Mode from Source Rest Pose or the saved Work Pose"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_work_pose_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        if is_work_pose_editing(context, profile, source):
            self.report({"INFO"}, "Already editing Work Pose.")
            _activate_source_pose_mode(context, source)
            return {"FINISHED"}

        _begin_edit_session(context, profile, source)
        if has_saved_work_pose(profile):
            applied = apply_saved_work_pose(context, profile, source)
            self.report({"INFO"}, f"Entered Work Pose Edit from saved Work Pose ({applied} bones).")
        else:
            reset_source_pose_to_rest(context, source)
            self.report({"INFO"}, "Entered Work Pose Edit from Source Rest Pose.")

        _activate_source_pose_mode(context, source)
        return {"FINISHED"}


class BRM_OT_work_pose_save(Operator):
    bl_idname = "bone_remap.work_pose_save"
    bl_label = "Save Work Pose"
    bl_description = "Save evaluated Work Pose matrices for the full visible Source Armature"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_work_pose_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        if not is_work_pose_editing(context, profile, source):
            self.report({"ERROR"}, "Enter Work Pose Edit Mode before saving Work Pose.")
            return {"CANCELLED"}

        session = _get_edit_session(context, profile, source)
        if session is None:
            self.report({"ERROR"}, "Work Pose Edit Snapshot is missing.")
            return {"CANCELLED"}

        count = capture_work_pose(context, profile, source)
        _classify_work_pose_changes(profile, source, session.original_pose_matrices)
        _finish_edit_session(context, profile, source, restore_pose=False)
        layered = _ensure_work_pose_layer(context, profile, source)
        reset_source_pose_to_rest(context, source)
        _solve_live_preview_if_enabled(context, reason="work_pose_saved")
        input_count, output_count, ambiguous_count = classification_summary(profile)
        self.report(
            {"INFO"},
            (
                f"Saved Work Pose matrices for {count} visible source bones; "
                f"layered {layered}; "
                f"classified {input_count} input, {output_count} output, {ambiguous_count} ambiguous."
            ),
        )
        return {"FINISHED"}


class BRM_OT_work_pose_cancel(Operator):
    bl_idname = "bone_remap.work_pose_cancel"
    bl_label = "Cancel Work Pose Edit"
    bl_description = "Leave Work Pose Edit Mode without saving changes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_work_pose_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        if not is_work_pose_editing(context, profile, source):
            self.report({"WARNING"}, "Work Pose Edit Mode is not active.")
            return {"CANCELLED"}

        _finish_edit_session(context, profile, source, restore_pose=True)
        self.report({"INFO"}, "Cancelled Work Pose Edit.")
        return {"FINISHED"}


class BRM_OT_work_pose_reset_to_rest(Operator):
    bl_idname = "bone_remap.work_pose_reset_to_rest"
    bl_label = "Reset Work Pose To Rest"
    bl_description = "Explicitly clear the saved Work Pose and return the source pose to rest while editing"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_work_pose_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        profile.work_pose_matrices.clear()
        profile.input_compensations.clear()
        profile.classification_report.clear()
        profile.work_pose_saved = False
        _remove_work_pose_layer(profile, source)
        reset_source_pose_to_rest(context, source)

        if is_work_pose_editing(context, profile, source):
            session = _get_edit_session(context, profile, source)
            if session is not None:
                session.original_pose_matrices = _capture_current_pose_matrices(source)

        _solve_live_preview_if_enabled(context, reason="work_pose_reset")
        self.report({"INFO"}, "Reset saved Work Pose to Source Rest Pose.")
        return {"FINISHED"}


class BRM_OT_classification_override_set(Operator):
    bl_idname = "bone_remap.classification_override_set"
    bl_label = "Set Classification Override"
    bl_description = "Override Work Pose classification for the active Source Armature bone"
    bl_options = {"REGISTER", "UNDO"}

    classification: EnumProperty(
        name="Classification",
        items=(
            ("INPUT", "Input Compensation", ""),
            ("OUTPUT", "Output Compensation", ""),
        ),
        default="OUTPUT",
    )

    def execute(self, context):
        profile, source, error = _active_work_pose_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        bone_name = _active_source_bone_name(context, source)
        if bone_name is None:
            self.report({"ERROR"}, "Select a Source Armature bone.")
            return {"CANCELLED"}

        override = _find_or_create_override(profile, bone_name)
        override.classification = self.classification
        self.report({"INFO"}, f"{bone_name} override set to {self.classification}.")
        return {"FINISHED"}


class BRM_OT_classification_override_clear(Operator):
    bl_idname = "bone_remap.classification_override_clear"
    bl_label = "Clear Classification Override"
    bl_description = "Clear Work Pose classification override for the active Source Armature bone"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_work_pose_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        bone_name = _active_source_bone_name(context, source)
        if bone_name is None:
            self.report({"ERROR"}, "Select a Source Armature bone.")
            return {"CANCELLED"}

        for index in range(len(profile.classification_overrides) - 1, -1, -1):
            if profile.classification_overrides[index].bone_name == bone_name:
                profile.classification_overrides.remove(index)
                self.report({"INFO"}, f"Cleared override for {bone_name}.")
                return {"FINISHED"}

        self.report({"INFO"}, f"{bone_name} has no override.")
        return {"FINISHED"}


def _active_source_bone_name(context, source_armature: Object) -> str | None:
    if context.object == source_armature and context.mode == "POSE":
        active_pose_bone = getattr(context, "active_pose_bone", None)
        if active_pose_bone is not None:
            return active_pose_bone.name
    return None


def _find_or_create_override(profile, bone_name: str):
    for item in profile.classification_overrides:
        if item.bone_name == bone_name:
            return item
    item = profile.classification_overrides.add()
    item.bone_name = bone_name
    return item


def _solve_live_preview_if_enabled(context, reason: str) -> None:
    from . import live_preview

    live_preview.solve_if_enabled(context, reason=reason)


def _ensure_work_pose_layer(context, profile, source_armature: Object) -> int:
    from . import work_pose_layer

    return work_pose_layer.ensure_work_pose_layer(context, profile, source_armature)


def _remove_work_pose_layer(profile, source_armature: Object) -> bool:
    from . import work_pose_layer

    return work_pose_layer.remove_work_pose_layer(profile, source_armature)


_CLASSES = (
    BRM_OT_work_pose_enter,
    BRM_OT_work_pose_save,
    BRM_OT_work_pose_cancel,
    BRM_OT_work_pose_reset_to_rest,
    BRM_OT_classification_override_set,
    BRM_OT_classification_override_clear,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)

    _EDIT_SESSIONS.clear()
