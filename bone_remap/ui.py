"""User interface for the Bone Remap workbench shell."""

from __future__ import annotations

import bpy
from bpy.types import Panel, UIList

from . import mapping, state
from .properties import ACTIVE_PROFILE_INDEX_ATTR, PROFILE_COLLECTION_ATTR
from .registration import register_classes, unregister_classes


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

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            op = row.operator(
                "bone_remap.mapping_activate_source_row",
                text=item.source_bone_name or "Unnamed Source",
                emboss=False,
                icon="BONE_DATA",
            )
            op.mapping_index = index
            row.label(text=str(len(item.target_links)), icon="LINKED")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class BRM_UL_target_links(UIList):
    bl_idname = "BRM_UL_target_links"

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            op = layout.operator(
                "bone_remap.mapping_activate_target_link",
                text=item.target_bone_name or "Unnamed Target",
                emboss=False,
                icon="BONE_DATA",
            )
            op.target_link_index = index
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

        solve_box = layout.box()
        solve_row = solve_box.row(align=True)
        solve_row.scale_y = 1.25
        solve_row.operator(
            "bone_remap.live_preview_toggle",
            text="Solve",
            icon="PLAY",
            depress=profile.live_preview_enabled,
        )
        if profile.live_preview_last_result and not profile.live_preview_enabled:
            solve_box.label(text=profile.live_preview_last_result, icon="INFO")

        work_pose_box = layout.box()
        work_pose_box.label(text="Work Pose", icon="ARMATURE_DATA")
        row = work_pose_box.row(align=True)
        row.operator(
            "bone_remap.work_pose_enter",
            text="Edit",
            icon="GREASEPENCIL",
            depress=profile.work_pose_editing,
        )
        row.operator("bone_remap.work_pose_save", text="Save", icon="CHECKMARK")
        row.operator("bone_remap.work_pose_cancel", text="Cancel", icon="CANCEL")
        row.operator("bone_remap.work_pose_reset_to_rest", text="Reset", icon="TRASH")

        mapping_box = layout.box()
        mapping_box.label(text="Mapping Table")
        row = mapping_box.row(align=True)
        row.operator("bone_remap.mapping_add_weighted_source_rows", icon="GROUP_VERTEX")
        row.operator("bone_remap.auto_match_visible_meshes", text="Auto Match", icon="MOD_VERTEX_WEIGHT")

        scope_row = mapping_box.row(align=True)
        scope_row.label(
            text=f"Auto Match Meshes: S {len(profile.auto_match_source_meshes)} / T {len(profile.auto_match_target_meshes)}",
            icon="MESH_DATA",
        )
        scope_buttons = mapping_box.row(align=True)
        scope_buttons.operator("bone_remap.auto_match_add_selected_source_meshes", text="Add Src", icon="ADD")
        scope_buttons.operator("bone_remap.auto_match_add_selected_target_meshes", text="Add Tgt", icon="ADD")
        scope_buttons.operator("bone_remap.auto_match_add_bound_meshes", text="Bound", icon="LINKED")
        scope_buttons.operator("bone_remap.auto_match_clear_mesh_scope", text="", icon="TRASH")

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

        link_count = sum(len(row.target_links) for row in profile.mapping_rows)
        health_messages = mapping.mapping_health_messages(profile, profile.source_armature, profile.target_armature)
        issue_count = sum(1 for message in health_messages if message.severity in {"ERROR", "WARNING"})
        mapping_box.label(
            text=f"{len(profile.mapping_rows)} sources / {link_count} targets / {issue_count} issues",
            icon="INFO" if issue_count else "CHECKMARK",
        )

        active_row = mapping.get_active_mapping_row(profile)
        if active_row is None:
            mapping_box.label(text="No Destination Source Row", icon="INFO")
        else:
            mapping_box.label(
                text=f"{active_row.source_bone_name} -> {len(active_row.target_links)} targets",
                icon="FORWARD",
            )
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

        if profile.revealed_target_bone_name:
            revealed_owner = profile.revealed_owner_source_bone_name or "Unmapped"
            mapping_box.label(text=f"{profile.revealed_target_bone_name} -> {revealed_owner}", icon="VIEWZOOM")
            if profile.revealed_owner_source_bone_name:
                mapping_box.operator("bone_remap.mapping_use_revealed_owner_as_destination", icon="FORWARD")
        if issue_count:
            for message in health_messages[:3]:
                if message.severity in {"ERROR", "WARNING"}:
                    mapping_box.label(text=message.text, icon=_validation_icon(message.severity))
            mapping_box.operator("bone_remap.mapping_report_health", icon="INFO")

        motion_box = layout.box()
        motion_box.label(text="Motion Action", icon="ACTION")
        row = motion_box.row(align=True)
        row.prop_search(profile, "active_motion_action", context.blend_data, "actions", text="")
        row.operator("bone_remap.motion_action_duplicate", text="", icon="DUPLICATE")
        motion_box.operator(
            "bone_remap.motion_edit_toggle",
            text="Edit Motion",
            icon="GREASEPENCIL",
            depress=profile.motion_editing,
        )

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

        profile_errors = [message for message in state.validate_profile(profile) if message.severity == "ERROR"]
        if profile_errors:
            validation_box = layout.box()
            validation_box.label(text="Profile Errors", icon="ERROR")
            for message in profile_errors:
                validation_box.label(text=message.text, icon="ERROR")


_CLASSES = (
    BRM_UL_retarget_profiles,
    BRM_UL_mapping_rows,
    BRM_UL_target_links,
    BRM_PT_retarget_workbench,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
