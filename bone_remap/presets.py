"""Retarget preset import/export."""

import json

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import live_preview, mapping, runtime_plan, state


PRESET_VERSION = 1


def export_profile(profile) -> dict:
    return {
        "version": PRESET_VERSION,
        "mapping_rows": [
            {
                "source_bone_name": row.source_bone_name,
                "target_links": [link.target_bone_name for link in row.target_links],
            }
            for row in profile.mapping_rows
        ],
        "work_pose_matrices": [
            {
                "bone_name": item.bone_name,
                "matrix": list(item.matrix),
            }
            for item in profile.work_pose_matrices
        ],
        "input_compensations": [
            {
                "bone_name": item.bone_name,
                "matrix": list(item.matrix),
            }
            for item in profile.input_compensations
        ],
        "classification_overrides": [
            {
                "bone_name": item.bone_name,
                "classification": item.classification,
            }
            for item in profile.classification_overrides
        ],
        "target_bind_matrices": [
            {
                "target_bone_name": item.target_bone_name,
                "matrix": list(item.matrix),
            }
            for item in profile.target_bind_matrices
        ],
    }


def import_profile(context, profile, data: dict) -> list[str]:
    old_targets = runtime_plan.mapped_target_names(profile)

    profile.mapping_rows.clear()
    for row_data in data.get("mapping_rows", []):
        row = profile.mapping_rows.add()
        row.source_bone_name = row_data.get("source_bone_name", "")
        row.active_target_link_index = -1
        for target_bone_name in row_data.get("target_links", []):
            link = row.target_links.add()
            link.target_bone_name = target_bone_name
        if row.target_links:
            row.active_target_link_index = 0
    mapping.set_active_mapping_row_index(profile, 0)

    _replace_matrix_collection(profile.work_pose_matrices, data.get("work_pose_matrices", []), "bone_name")
    profile.work_pose_saved = len(profile.work_pose_matrices) > 0
    _replace_matrix_collection(profile.input_compensations, data.get("input_compensations", []), "bone_name")
    _replace_overrides(profile, data.get("classification_overrides", []))
    _replace_matrix_collection(profile.target_bind_matrices, data.get("target_bind_matrices", []), "target_bone_name")

    new_targets = set(runtime_plan.mapped_target_names(profile))
    leaving_targets = [target for target in old_targets if target not in new_targets]
    if profile.target_armature is not None:
        live_preview.cleanup_removed_target_links(context, profile, profile.target_armature, leaving_targets)

    _solve_live_preview_if_enabled(context)
    return _missing_references(profile)


def _replace_matrix_collection(collection, items, name_field: str) -> None:
    collection.clear()
    for item_data in items:
        matrix = item_data.get("matrix")
        name = item_data.get(name_field, "")
        if not name or not isinstance(matrix, list) or len(matrix) != 16:
            continue
        item = collection.add()
        setattr(item, name_field, name)
        item.matrix = matrix


def _replace_overrides(profile, items) -> None:
    profile.classification_overrides.clear()
    for item_data in items:
        bone_name = item_data.get("bone_name", "")
        classification = item_data.get("classification", "OUTPUT")
        if not bone_name or classification not in {"INPUT", "OUTPUT"}:
            continue
        item = profile.classification_overrides.add()
        item.bone_name = bone_name
        item.classification = classification


def _missing_references(profile) -> list[str]:
    missing = []
    source_bones = {bone.name for bone in profile.source_armature.pose.bones} if profile.source_armature else set()
    target_bones = {bone.name for bone in profile.target_armature.pose.bones} if profile.target_armature else set()

    for row in profile.mapping_rows:
        if row.source_bone_name not in source_bones:
            missing.append(f"Missing source bone: {row.source_bone_name}")
        for link in row.target_links:
            if link.target_bone_name not in target_bones:
                missing.append(f"Missing target bone: {link.target_bone_name}")
    return missing


def _solve_live_preview_if_enabled(context) -> None:
    from . import live_preview

    live_preview.solve_if_enabled(context, reason="preset_imported")


class BRM_OT_preset_export(Operator, ExportHelper):
    bl_idname = "bone_remap.preset_export"
    bl_label = "Export Retarget Preset"
    bl_description = "Export reusable retarget setup without Motion Action data"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(export_profile(profile), file, indent=2)
        self.report({"INFO"}, f"Exported Retarget Preset: {self.filepath}")
        return {"FINISHED"}


class BRM_OT_preset_import(Operator, ImportHelper):
    bl_idname = "bone_remap.preset_import"
    bl_label = "Import Retarget Preset"
    bl_description = "Import reusable retarget setup and replace the current Mapping Table"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}

        with open(self.filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        missing = import_profile(context, profile, data)
        for message in missing[:10]:
            self.report({"WARNING"}, message)
        if len(missing) > 10:
            self.report({"WARNING"}, f"{len(missing) - 10} more missing references.")

        self.report({"INFO"}, "Imported Retarget Preset and replaced Mapping Table.")
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_preset_export,
    BRM_OT_preset_import,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
