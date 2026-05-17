"""Auto Match Visible Meshes using weighted point clouds."""

from __future__ import annotations

from time import perf_counter

import bpy
from bpy.types import Operator
from mathutils.kdtree import KDTree
import numpy as np

from . import auto_match_core, mapping, runtime_plan, state, weighted_geometry
from .registration import register_classes, unregister_classes


CANDIDATE_GAP_RATIO = 0.03
MIN_SCORE_LIMIT = 1.0e-4


def auto_match_active_profile(context) -> tuple[int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    source_meshes = _mesh_refs(profile.auto_match_source_meshes)
    target_meshes = _mesh_refs(profile.auto_match_target_meshes)
    if not source_meshes or not target_meshes:
        return 0, "Auto Match Mesh Scope needs source and target meshes."

    source_filter = _existing_source_row_names(profile, active_context.source_armature)
    source_started_at = perf_counter()
    source_field = weighted_geometry.visible_source_weight_field(
        context,
        source_meshes,
        active_context.source_armature,
        allowed_bone_names=source_filter,
    )
    source_seconds = perf_counter() - source_started_at
    if source_field is None:
        if source_filter:
            return 0, "No usable source vertex weights for Mapping Table source rows."
        return 0, "No usable source vertex weights with exact bone-name vertex groups."

    was_live_enabled = _pause_live_preview_for_target_sampling(profile)
    try:
        target_started_at = perf_counter()
        target_clouds = weighted_geometry.visible_weighted_point_clouds(
            context,
            target_meshes,
            active_context.target_armature,
        )
        target_seconds = perf_counter() - target_started_at
    finally:
        if was_live_enabled:
            profile.live_preview_enabled = True

    if not target_clouds:
        return 0, "No usable target weighted point clouds with exact bone-name vertex groups."

    plan_started_at = perf_counter()
    plan = auto_match_core.build_projection_assignment_plan(
        source_field,
        target_clouds,
        max_projection_distance=_projection_max_distance(source_field, target_clouds),
        nearest_indices=_nearest_indices_for_source_field(source_field),
    )
    plan_seconds = perf_counter() - plan_started_at
    apply_started_at = perf_counter()
    matched = apply_assignment_plan(profile, plan, source_row_names=source_filter)
    apply_seconds = perf_counter() - apply_started_at
    if matched:
        _solve_live_preview_if_enabled(context)
    return matched, (
        f"Auto Match assigned {matched} target channels "
        f"(source {source_seconds:.2f}s, target {target_seconds:.2f}s, "
        f"match {plan_seconds:.2f}s, apply {apply_seconds:.2f}s)."
    )


def apply_assignment_plan(
    profile,
    plan: auto_match_core.AssignmentPlan,
    source_row_names: tuple[str, ...] | None = None,
) -> int:
    if source_row_names:
        _clear_existing_target_links(profile)
    else:
        profile.mapping_rows.clear()
        mapping.set_active_mapping_row_index(profile, -1)
    runtime_plan.invalidate_runtime_plan(profile)

    matched = 0
    for assignment in plan.assignments:
        row, _created = mapping.ensure_mapping_row(profile, assignment.source_name)
        mapping.assign_targets_to_row(profile, row, list(assignment.target_names))
        matched += len(assignment.target_names)
    return matched


def _existing_source_row_names(profile, source_armature) -> tuple[str, ...] | None:
    if not profile.mapping_rows:
        return None

    source_bone_names = {bone.name for bone in source_armature.pose.bones}
    names: list[str] = []
    seen: set[str] = set()
    for row in profile.mapping_rows:
        source_bone_name = row.source_bone_name
        if not source_bone_name or source_bone_name not in source_bone_names:
            continue
        if source_bone_name in seen:
            continue
        seen.add(source_bone_name)
        names.append(source_bone_name)
    return tuple(names)


def _clear_existing_target_links(profile) -> None:
    for row in profile.mapping_rows:
        row.target_links.clear()
        row.active_target_link_index = -1


def add_selected_meshes_to_scope(context, collection) -> int:
    meshes = [
        obj
        for obj in context.selected_objects
        if obj is not None and obj.type == "MESH"
    ]
    return _add_mesh_refs(collection, meshes)


def add_bound_meshes_to_scope(context) -> tuple[int, int]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, 0

    source_meshes = weighted_geometry.bound_meshes(context.scene, active_context.source_armature)
    target_meshes = weighted_geometry.bound_meshes(context.scene, active_context.target_armature)
    source_count = _add_mesh_refs(active_context.profile.auto_match_source_meshes, source_meshes)
    target_count = _add_mesh_refs(active_context.profile.auto_match_target_meshes, target_meshes)
    return source_count, target_count


def clear_mesh_scope(profile) -> int:
    count = len(profile.auto_match_source_meshes) + len(profile.auto_match_target_meshes)
    profile.auto_match_source_meshes.clear()
    profile.auto_match_target_meshes.clear()
    return count


def _mesh_refs(collection) -> list:
    return [
        item.mesh
        for item in collection
        if item.mesh is not None and item.mesh.type == "MESH"
    ]


def _add_mesh_refs(collection, meshes: list) -> int:
    existing = {
        item.mesh.as_pointer()
        for item in collection
        if item.mesh is not None
    }
    added = 0
    for mesh in meshes:
        if mesh is None or mesh.type != "MESH":
            continue
        pointer = mesh.as_pointer()
        if pointer in existing:
            continue
        item = collection.add()
        item.mesh = mesh
        existing.add(pointer)
        added += 1
    return added


def _candidate_gap(
    source_clouds: tuple[auto_match_core.WeightedPointCloud, ...],
    target_clouds: tuple[auto_match_core.WeightedPointCloud, ...],
) -> float:
    diag = weighted_geometry.visible_point_cloud_diag((*source_clouds, *target_clouds))
    return max(MIN_SCORE_LIMIT, float(diag) * CANDIDATE_GAP_RATIO)


def _projection_max_distance(
    source_field: auto_match_core.SourceWeightField,
    target_clouds: tuple[auto_match_core.WeightedPointCloud, ...],
) -> float:
    point_sets = [source_field.points]
    point_sets.extend(cloud.points for cloud in target_clouds if len(cloud.points))
    if not point_sets:
        return MIN_SCORE_LIMIT
    points = np.vstack(point_sets)
    bounds_min = np.min(points, axis=0)
    bounds_max = np.max(points, axis=0)
    diag = float(np.linalg.norm(bounds_max - bounds_min))
    return max(MIN_SCORE_LIMIT, diag * CANDIDATE_GAP_RATIO)


def _nearest_indices_for_source_field(source_field: auto_match_core.SourceWeightField):
    kd_tree = KDTree(len(source_field.points))
    for index, point in enumerate(source_field.points):
        kd_tree.insert(tuple(float(value) for value in point), int(index))
    kd_tree.balance()

    def nearest_indices(query_points):
        return [
            int(kd_tree.find(tuple(float(value) for value in point))[1])
            for point in query_points
        ]

    return nearest_indices


def _pause_live_preview_for_target_sampling(profile) -> bool:
    was_enabled = bool(profile.live_preview_enabled)
    if was_enabled:
        profile.live_preview_enabled = False
    return was_enabled


def _solve_live_preview_if_enabled(context) -> None:
    from . import live_preview

    live_preview.solve_if_enabled(context, reason="auto_match")


class BRM_OT_auto_match_visible_meshes(Operator):
    bl_idname = "bone_remap.auto_match_visible_meshes"
    bl_label = "Auto Match"
    bl_description = "Match visible source and target weighted mesh point clouds into the Mapping Table"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        matched, message = auto_match_active_profile(context)
        if matched == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


class BRM_OT_auto_match_add_selected_source_meshes(Operator):
    bl_idname = "bone_remap.auto_match_add_selected_source_meshes"
    bl_label = "Add Source Meshes"
    bl_description = "Add selected Mesh objects to the source Auto Match Mesh Scope"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}
        added = add_selected_meshes_to_scope(context, profile.auto_match_source_meshes)
        self.report({"INFO"}, f"Added {added} source mesh(es) to Auto Match scope.")
        return {"FINISHED"} if added else {"CANCELLED"}


class BRM_OT_auto_match_add_selected_target_meshes(Operator):
    bl_idname = "bone_remap.auto_match_add_selected_target_meshes"
    bl_label = "Add Target Meshes"
    bl_description = "Add selected Mesh objects to the target Auto Match Mesh Scope"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}
        added = add_selected_meshes_to_scope(context, profile.auto_match_target_meshes)
        self.report({"INFO"}, f"Added {added} target mesh(es) to Auto Match scope.")
        return {"FINISHED"} if added else {"CANCELLED"}


class BRM_OT_auto_match_add_bound_meshes(Operator):
    bl_idname = "bone_remap.auto_match_add_bound_meshes"
    bl_label = "Use Bound Meshes"
    bl_description = "Add meshes bound to the active Source and Target Armatures to Auto Match Mesh Scope"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        source_count, target_count = add_bound_meshes_to_scope(context)
        if source_count == 0 and target_count == 0:
            self.report({"WARNING"}, "No new bound source or target meshes found.")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Added {source_count} source and {target_count} target mesh(es).")
        return {"FINISHED"}


class BRM_OT_auto_match_clear_mesh_scope(Operator):
    bl_idname = "bone_remap.auto_match_clear_mesh_scope"
    bl_label = "Clear Mesh Scope"
    bl_description = "Clear source and target meshes from Auto Match Mesh Scope"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = state.get_active_profile(context.scene)
        if profile is None:
            self.report({"ERROR"}, "No Active Retarget Profile.")
            return {"CANCELLED"}
        cleared = clear_mesh_scope(profile)
        self.report({"INFO"}, f"Cleared {cleared} Auto Match mesh reference(s).")
        return {"FINISHED"} if cleared else {"CANCELLED"}


_CLASSES = (
    BRM_OT_auto_match_visible_meshes,
    BRM_OT_auto_match_add_selected_source_meshes,
    BRM_OT_auto_match_add_selected_target_meshes,
    BRM_OT_auto_match_add_bound_meshes,
    BRM_OT_auto_match_clear_mesh_scope,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
