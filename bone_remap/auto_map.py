"""Auto Map From Work Pose using weighted geometry."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import bpy
from bpy.types import Operator
from mathutils import Vector

from . import mapping, state, work_pose


WEIGHT_EPSILON = 1.0e-5
ACCEPTANCE_SCORE = 0.28


@dataclass
class WeightedRegion:
    bone_name: str
    centroid: Vector
    radius: float
    weight_sum: float
    vertex_count: int


class _RegionAccumulator:
    def __init__(self, bone_name: str):
        self.bone_name = bone_name
        self.weight_sum = 0.0
        self.weighted_sum = Vector((0.0, 0.0, 0.0))
        self.weighted_sq_sum = 0.0
        self.vertex_count = 0

    def add(self, coordinate: Vector, weight: float) -> None:
        self.weight_sum += weight
        self.weighted_sum += coordinate * weight
        self.weighted_sq_sum += coordinate.length_squared * weight
        self.vertex_count += 1

    def to_region(self) -> WeightedRegion | None:
        if self.weight_sum <= WEIGHT_EPSILON or self.vertex_count == 0:
            return None

        centroid = self.weighted_sum / self.weight_sum
        variance = max(0.0, self.weighted_sq_sum / self.weight_sum - centroid.length_squared)
        return WeightedRegion(
            bone_name=self.bone_name,
            centroid=centroid,
            radius=sqrt(variance),
            weight_sum=self.weight_sum,
            vertex_count=self.vertex_count,
        )


def auto_map_active_profile(context) -> tuple[int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    if not work_pose.has_saved_work_pose(profile):
        return 0, "Auto Map requires a saved Work Pose."

    source_meshes = _bound_meshes(context.scene, active_context.source_armature)
    target_meshes = _bound_meshes(context.scene, active_context.target_armature)
    if not source_meshes:
        return 0, "No source meshes bound to Source Armature."
    if not target_meshes:
        return 0, "No target meshes bound to Target Armature."

    source_regions = _weighted_regions(source_meshes, active_context.source_armature)
    target_regions = _weighted_regions(target_meshes, active_context.target_armature)
    if not source_regions:
        return 0, "No usable source weighted regions with exact bone-name vertex groups."
    if not target_regions:
        return 0, "No usable target weighted regions with exact bone-name vertex groups."

    source_regions = _apply_source_work_pose(profile, active_context.source_armature, source_regions)
    source_regions = _normalize_regions(source_regions)
    target_regions = _normalize_regions(target_regions)
    if not source_regions or not target_regions:
        return 0, "Auto Map needs non-degenerate weighted geometry."

    matched = 0
    for target_region in target_regions:
        source_region, score = _best_source_region(target_region, source_regions)
        if source_region is None or score > ACCEPTANCE_SCORE:
            continue
        row, _created = mapping.ensure_mapping_row(profile, source_region.bone_name)
        mapping.assign_targets_to_row(profile, row, [target_region.bone_name])
        matched += 1

    if matched:
        _solve_live_preview_if_enabled(context)
    return matched, f"Auto Map assigned {matched} target channels."


def _bound_meshes(scene, armature):
    meshes = []
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object == armature:
                meshes.append(obj)
                break
    return meshes


def _weighted_regions(meshes, armature) -> list[WeightedRegion]:
    bone_names = {bone.name for bone in armature.pose.bones}
    accumulators: dict[str, _RegionAccumulator] = {}
    armature_world_inverse = armature.matrix_world.inverted_safe()

    for mesh_obj in meshes:
        mesh_world = mesh_obj.matrix_world
        vertex_group_names = {
            group.index: group.name
            for group in mesh_obj.vertex_groups
            if group.name in bone_names
        }
        if not vertex_group_names:
            continue

        for vertex in mesh_obj.data.vertices:
            coordinate = armature_world_inverse @ (mesh_world @ vertex.co)
            for group_ref in vertex.groups:
                bone_name = vertex_group_names.get(group_ref.group)
                if bone_name is None or group_ref.weight <= WEIGHT_EPSILON:
                    continue
                accumulator = accumulators.setdefault(bone_name, _RegionAccumulator(bone_name))
                accumulator.add(coordinate, group_ref.weight)

    regions = []
    for accumulator in accumulators.values():
        region = accumulator.to_region()
        if region is not None:
            regions.append(region)
    return regions


def _apply_source_work_pose(profile, source_armature, regions: list[WeightedRegion]) -> list[WeightedRegion]:
    work_pose_matrices = {
        item.bone_name: work_pose.matrix_from_flat(item.matrix)
        for item in profile.work_pose_matrices
    }
    transformed = []
    for region in regions:
        source_bone = source_armature.data.bones.get(region.bone_name)
        work_matrix = work_pose_matrices.get(region.bone_name)
        if source_bone is None or work_matrix is None:
            transformed.append(region)
            continue
        delta = work_matrix @ source_bone.matrix_local.inverted_safe()
        transformed.append(WeightedRegion(
            bone_name=region.bone_name,
            centroid=delta @ region.centroid,
            radius=region.radius * _average_scale(delta),
            weight_sum=region.weight_sum,
            vertex_count=region.vertex_count,
        ))
    return transformed


def _average_scale(matrix) -> float:
    scale = matrix.to_scale()
    return max(WEIGHT_EPSILON, (abs(scale.x) + abs(scale.y) + abs(scale.z)) / 3.0)


def _normalize_regions(regions: list[WeightedRegion]) -> list[WeightedRegion]:
    if not regions:
        return []

    center = Vector((0.0, 0.0, 0.0))
    for region in regions:
        center += region.centroid
    center /= len(regions)

    scale = max((region.centroid - center).length + region.radius for region in regions)
    if scale <= WEIGHT_EPSILON:
        return []

    return [
        WeightedRegion(
            bone_name=region.bone_name,
            centroid=(region.centroid - center) / scale,
            radius=region.radius / scale,
            weight_sum=region.weight_sum,
            vertex_count=region.vertex_count,
        )
        for region in regions
    ]


def _best_source_region(target_region: WeightedRegion, source_regions: list[WeightedRegion]):
    best_region = None
    best_score = float("inf")
    for source_region in source_regions:
        score = (target_region.centroid - source_region.centroid).length
        score += 0.25 * abs(target_region.radius - source_region.radius)
        if score < best_score:
            best_score = score
            best_region = source_region
    return best_region, best_score


def _solve_live_preview_if_enabled(context) -> None:
    from . import live_preview

    live_preview.solve_if_enabled(context, reason="auto_map")


class BRM_OT_auto_map_from_work_pose(Operator):
    bl_idname = "bone_remap.auto_map_from_work_pose"
    bl_label = "Auto Map From Work Pose"
    bl_description = "Assign target channels from weighted geometry compared under saved Work Pose"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        matched, message = auto_map_active_profile(context)
        if matched == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_auto_map_from_work_pose,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
