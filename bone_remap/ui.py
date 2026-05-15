"""User interface for the Bone Remap workbench shell."""

from __future__ import annotations

import bpy
from bpy.types import Panel, UIList

from . import mapping, state, work_pose
from .properties import ACTIVE_PROFILE_INDEX_ATTR, PROFILE_COLLECTION_ATTR


def _validation_icon(severity: str) -> str:
    if severity == "ERROR":
        return "ERROR"
    if severity == "WARNING":
        return "ERROR"
    return "CHECKMARK"


class BRM_UL_retarget_profiles(UIList):
    bl_idname = "BRM_UL_retarget_profiles"

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class BRM_UL_mapping_rows(UIList):
    bl_idname = "BRM_UL_mapping_rows"

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            row.prop(item, "source_bone_name", text="", emboss=False, icon_value=icon)
            row.label(text=str(len(item.target_links)), icon="LINKED")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class BRM_UL_target_links(UIList):
    bl_idname = "BRM_UL_target_links"

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.prop(item, "target_bone_name", text="", emboss=False, icon_value=icon)
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class BRM_PT_retarget_workbench(Panel):
    bl_idname = "BRM_PT_retarget_workbench"
    bl_label = "Bone Remap"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bone Remap"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list(
            BRM_UL_retarget_profiles.bl_idname,
            "",
            scene,
            PROFILE_COLLECTION_ATTR,
            scene,
            ACTIVE_PROFILE_INDEX_ATTR,
            rows=3,
        )

        buttons = row.column(align=True)
        buttons.operator("bone_remap.profile_add", text="", icon="ADD")
        buttons.operator("bone_remap.profile_remove", text="", icon="REMOVE")

        profile = state.get_active_profile(scene)
        if profile is None:
            layout.label(text="No Active Retarget Profile", icon="INFO")
            return

        box = layout.box()
        box.prop(profile, "name", text="Name")
        box.prop(profile, "source_armature")
        box.operator("bone_remap.set_source_from_active", icon="ARMATURE_DATA")
        box.prop(profile, "target_armature")
        box.operator("bone_remap.set_target_from_active", icon="ARMATURE_DATA")

        work_pose_box = layout.box()
        work_pose_box.label(text="Work Pose")
        status_text = "Editing" if profile.work_pose_editing else "Saved" if profile.work_pose_saved else "Not Saved"
        status_icon = "GREASEPENCIL" if profile.work_pose_editing else "CHECKMARK" if profile.work_pose_saved else "INFO"
        work_pose_box.label(
            text=f"{status_text} ({len(profile.work_pose_matrices)} bones)",
            icon=status_icon,
        )
        layer_action = profile.work_pose_action.name if profile.work_pose_action is not None else "None"
        work_pose_box.label(text=f"Layer: {layer_action}", icon="ACTION")

        row = work_pose_box.row(align=True)
        row.operator("bone_remap.work_pose_enter", icon="ARMATURE_DATA")
        row.operator("bone_remap.work_pose_save", icon="CHECKMARK")

        row = work_pose_box.row(align=True)
        row.operator("bone_remap.work_pose_cancel", icon="CANCEL")
        row.operator("bone_remap.work_pose_reset_to_rest")
        input_count, output_count, ambiguous_count = work_pose.classification_summary(profile)
        work_pose_box.label(
            text=f"Classification: {input_count} input / {output_count} output / {ambiguous_count} ambiguous",
            icon="INFO",
        )
        for index, item in enumerate(profile.classification_report):
            if index >= 5:
                break
            work_pose_box.label(text=f"{item.bone_name}: {item.classification}", icon=_validation_icon("WARNING" if item.classification == "AMBIGUOUS_OUTPUT" else "INFO"))
        if len(profile.classification_report) > 5:
            work_pose_box.label(text=f"{len(profile.classification_report) - 5} more classifications", icon="INFO")
        row = work_pose_box.row(align=True)
        op = row.operator("bone_remap.classification_override_set", text="Override Input")
        op.classification = "INPUT"
        op = row.operator("bone_remap.classification_override_set", text="Override Output")
        op.classification = "OUTPUT"
        work_pose_box.operator("bone_remap.classification_override_clear", icon="X")

        mapping_box = layout.box()
        mapping_box.label(text="Mapping Table")

        row = mapping_box.row()
        row.template_list(
            BRM_UL_mapping_rows.bl_idname,
            "",
            profile,
            "mapping_rows",
            profile,
            "active_mapping_row_index",
            rows=5,
        )

        buttons = row.column(align=True)
        buttons.operator("bone_remap.mapping_add_source_rows", text="", icon="ADD")
        buttons.operator("bone_remap.mapping_remove_active_source_row", text="", icon="REMOVE")

        active_row = mapping.get_active_mapping_row(profile)
        if active_row is None:
            mapping_box.label(text="No Destination Source Row", icon="INFO")
        else:
            mapping_box.label(text=f"Destination: {active_row.source_bone_name}", icon="FORWARD")
            mapping_box.template_list(
                BRM_UL_target_links.bl_idname,
                "",
                active_row,
                "target_links",
                active_row,
                "active_target_link_index",
                rows=4,
            )
            mapping_box.operator("bone_remap.mapping_remove_active_target_link", icon="REMOVE")

        row = mapping_box.row(align=True)
        row.operator("bone_remap.mapping_assign_selected_targets", icon="LINKED")
        row.operator("bone_remap.mapping_unassign_selected_targets", icon="UNLINKED")
        row = mapping_box.row(align=True)
        row.operator("bone_remap.mapping_reveal_active_target_owner", icon="VIEWZOOM")

        revealed_target = profile.revealed_target_bone_name or "None"
        revealed_owner = profile.revealed_owner_source_bone_name or "Unmapped"
        mapping_box.label(text=f"Active Target Owner: {revealed_target} -> {revealed_owner}")
        mapping_box.operator("bone_remap.mapping_use_revealed_owner_as_destination", icon="FORWARD")

        health_box = layout.box()
        health_box.label(text="Mapping Health")
        health_messages = mapping.mapping_health_messages(profile, profile.source_armature, profile.target_armature)
        for message in health_messages[:6]:
            health_box.label(text=message.text, icon=_validation_icon(message.severity))
        if len(health_messages) > 6:
            health_box.label(text=f"{len(health_messages) - 6} more issues", icon="INFO")
        health_box.operator("bone_remap.mapping_report_health", icon="INFO")
        mapping_box.operator("bone_remap.auto_map_from_work_pose", icon="MOD_VERTEX_WEIGHT")

        solve_box = layout.box()
        solve_box.label(text="One Frame Solve")
        solve_box.operator("bone_remap.solve_one_frame", icon="PLAY")

        live_box = layout.box()
        live_box.label(text="Live Preview")
        live_status = "Enabled" if profile.live_preview_enabled else "Disabled"
        live_icon = "PLAY" if profile.live_preview_enabled else "PAUSE"
        live_box.label(
            text=f"{live_status} ({len(profile.live_preview_last_written_targets)} last targets)",
            icon=live_icon,
        )
        row = live_box.row(align=True)
        row.operator("bone_remap.live_preview_enable", icon="PLAY")
        row.operator("bone_remap.live_preview_disable", icon="PAUSE")
        live_box.operator("bone_remap.live_preview_clear", icon="CANCEL")
        if profile.live_preview_last_result:
            live_box.label(text=profile.live_preview_last_result, icon="INFO")

        motion_box = layout.box()
        motion_box.label(text="Motion Edit")
        motion_status = "Editing" if profile.motion_editing else "Inactive"
        motion_action = profile.active_motion_action.name if profile.active_motion_action is not None else "None"
        motion_box.label(text=f"{motion_status}: {motion_action}", icon="ACTION")
        row = motion_box.row(align=True)
        row.operator("bone_remap.motion_edit_enter", icon="GREASEPENCIL")
        row.operator("bone_remap.motion_edit_exit", icon="CANCEL")
        motion_box.operator("bone_remap.motion_action_duplicate", icon="DUPLICATE")

        bake_box = layout.box()
        bake_box.label(text="Bake")
        bake_box.prop(profile, "bake_use_range_override")
        if profile.bake_use_range_override:
            row = bake_box.row(align=True)
            row.prop(profile, "bake_frame_start")
            row.prop(profile, "bake_frame_end")
        bake_box.prop(profile, "bake_overwrite_existing")
        bake_box.operator("bone_remap.bake_live_result", icon="REC")
        if profile.bake_last_result:
            bake_box.label(text=profile.bake_last_result, icon="INFO")

        preset_box = layout.box()
        preset_box.label(text="Presets")
        row = preset_box.row(align=True)
        row.operator("bone_remap.preset_export", icon="EXPORT")
        row.operator("bone_remap.preset_import", icon="IMPORT")

        calibration_box = layout.box()
        calibration_box.label(text="Target Calibration")
        calibration_box.operator("bone_remap.channel_align_heads", icon="ARMATURE_DATA")
        calibration_box.operator("bone_remap.target_bind_refresh", icon="CHECKMARK")
        calibration_box.label(text=f"Stored target binds: {len(profile.target_bind_matrices)}", icon="INFO")

        validation_box = layout.box()
        validation_box.label(text="Profile Validation")
        for message in state.validate_profile(profile):
            validation_box.label(text=message.text, icon=_validation_icon(message.severity))
        validation_box.operator("bone_remap.report_active_profile", icon="INFO")


_CLASSES = (
    BRM_UL_retarget_profiles,
    BRM_UL_mapping_rows,
    BRM_UL_target_links,
    BRM_PT_retarget_workbench,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
