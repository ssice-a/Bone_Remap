"""Automatic Live Preview around the one-frame solver."""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent
from bpy.types import Object, Operator

from . import solver, state


_IS_SOLVING = False


def is_enabled(profile) -> bool:
    return bool(profile is not None and profile.live_preview_enabled)


def solve_if_enabled(context, reason: str = "manual", depsgraph=None, update_view_layer: bool = True):
    profile = state.get_active_profile(context.scene)
    if not is_enabled(profile):
        return None
    return solve_now(context, reason=reason, depsgraph=depsgraph, update_view_layer=update_view_layer)


def solve_now(context, reason: str = "manual", depsgraph=None, update_view_layer: bool = True):
    global _IS_SOLVING

    if _IS_SOLVING:
        return None

    profile = state.get_active_profile(context.scene)
    if profile is None:
        return None

    _IS_SOLVING = True
    try:
        result = solver.solve_active_profile_one_frame(
            context,
            depsgraph=depsgraph,
            update_view_layer=update_view_layer,
        )
        _record_live_result(profile, result, reason)
        return result
    finally:
        _IS_SOLVING = False


def _record_live_result(profile, result: solver.SolveResult, reason: str) -> None:
    if result.written_target_names:
        profile.live_preview_last_written_targets.clear()
        for target_bone_name in result.written_target_names:
            item = profile.live_preview_last_written_targets.add()
            item.target_bone_name = target_bone_name

    errors = [message.text for message in result.messages if message.severity == "ERROR"]
    if errors:
        profile.live_preview_last_result = errors[0]
    else:
        profile.live_preview_last_result = f"{reason}: wrote {result.written_targets} target channels"


def clear_live_preview(context, profile, target_armature: Object) -> tuple[int, list[state.ValidationMessage]]:
    target_bone_names = _last_live_written_target_names(profile)
    if not target_bone_names:
        target_bone_names = _mapped_target_names(profile)

    reset_count, messages = reset_target_channels_to_bind(context, target_armature, target_bone_names)
    profile.live_preview_last_written_targets.clear()
    profile.live_preview_last_result = f"clear: reset {reset_count} target channels"
    return reset_count, messages


def cleanup_removed_target_links(context, profile, target_armature: Object, target_bone_names: list[str]) -> int:
    removed_names = [name for name in _unique_names(target_bone_names) if not _target_is_mapped(profile, name)]
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

    target_writes = {}
    for target_bone_name in _unique_names(target_bone_names):
        profile = state.get_active_profile(context.scene)
        bind_matrix = solver.target_bind_matrix_for_bone(target_armature, target_bone_name, profile)
        if bind_matrix is None:
            messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {target_bone_name}"))
            continue
        target_writes[target_bone_name] = bind_matrix

    written = 0
    for target_bone_name in solver.target_write_order(target_armature, target_writes):
        pose_bone = target_armature.pose.bones.get(target_bone_name)
        if pose_bone is None:
            messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {target_bone_name}"))
            continue
        pose_bone.matrix = target_writes[target_bone_name]
        written += 1

    if target_writes:
        context.view_layer.update()

    if not messages:
        messages.append(state.ValidationMessage("INFO", f"Reset {written} target channels to bind/rest."))
    return written, messages


def _last_live_written_target_names(profile) -> list[str]:
    return [item.target_bone_name for item in profile.live_preview_last_written_targets if item.target_bone_name]


def _mapped_target_names(profile) -> list[str]:
    return _unique_names([
        link.target_bone_name
        for row in profile.mapping_rows
        for link in row.target_links
        if link.target_bone_name
    ])


def _target_is_mapped(profile, target_bone_name: str) -> bool:
    for row in profile.mapping_rows:
        if any(link.target_bone_name == target_bone_name for link in row.target_links):
            return True
    return False


def _remove_last_live_written_targets(profile, target_bone_names: list[str]) -> None:
    removed_names = set(target_bone_names)
    if not removed_names:
        return

    for index in range(len(profile.live_preview_last_written_targets) - 1, -1, -1):
        if profile.live_preview_last_written_targets[index].target_bone_name in removed_names:
            profile.live_preview_last_written_targets.remove(index)


def _unique_names(names: list[str]) -> list[str]:
    seen = set()
    unique = []
    for name in names:
        if name and name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


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
    target = profile.target_armature
    if source is None:
        return False

    source_data = source.data
    target_data = target.data if target is not None else None
    for update in depsgraph.updates:
        updated_id = update.id
        if updated_id == source or updated_id == source_data or updated_id == target_data:
            return True

    return False


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
    solve_if_enabled(context, reason="depsgraph_update", depsgraph=depsgraph, update_view_layer=False)


def _append_once(handler_list, handler) -> None:
    if handler not in handler_list:
        handler_list.append(handler)


def _remove_if_present(handler_list, handler) -> None:
    while handler in handler_list:
        handler_list.remove(handler)


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

        profile.live_preview_enabled = True
        result = solve_now(context, reason="enabled")
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

        profile.live_preview_enabled = False
        profile.live_preview_last_result = "disabled; target pose left unchanged"
        self.report({"INFO"}, "Live Preview disabled; Target Armature pose left unchanged.")
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
    BRM_OT_live_preview_clear,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    _append_once(bpy.app.handlers.frame_change_post, _frame_change_post)
    _append_once(bpy.app.handlers.depsgraph_update_post, _depsgraph_update_post)


def unregister():
    _remove_if_present(bpy.app.handlers.depsgraph_update_post, _depsgraph_update_post)
    _remove_if_present(bpy.app.handlers.frame_change_post, _frame_change_post)

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
