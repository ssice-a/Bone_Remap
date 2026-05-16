"""Blender-independent Auto Match Array Core."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Iterable, Sequence

import numpy as np


WEIGHT_EPSILON = 1.0e-8
DEFAULT_POINT_TARGET = 128
DEFAULT_SEAM_POSITION_TOLERANCE = 1.0e-5
DEFAULT_SEAM_WEIGHT_TOLERANCE = 1.0e-4
MAX_SOURCE_CANDIDATES_PER_TARGET = 16
MAX_VECTORIZED_DISTANCE_PAIRS = 65536


@dataclass(frozen=True)
class WeightedPointCloud:
    name: str
    channel_names: tuple[str, ...]
    points: np.ndarray
    weights: np.ndarray
    seam_points: np.ndarray | None = None
    seam_weights: np.ndarray | None = None
    seam_ids: tuple[object, ...] | None = None

    def __post_init__(self) -> None:
        points = np.asarray(self.points, dtype=np.float64)
        weights = np.asarray(self.weights, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError(f"{self.name}: points must have shape (N, 3)")
        if weights.ndim != 1 or weights.shape[0] != points.shape[0]:
            raise ValueError(f"{self.name}: weights must have shape (N,)")
        channel_names = tuple(str(name) for name in self.channel_names if str(name))
        if not channel_names:
            channel_names = (str(self.name),)
        seam_points = points if self.seam_points is None else np.asarray(self.seam_points, dtype=np.float64)
        seam_weights = weights if self.seam_weights is None else np.asarray(self.seam_weights, dtype=np.float64)
        if seam_points.ndim != 2 or seam_points.shape[1] != 3:
            raise ValueError(f"{self.name}: seam_points must have shape (N, 3)")
        if seam_weights.ndim != 1 or seam_weights.shape[0] != seam_points.shape[0]:
            raise ValueError(f"{self.name}: seam_weights must have shape (N,)")
        if self.seam_ids is None:
            seam_ids = tuple((str(self.name), index) for index in range(seam_points.shape[0]))
        else:
            seam_ids = tuple(self.seam_ids)
        if len(seam_ids) != seam_points.shape[0]:
            raise ValueError(f"{self.name}: seam_ids must have length N")
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "weights", weights)
        object.__setattr__(self, "channel_names", channel_names)
        object.__setattr__(self, "seam_points", seam_points)
        object.__setattr__(self, "seam_weights", seam_weights)
        object.__setattr__(self, "seam_ids", seam_ids)


@dataclass(frozen=True)
class Assignment:
    source_name: str
    target_names: tuple[str, ...]
    score: float


@dataclass(frozen=True)
class AssignmentPlan:
    assignments: tuple[Assignment, ...]


def build_assignment_plan(
    source_clouds: Sequence[WeightedPointCloud],
    target_clouds: Sequence[WeightedPointCloud],
    *,
    max_score: float | None = None,
    candidate_max_gap: float | None = None,
    point_target: int = DEFAULT_POINT_TARGET,
    seam_position_tolerance: float = DEFAULT_SEAM_POSITION_TOLERANCE,
    seam_weight_tolerance: float = DEFAULT_SEAM_WEIGHT_TOLERANCE,
) -> AssignmentPlan:
    """Build planned source-to-target assignments from visible weighted point clouds."""

    target_clouds = build_target_seam_clusters(
        target_clouds,
        position_tolerance=seam_position_tolerance,
        weight_tolerance=seam_weight_tolerance,
    )
    compressed_sources = tuple(
        deterministic_point_cloud_compression(cloud, point_target=point_target)
        for cloud in source_clouds
        if _has_usable_points(cloud)
    )
    compressed_targets = tuple(
        deterministic_point_cloud_compression(cloud, point_target=point_target)
        for cloud in target_clouds
        if _has_usable_points(cloud)
    )
    compressed_source_entries = tuple(
        (source, _cloud_bounds(source), _weighted_centroid(source))
        for source in compressed_sources
    )
    assignments: list[Assignment] = []

    for target in compressed_targets:
        best_source = None
        best_score = float("inf")
        target_bounds = _cloud_bounds(target)
        target_centroid = _weighted_centroid(target)
        for source in _candidate_sources_for_target(
            target_bounds,
            target_centroid,
            compressed_source_entries,
            max_gap=candidate_max_gap if candidate_max_gap is not None else max_score,
        ):
            score = bidirectional_weighted_nearest_point_distance(source, target)
            if score < best_score:
                best_score = score
                best_source = source
        if best_source is None:
            continue
        if max_score is not None and best_score > float(max_score):
            continue
        assignments.append(
            Assignment(
                source_name=best_source.name,
                target_names=target.channel_names,
                score=float(best_score),
            )
        )

    return AssignmentPlan(assignments=tuple(assignments))


def build_target_seam_clusters(
    target_clouds: Sequence[WeightedPointCloud],
    *,
    position_tolerance: float = DEFAULT_SEAM_POSITION_TOLERANCE,
    weight_tolerance: float = DEFAULT_SEAM_WEIGHT_TOLERANCE,
) -> tuple[WeightedPointCloud, ...]:
    """Join target clouds whose split seam vertices have matching weight signatures."""

    clouds = tuple(target_clouds)
    if len(clouds) < 2:
        return clouds

    parent = list(range(len(clouds)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    seam_vertices: dict[object, dict[str, object]] = {}
    tolerance_squared = float(position_tolerance) * float(position_tolerance)
    for cloud_index, cloud in enumerate(clouds):
        if not _has_usable_points(cloud):
            continue
        seam_points = cloud.seam_points
        seam_weights = cloud.seam_weights
        seam_ids = cloud.seam_ids
        if seam_points is None or seam_weights is None or seam_ids is None:
            continue
        for point, weight, seam_id in zip(seam_points, seam_weights, seam_ids):
            weight = float(weight)
            if weight <= WEIGHT_EPSILON:
                continue
            vertex = seam_vertices.setdefault(
                seam_id,
                {
                    "point": np.asarray(point, dtype=np.float64),
                    "entries": [],
                },
            )
            entries = vertex["entries"]
            entries.append((cloud_index, weight))

    prepared_vertices = {
        seam_id: (
            vertex["point"],
            _prepare_seam_vertex_entries(vertex["entries"], weight_tolerance),
        )
        for seam_id, vertex in seam_vertices.items()
    }

    seam_index: dict[tuple[int, int, int], list[object]] = {}
    for seam_id, (point, entries) in prepared_vertices.items():
        if not entries:
            continue
        cell = _cell_key(point, position_tolerance)
        for neighbor_cell in _neighbor_keys(cell):
            for other_seam_id in seam_index.get(neighbor_cell, ()):
                if other_seam_id == seam_id:
                    continue
                other_point, other_entries = prepared_vertices[other_seam_id]
                if not other_entries:
                    continue
                delta = point - other_point
                if float(np.dot(delta, delta)) > tolerance_squared:
                    continue
                matched_pairs = _matching_seam_entry_pairs(entries, other_entries, weight_tolerance)
                for cloud_index, other_cloud_index in matched_pairs:
                    if cloud_index != other_cloud_index:
                        union(cloud_index, other_cloud_index)
        seam_index.setdefault(cell, []).append(seam_id)

    groups: dict[int, list[int]] = {}
    for index in range(len(clouds)):
        groups.setdefault(find(index), []).append(index)

    clustered: list[WeightedPointCloud] = []
    for indexes in groups.values():
        if len(indexes) == 1:
            clustered.append(clouds[indexes[0]])
            continue
        parts = [clouds[index] for index in indexes]
        channel_names = tuple(
            channel_name
            for part in parts
            for channel_name in part.channel_names
        )
        clustered.append(
            WeightedPointCloud(
                name="+".join(part.name for part in parts),
                channel_names=channel_names,
                points=np.vstack([part.points for part in parts]),
                weights=np.concatenate([part.weights for part in parts]),
                seam_points=np.vstack([part.seam_points for part in parts]),
                seam_weights=np.concatenate([part.seam_weights for part in parts]),
                seam_ids=tuple(seam_id for part in parts for seam_id in part.seam_ids),
            )
        )
    return tuple(clustered)


def _prepare_seam_vertex_entries(
    entries: list[tuple[int, float]],
    weight_tolerance: float,
) -> tuple[tuple[int, float], ...]:
    best_by_cloud: dict[int, float] = {}
    for cloud_index, weight in entries:
        current = best_by_cloud.get(cloud_index)
        if current is None or weight > current:
            best_by_cloud[int(cloud_index)] = float(weight)
    prepared = tuple(
        sorted(
            best_by_cloud.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )
    if _has_ambiguous_weight_order(prepared, weight_tolerance):
        return ()
    return prepared


def _matching_seam_entry_pairs(
    left: tuple[tuple[int, float], ...],
    right: tuple[tuple[int, float], ...],
    weight_tolerance: float,
) -> tuple[tuple[int, int], ...]:
    if len(left) != len(right):
        return ()
    pairs: list[tuple[int, int]] = []
    for (left_index, left_weight), (right_index, right_weight) in zip(left, right):
        if abs(float(left_weight) - float(right_weight)) > float(weight_tolerance):
            return ()
        pairs.append((int(left_index), int(right_index)))
    return tuple(pairs)


def _has_ambiguous_weight_order(
    entries: tuple[tuple[int, float], ...],
    weight_tolerance: float,
) -> bool:
    for index in range(1, len(entries)):
        if abs(float(entries[index - 1][1]) - float(entries[index][1])) <= float(weight_tolerance):
            return True
    return False


def bidirectional_weighted_nearest_point_distance(
    source: WeightedPointCloud,
    target: WeightedPointCloud,
) -> float:
    """Return symmetric weighted nearest-point distance in visible space."""

    tolerance = _match_tolerance(source.points, target.points)
    source_to_target = _weighted_nearest_distance(source.points, source.weights, target.points, tolerance)
    target_to_source = _weighted_nearest_distance(target.points, target.weights, source.points, tolerance)
    return (source_to_target + target_to_source) * 0.5


def deterministic_point_cloud_compression(
    cloud: WeightedPointCloud,
    *,
    point_target: int = DEFAULT_POINT_TARGET,
) -> WeightedPointCloud:
    """Reduce a point cloud while keeping high-weight samples and visible-space coverage."""

    if len(cloud.points) <= int(point_target):
        return cloud
    point_target = max(1, int(point_target))
    top_weight_count = min(point_target, max(1, point_target // 4))
    selected_indices: list[int] = []
    selected: set[int] = set()

    def add(index: int) -> None:
        if index in selected or len(selected_indices) >= point_target:
            return
        selected.add(index)
        selected_indices.append(index)

    order_by_weight = np.lexsort((
        cloud.points[:, 2],
        cloud.points[:, 1],
        cloud.points[:, 0],
        -cloud.weights,
    ))
    for index in order_by_weight[:top_weight_count].tolist():
        add(int(index))

    if len(selected_indices) < point_target:
        diag = _points_diag(cloud.points)
        cell_size = max(diag * 0.08, 1.0e-5)
        cell_keys = np.floor(cloud.points / cell_size).astype(np.int64)
        best_by_cell: dict[tuple[int, int, int], int] = {}
        for index, cell in enumerate(cell_keys):
            key = int(cell[0]), int(cell[1]), int(cell[2])
            current = best_by_cell.get(key)
            if current is None or _sample_rank(cloud, index) < _sample_rank(cloud, current):
                best_by_cell[key] = int(index)
        representatives = sorted(best_by_cell.values(), key=lambda item: _spatial_rank(cloud, item))
        for index in _evenly_spaced_indices(representatives, point_target - len(selected_indices)):
            add(index)
            if len(selected_indices) >= point_target:
                break

    for index in order_by_weight.tolist():
        add(int(index))
        if len(selected_indices) >= point_target:
            break

    chosen = np.asarray(selected_indices, dtype=np.intp)
    return WeightedPointCloud(
        name=cloud.name,
        channel_names=cloud.channel_names,
        points=cloud.points[chosen],
        weights=cloud.weights[chosen],
        seam_points=cloud.seam_points,
        seam_weights=cloud.seam_weights,
        seam_ids=cloud.seam_ids,
    )


def _weighted_nearest_distance(
    query_points: np.ndarray,
    query_weights: np.ndarray,
    reference_points: np.ndarray,
    tolerance: float,
) -> float:
    positive = query_weights > WEIGHT_EPSILON
    if not bool(np.any(positive)) or len(reference_points) == 0:
        return float("inf")

    query_points = query_points[positive]
    query_weights = query_weights[positive]
    penalty = max(_points_diag(np.vstack((query_points, reference_points))), float(tolerance) * 4.0)
    if len(query_points) * len(reference_points) <= MAX_VECTORIZED_DISTANCE_PAIRS:
        return _weighted_nearest_distance_vectorized(
            query_points,
            query_weights,
            reference_points,
            tolerance,
            penalty,
        )

    spatial_hash = _build_spatial_hash(reference_points, tolerance)
    distance_sum = 0.0
    weight_sum = 0.0
    for point, weight in zip(query_points, query_weights):
        distance = _nearest_distance(point, reference_points, spatial_hash, tolerance)
        if distance is None:
            distance = penalty
        distance_sum += float(distance) * float(weight)
        weight_sum += float(weight)
    if weight_sum <= WEIGHT_EPSILON:
        return float("inf")
    return distance_sum / weight_sum


def _weighted_nearest_distance_vectorized(
    query_points: np.ndarray,
    query_weights: np.ndarray,
    reference_points: np.ndarray,
    tolerance: float,
    penalty: float,
) -> float:
    deltas = query_points[:, np.newaxis, :] - reference_points[np.newaxis, :, :]
    distances_squared = np.einsum("ijk,ijk->ij", deltas, deltas)
    nearest_squared = np.min(distances_squared, axis=1)
    tolerance_squared = float(tolerance) * float(tolerance)
    distances = np.where(
        nearest_squared <= tolerance_squared,
        np.sqrt(nearest_squared),
        float(penalty),
    )
    weight_sum = float(np.sum(query_weights))
    if weight_sum <= WEIGHT_EPSILON:
        return float("inf")
    return float(np.dot(distances, query_weights) / weight_sum)


def _nearest_distance(
    point: np.ndarray,
    reference_points: np.ndarray,
    spatial_hash: dict[tuple[int, int, int], np.ndarray],
    tolerance: float,
) -> float | None:
    key = _cell_key(point, tolerance)
    candidate_indices = [
        spatial_hash[neighbor]
        for neighbor in _neighbor_keys(key)
        if neighbor in spatial_hash
    ]
    if not candidate_indices:
        return None
    indices = np.concatenate(candidate_indices) if len(candidate_indices) > 1 else candidate_indices[0]
    deltas = reference_points[indices] - point
    distances_squared = np.einsum("ij,ij->i", deltas, deltas)
    best = float(np.min(distances_squared))
    if best > float(tolerance) * float(tolerance):
        return None
    return best ** 0.5


def _build_spatial_hash(points: np.ndarray, cell_size: float) -> dict[tuple[int, int, int], np.ndarray]:
    cell_keys = np.floor(points / max(float(cell_size), 1.0e-6)).astype(np.int64)
    buckets: dict[tuple[int, int, int], list[int]] = {}
    for index, cell in enumerate(cell_keys):
        buckets.setdefault((int(cell[0]), int(cell[1]), int(cell[2])), []).append(int(index))
    return {
        key: np.asarray(indices, dtype=np.intp)
        for key, indices in buckets.items()
    }


def _cell_key(point: Iterable[float], cell_size: float) -> tuple[int, int, int]:
    inverse = 1.0 / max(float(cell_size), 1.0e-6)
    values = tuple(float(value) for value in point)
    return (
        floor(values[0] * inverse),
        floor(values[1] * inverse),
        floor(values[2] * inverse),
    )


def _neighbor_keys(base_key: tuple[int, int, int]):
    base_x, base_y, base_z = base_key
    for offset_x in (-1, 0, 1):
        for offset_y in (-1, 0, 1):
            for offset_z in (-1, 0, 1):
                yield base_x + offset_x, base_y + offset_y, base_z + offset_z


def _match_tolerance(source_points: np.ndarray, target_points: np.ndarray) -> float:
    points = np.vstack((source_points, target_points))
    return max(_points_diag(points) * 0.015, 1.0e-5)


def _points_diag(points: np.ndarray) -> float:
    if len(points) == 0:
        return 0.0
    bounds_min = np.min(points, axis=0)
    bounds_max = np.max(points, axis=0)
    return float(np.linalg.norm(bounds_max - bounds_min))


def _candidate_sources_for_target(
    target_bounds: tuple[np.ndarray, np.ndarray],
    target_centroid: np.ndarray,
    source_entries: tuple[tuple[WeightedPointCloud, tuple[np.ndarray, np.ndarray], np.ndarray], ...],
    *,
    max_gap: float | None,
) -> tuple[WeightedPointCloud, ...]:
    if max_gap is None:
        return tuple(source for source, _bounds, _centroid in source_entries)

    candidates = []
    for source, source_bounds, source_centroid in source_entries:
        bounds_gap = _bounds_gap(target_bounds, source_bounds)
        if bounds_gap > float(max_gap):
            continue
        centroid_gap = float(np.linalg.norm(target_centroid - source_centroid))
        candidates.append((source, bounds_gap, centroid_gap))

    candidates.sort(key=lambda item: (item[1], item[2], item[0].name))
    return tuple(
        source
        for source, _bounds_gap_value, _centroid_gap in candidates[:MAX_SOURCE_CANDIDATES_PER_TARGET]
    )


def _cloud_bounds(cloud: WeightedPointCloud) -> tuple[np.ndarray, np.ndarray]:
    return np.min(cloud.points, axis=0), np.max(cloud.points, axis=0)


def _weighted_centroid(cloud: WeightedPointCloud) -> np.ndarray:
    weights = np.maximum(cloud.weights, 0.0)
    weight_sum = float(np.sum(weights))
    if weight_sum <= WEIGHT_EPSILON:
        return np.mean(cloud.points, axis=0)
    return np.sum(cloud.points * weights[:, np.newaxis], axis=0) / weight_sum


def _bounds_gap(
    left: tuple[np.ndarray, np.ndarray],
    right: tuple[np.ndarray, np.ndarray],
) -> float:
    left_min, left_max = left
    right_min, right_max = right
    low_gap = right_min - left_max
    high_gap = left_min - right_max
    axis_gap = np.maximum(np.maximum(low_gap, high_gap), 0.0)
    return float(np.linalg.norm(axis_gap))


def _sample_rank(cloud: WeightedPointCloud, index: int) -> tuple[float, float, float, float]:
    point = cloud.points[int(index)]
    return (
        -float(cloud.weights[int(index)]),
        float(point[0]),
        float(point[1]),
        float(point[2]),
    )


def _spatial_rank(cloud: WeightedPointCloud, index: int) -> tuple[float, float, float]:
    point = cloud.points[int(index)]
    return float(point[0]), float(point[1]), float(point[2])


def _evenly_spaced_indices(indices: list[int], count: int) -> list[int]:
    if count <= 0 or not indices:
        return []
    if len(indices) <= count:
        return list(indices)
    positions = np.linspace(0, len(indices) - 1, int(count))
    selected_positions: list[int] = []
    used_positions: set[int] = set()
    for position in positions:
        rounded = int(round(float(position)))
        if rounded not in used_positions:
            used_positions.add(rounded)
            selected_positions.append(rounded)
    cursor = 0
    while len(selected_positions) < count and cursor < len(indices):
        if cursor not in used_positions:
            used_positions.add(cursor)
            selected_positions.append(cursor)
        cursor += 1
    selected_positions.sort()
    return [indices[position] for position in selected_positions[:count]]


def _has_usable_points(cloud: WeightedPointCloud) -> bool:
    return len(cloud.points) > 0 and bool(np.any(cloud.weights > WEIGHT_EPSILON))
