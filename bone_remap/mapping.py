"""Source-first Mapping Table helpers and operators."""

from __future__ import annotations

from collections import Counter

import bpy
from bpy.types import Object, Operator

from . import state


def get_active_mapping_row(profile):
    index = profile.active_mapping_row_index
    if 0 <= index < len(profile.mapping_rows):
        return profile.mapping_rows[index]
    return None


def set_active_mapping_row_index(profile, index: int) -> None:
    if not profile.mapping_rows:
        profile.active_mapping_row_index = -1
        return
    profile.active_mapping_row_index = max(0, min(index, len(profile.mapping_rows) - 1))


def find_row_index_by_source(profile, source_bone_name: str) -> int:
    for index, row in enumerate(profile.mapping_rows):
        if row.source_bone_name == source_bone_name:
            return index
    return -1


def find_owner_row(profile, target_bone_name: str):
    for index, row in enumerate(profile.mapping_rows):
        if any(link.target_bone_name == target_bone_name for link in row.target_links):
            return index, row
    return -1, None


def ensure_mapping_row(profile, source_bone_name: str):
    existing_index = find_row_index_by_source(profile, source_bone_name)
    if existing_index >= 0:
        set_active_mapping_row_index(profile, existing_index)
        return profile.mapping_rows[existing_index], False

    row = profile.mapping_rows.add()
    row.source_bone_name = source_bone_name
    row.active_target_link_index = -1
    set_active_mapping_row_index(profile, len(profile.mapping_rows) - 1)
    return row, True


def assign_targets_to_row(profile, row, target_bone_names: list[str]) -> tuple[int, int]:
    """Assign selected targets to a row; latest assignment wins globally."""

    assigned = 0
    moved = 0
    destination_index = _row_index(profile, row)
    for target_bone_name in _unique_names(target_bone_names):
        previous_owner_indexes = _owner_row_indexes(profile, target_bone_name)
        for previous_owner_index in previous_owner_indexes:
            _remove_target_from_row(profile.mapping_rows[previous_owner_index], target_bone_name)
        if any(previous_owner_index != destination_index for previous_owner_index in previous_owner_indexes):
            moved += 1

        if not any(link.target_bone_name == target_bone_name for link in row.target_links):
            link = row.target_links.add()
            link.target_bone_name = target_bone_name
            row.active_target_link_index = len(row.target_links) - 1
            assigned += 1

    _clamp_target_link_index(row)
    return assigned, moved


def mapped_target_names(profile) -> list[str]:
    return _unique_names([
        link.target_bone_name
        for row in profile.mapping_rows
        for link in row.target_links
        if link.target_bone_name
    ])


def target_is_mapped(profile, target_bone_name: str) -> bool:
    return any(
        link.target_bone_name == target_bone_name
        for row in profile.mapping_rows
        for link in row.target_links
    )


def mapping_health_messages(profile, source_armature: Object | None, target_armature: Object | None) -> list[state.ValidationMessage]:
    messages: list[state.ValidationMessage] = []
    duplicate_counts = Counter()

    source_bones = {bone.name for bone in source_armature.pose.bones} if _is_armature(source_armature) else set()
    target_bones = {bone.name for bone in target_armature.pose.bones} if _is_armature(target_armature) else set()

    for row in profile.mapping_rows:
        if not row.target_links:
            messages.append(state.ValidationMessage("WARNING", f"Unmapped row: {row.source_bone_name}"))

        if row.source_bone_name not in source_bones:
            messages.append(state.ValidationMessage("ERROR", f"Invalid source bone: {row.source_bone_name}"))

        for link in row.target_links:
            duplicate_counts[link.target_bone_name] += 1
            if link.target_bone_name not in target_bones:
                messages.append(state.ValidationMessage("ERROR", f"Invalid target bone: {link.target_bone_name}"))

    for target_bone_name, count in duplicate_counts.items():
        if count > 1:
            messages.append(state.ValidationMessage("ERROR", f"Duplicate target assignment: {target_bone_name}"))

    if not profile.mapping_rows:
        messages.append(state.ValidationMessage("INFO", "Mapping Table is empty."))
    elif not messages:
        messages.append(state.ValidationMessage("INFO", "Mapping Table is healthy."))

    return messages


def selected_bone_names(context, armature: Object) -> list[str]:
    names: list[str] = []

    if context.object == armature and context.mode == "POSE":
        selected_pose_bones = getattr(context, "selected_pose_bones", None) or []
        names.extend(pose_bone.name for pose_bone in selected_pose_bones)

        active_pose_bone = getattr(context, "active_pose_bone", None)
        if active_pose_bone is not None:
            names.append(active_pose_bone.name)

    names.extend(bone.name for bone in armature.data.bones if bone.select)
    return _unique_names(names)


def active_or_selected_bone_name(context, armature: Object) -> str | None:
    if context.object == armature and context.mode == "POSE":
        active_pose_bone = getattr(context, "active_pose_bone", None)
        if active_pose_bone is not None:
            return active_pose_bone.name

    selected = selected_bone_names(context, armature)
    return selected[0] if selected else None


def _remove_target_from_row(row, target_bone_name: str) -> None:
    for index in range(len(row.target_links) - 1, -1, -1):
        if row.target_links[index].target_bone_name == target_bone_name:
            row.target_links.remove(index)
    _clamp_target_link_index(row)


def _owner_row_indexes(profile, target_bone_name: str) -> list[int]:
    indexes = []
    for index, row in enumerate(profile.mapping_rows):
        if any(link.target_bone_name == target_bone_name for link in row.target_links):
            indexes.append(index)
    return indexes


def _row_index(profile, row) -> int:
    row_pointer = row.as_pointer()
    for index, candidate in enumerate(profile.mapping_rows):
        if candidate.as_pointer() == row_pointer:
            return index
    return -1


def _clamp_target_link_index(row) -> None:
    if not row.target_links:
        row.active_target_link_index = -1
        return
    row.active_target_link_index = max(0, min(row.active_target_link_index, len(row.target_links) - 1))


def _active_profile_source(context):
    profile = state.get_active_profile(context.scene)
    if profile is None:
        return None, None, "No Active Retarget Profile."

    source = profile.source_armature
    if not _is_armature(source):
        return None, None, "Source Armature is not assigned or invalid."

    return profile, source, None


def _active_profile_pair(context):
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return None, None, None, "Active Retarget Profile needs valid Source and Target Armatures."
    return active_context.profile, active_context.source_armature, active_context.target_armature, None


def _is_armature(obj) -> bool:
    return obj is not None and obj.type == "ARMATURE"


def _unique_names(names: list[str]) -> list[str]:
    seen = set()
    unique = []
    for name in names:
        if name and name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


class BRM_OT_mapping_add_source_rows(Operator):
    bl_idname = "bone_remap.mapping_add_source_rows"
    bl_label = "Add Source Rows"
    bl_description = "Create Mapping Rows from selected Source Armature bones"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, source, error = _active_profile_source(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        source_bone_names = selected_bone_names(context, source)
        if not source_bone_names:
            self.report({"ERROR"}, "Select one or more bones on the Source Armature.")
            return {"CANCELLED"}

        created = 0
        for source_bone_name in source_bone_names:
            if source_bone_name not in source.pose.bones:
                continue
            _row, was_created = ensure_mapping_row(profile, source_bone_name)
            created += int(was_created)

        _solve_live_preview_if_enabled(context, reason="mapping_source_rows_changed")
        self.report({"INFO"}, f"Added {created} source rows; selected {len(source_bone_names)} source bones.")
        return {"FINISHED"}


class BRM_OT_mapping_remove_active_source_row(Operator):
    bl_idname = "bone_remap.mapping_remove_active_source_row"
    bl_label = "Remove Source Row"
    bl_description = "Remove the Destination Source Row and clean target links that leave the Mapping Table"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, _source, target, error = _active_profile_pair(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        index = profile.active_mapping_row_index
        if not (0 <= index < len(profile.mapping_rows)):
            self.report({"ERROR"}, "Choose a Destination Source Row first.")
            return {"CANCELLED"}

        row = profile.mapping_rows[index]
        removed_targets = [link.target_bone_name for link in row.target_links]
        source_bone_name = row.source_bone_name
        profile.mapping_rows.remove(index)
        set_active_mapping_row_index(profile, min(index, len(profile.mapping_rows) - 1))

        cleanup_count = _cleanup_removed_targets(context, profile, target, removed_targets)
        _solve_live_preview_if_enabled(context, reason="mapping_source_row_removed")
        self.report({"INFO"}, f"Removed {source_bone_name}; cleaned {cleanup_count} target channels.")
        return {"FINISHED"}


class BRM_OT_mapping_assign_selected_targets(Operator):
    bl_idname = "bone_remap.mapping_assign_selected_targets"
    bl_label = "Assign Selected Targets"
    bl_description = "Assign selected Target Armature bones to the Destination Source Row"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, _source, target, error = _active_profile_pair(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        row = get_active_mapping_row(profile)
        if row is None:
            self.report({"ERROR"}, "Choose a Destination Source Row first.")
            return {"CANCELLED"}

        target_bone_names = selected_bone_names(context, target)
        if not target_bone_names:
            self.report({"ERROR"}, "Select one or more bones on the Target Armature.")
            return {"CANCELLED"}

        valid_target_names = [name for name in target_bone_names if name in target.pose.bones]
        assigned, moved = assign_targets_to_row(profile, row, valid_target_names)
        _solve_live_preview_if_enabled(context, reason="mapping_targets_assigned")
        self.report({"INFO"}, f"Assigned {assigned} targets to {row.source_bone_name}; moved {moved}.")
        return {"FINISHED"}


class BRM_OT_mapping_remove_active_target_link(Operator):
    bl_idname = "bone_remap.mapping_remove_active_target_link"
    bl_label = "Remove Target Link"
    bl_description = "Remove the active Target Link and clean it if it leaves the Mapping Table"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, _source, target, error = _active_profile_pair(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        row = get_active_mapping_row(profile)
        if row is None:
            self.report({"ERROR"}, "Choose a Destination Source Row first.")
            return {"CANCELLED"}

        index = row.active_target_link_index
        if not (0 <= index < len(row.target_links)):
            self.report({"ERROR"}, "Choose a Target Link first.")
            return {"CANCELLED"}

        target_bone_name = row.target_links[index].target_bone_name
        row.target_links.remove(index)
        _clamp_target_link_index(row)

        cleanup_count = _cleanup_removed_targets(context, profile, target, [target_bone_name])
        _solve_live_preview_if_enabled(context, reason="mapping_target_link_removed")
        self.report({"INFO"}, f"Removed {target_bone_name}; cleaned {cleanup_count} target channels.")
        return {"FINISHED"}


class BRM_OT_mapping_unassign_selected_targets(Operator):
    bl_idname = "bone_remap.mapping_unassign_selected_targets"
    bl_label = "Unassign Selected Targets"
    bl_description = "Remove selected Target Armature bones from the Mapping Table and clean channels that leave it"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile, _source, target, error = _active_profile_pair(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        target_bone_names = selected_bone_names(context, target)
        if not target_bone_names:
            self.report({"ERROR"}, "Select one or more bones on the Target Armature.")
            return {"CANCELLED"}

        removed = 0
        removed_targets = []
        for row in profile.mapping_rows:
            before = len(row.target_links)
            for target_bone_name in target_bone_names:
                if any(link.target_bone_name == target_bone_name for link in row.target_links):
                    removed_targets.append(target_bone_name)
                _remove_target_from_row(row, target_bone_name)
            removed += before - len(row.target_links)

        cleanup_count = _cleanup_removed_targets(context, profile, target, removed_targets)
        _solve_live_preview_if_enabled(context, reason="mapping_targets_unassigned")
        self.report({"INFO"}, f"Unassigned {removed} target links; cleaned {cleanup_count} target channels.")
        return {"FINISHED"}


class BRM_OT_mapping_reveal_active_target_owner(Operator):
    bl_idname = "bone_remap.mapping_reveal_active_target_owner"
    bl_label = "Reveal Active Target Owner"
    bl_description = "Show which Source Row owns the active or selected Target bone without changing Destination Source Row"
    bl_options = {"REGISTER"}

    def execute(self, context):
        profile, _source, target, error = _active_profile_pair(context)
        if error is not None:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        target_bone_name = active_or_selected_bone_name(context, target)
        if target_bone_name is None:
            self.report({"ERROR"}, "Select a Target Armature bone to reveal ownership.")
            return {"CANCELLED"}

        _owner_index, owner = find_owner_row(profile, target_bone_name)
        profile.revealed_target_bone_name = target_bone_name
        profile.revealed_owner_source_bone_name = owner.source_bone_name if owner is not None else ""

        if owner is None:
            self.report({"INFO"}, f"{target_bone_name} is unmapped.")
        else:
            self.report({"INFO"}, f"{target_bone_name} is owned by {owner.source_bone_name}.")
        return {"FINISHED"}


class BRM_OT_mapping_use_revealed_owner_as_destination(Operator):
    bl_idname = "bone_remap.mapping_use_revealed_owner_as_destination"
    bl_label = "Use Revealed Owner"
    bl_description = "Set Destination Source Row to the last revealed target owner"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        source_bone_name = profile.revealed_owner_source_bone_name
        if not source_bone_name:
            self.report({"ERROR"}, "The revealed target has no owner.")
            return {"CANCELLED"}

        index = find_row_index_by_source(profile, source_bone_name)
        if index < 0:
            self.report({"ERROR"}, "The revealed owner row no longer exists.")
            return {"CANCELLED"}

        set_active_mapping_row_index(profile, index)
        self.report({"INFO"}, f"Destination Source Row set to {source_bone_name}.")
        return {"FINISHED"}


class BRM_OT_mapping_report_health(Operator):
    bl_idname = "bone_remap.mapping_report_health"
    bl_label = "Report Mapping Health"
    bl_description = "Report unmapped rows, invalid references, and duplicate target assignments"
    bl_options = {"REGISTER"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        messages = mapping_health_messages(profile, profile.source_armature, profile.target_armature)
        has_error = False
        for message in messages:
            report_type = {"ERROR"} if message.severity == "ERROR" else {"WARNING"} if message.severity == "WARNING" else {"INFO"}
            has_error = has_error or message.severity == "ERROR"
            self.report(report_type, message.text)

        return {"CANCELLED"} if has_error else {"FINISHED"}


_CLASSES = (
    BRM_OT_mapping_add_source_rows,
    BRM_OT_mapping_remove_active_source_row,
    BRM_OT_mapping_assign_selected_targets,
    BRM_OT_mapping_remove_active_target_link,
    BRM_OT_mapping_unassign_selected_targets,
    BRM_OT_mapping_reveal_active_target_owner,
    BRM_OT_mapping_use_revealed_owner_as_destination,
    BRM_OT_mapping_report_health,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)


def _solve_live_preview_if_enabled(context, reason: str) -> None:
    from . import live_preview

    live_preview.solve_if_enabled(context, reason=reason)


def _cleanup_removed_targets(context, profile, target_armature: Object, target_bone_names: list[str]) -> int:
    from . import live_preview

    return live_preview.cleanup_removed_target_links(context, profile, target_armature, target_bone_names)
