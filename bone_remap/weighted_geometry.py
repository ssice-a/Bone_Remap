"""Weighted mesh region discovery shared by mapping and auto-map commands."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
from mathutils import Vector

from . import auto_match_core


WEIGHT_EPSILON = 1.0e-5


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


def bound_meshes(scene, armature):
    meshes = []
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object == armature:
                meshes.append(obj)
                break
    return meshes


def weighted_regions(meshes, armature) -> list[WeightedRegion]:
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


def visible_weighted_point_clouds(context, meshes, armature) -> tuple[auto_match_core.WeightedPointCloud, ...]:
    """Sample evaluated visible mesh vertices into per-bone weighted point clouds."""

    depsgraph = context.evaluated_depsgraph_get()
    bone_names = {bone.name for bone in armature.pose.bones}
    accumulators: dict[str, dict[str, list]] = {}

    for mesh_obj in meshes:
        if mesh_obj is None or mesh_obj.type != "MESH":
            continue
        vertex_group_names = {
            group.index: group.name
            for group in mesh_obj.vertex_groups
            if group.name in bone_names
        }
        if not vertex_group_names:
            continue

        evaluated_obj = mesh_obj.evaluated_get(depsgraph)
        evaluated_mesh = _evaluated_mesh(evaluated_obj, depsgraph)
        try:
            seam_vertex_indices = _boundary_vertex_indices(evaluated_mesh)
            mesh_world = evaluated_obj.matrix_world
            for vertex in evaluated_mesh.vertices:
                point = _point_tuple(mesh_world @ vertex.co)
                is_seam = int(vertex.index) in seam_vertex_indices
                for group_ref in vertex.groups:
                    bone_name = vertex_group_names.get(group_ref.group)
                    if bone_name is None or group_ref.weight <= WEIGHT_EPSILON:
                        continue
                    bucket = accumulators.setdefault(
                        bone_name,
                        {
                            "points": [],
                            "weights": [],
                            "seam_points": [],
                            "seam_weights": [],
                            "seam_ids": [],
                        },
                    )
                    weight = float(group_ref.weight)
                    bucket["points"].append(point)
                    bucket["weights"].append(weight)
                    if is_seam:
                        bucket["seam_points"].append(point)
                        bucket["seam_weights"].append(weight)
                        bucket["seam_ids"].append(_seam_vertex_id(mesh_obj, vertex.index))
        finally:
            evaluated_obj.to_mesh_clear()

    clouds = []
    for bone_name in sorted(accumulators):
        bucket = accumulators[bone_name]
        points = np.asarray(bucket["points"], dtype=np.float64)
        weights = np.asarray(bucket["weights"], dtype=np.float64)
        seam_points = np.asarray(bucket["seam_points"], dtype=np.float64).reshape((-1, 3))
        seam_weights = np.asarray(bucket["seam_weights"], dtype=np.float64)
        seam_ids = tuple(bucket["seam_ids"])
        if points.size == 0 or not bool(np.any(weights > WEIGHT_EPSILON)):
            continue
        clouds.append(
            auto_match_core.WeightedPointCloud(
                name=bone_name,
                channel_names=(bone_name,),
                points=points.reshape((-1, 3)),
                weights=weights,
                seam_points=seam_points,
                seam_weights=seam_weights,
                seam_ids=seam_ids,
            )
        )
    return tuple(clouds)


def visible_point_cloud_diag(clouds: tuple[auto_match_core.WeightedPointCloud, ...] | list[auto_match_core.WeightedPointCloud]) -> float:
    if not clouds:
        return 0.0
    points = [cloud.points for cloud in clouds if len(cloud.points)]
    if not points:
        return 0.0
    merged = np.vstack(points)
    bounds_min = np.min(merged, axis=0)
    bounds_max = np.max(merged, axis=0)
    return float(np.linalg.norm(bounds_max - bounds_min))


def _evaluated_mesh(evaluated_obj, depsgraph):
    try:
        return evaluated_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    except TypeError:
        return evaluated_obj.to_mesh()


def _boundary_vertex_indices(mesh) -> set[int]:
    if len(mesh.vertices) == 0 or len(mesh.edges) == 0:
        return set()

    edge_face_counts = [0] * len(mesh.edges)
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            edge_index = mesh.loops[loop_index].edge_index
            if 0 <= edge_index < len(edge_face_counts):
                edge_face_counts[edge_index] += 1

    boundary_indices: set[int] = set()
    for edge in mesh.edges:
        if edge.is_loose or edge_face_counts[edge.index] <= 1:
            boundary_indices.update(int(vertex_index) for vertex_index in edge.vertices)
    return boundary_indices


def _point_tuple(vector) -> tuple[float, float, float]:
    return float(vector.x), float(vector.y), float(vector.z)


def _seam_vertex_id(mesh_obj, vertex_index: int) -> tuple[str, int]:
    return mesh_obj.name, int(vertex_index)
