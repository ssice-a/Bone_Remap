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
class SourceWeightField:
    channel_names: tuple[str, ...]
    points: np.ndarray
    influence_indices: tuple[tuple[int, ...], ...]
    influence_weights: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        channel_names = tuple(str(name) for name in self.channel_names if str(name))
        points = np.asarray(self.points, dtype=np.float64)
        if not channel_names:
            raise ValueError("source weight field needs at least one channel")
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("source weight field points must have shape (N, 3)")
        if len(self.influence_indices) != points.shape[0] or len(self.influence_weights) != points.shape[0]:
            raise ValueError("source influence arrays must match point count")

        max_channel_index = len(channel_names) - 1
        prepared_indices = []
        prepared_weights = []
        for indices, weights in zip(self.influence_indices, self.influence_weights):
            if len(indices) != len(weights):
                raise ValueError("source influence index/weight lengths must match")
            row_indices = []
            row_weights = []
            for index, weight in zip(indices, weights):
                channel_index = int(index)
                weight = float(weight)
                if channel_index < 0 or channel_index > max_channel_index:
                    raise ValueError("source influence channel index is out of range")
                if weight <= WEIGHT_EPSILON:
                    continue
                row_indices.append(channel_index)
                row_weights.append(weight)
            prepared_indices.append(tuple(row_indices))
            prepared_weights.append(tuple(row_weights))

        object.__setattr__(self, "channel_names", channel_names)
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "influence_indices", tuple(prepared_indices))
        object.__setattr__(self, "influence_weights", tuple(prepared_weights))


@dataclass(frozen=True)
class Assignment:
    source_name: str
    target_names: tuple[str, ...]
    score: float


@dataclass(frozen=True)
class AssignmentPlan:
    assignments: tuple[Assignment, ...]


def build_assignment_plan(
    source_field: SourceWeightField,
    target_clouds: Sequence[WeightedPointCloud],
    *,
    point_target: int = DEFAULT_POINT_TARGET,
    seam_position_tolerance: float = DEFAULT_SEAM_POSITION_TOLERANCE,
    seam_weight_tolerance: float = DEFAULT_SEAM_WEIGHT_TOLERANCE,
    max_projection_distance: float | None = None,
    min_winner_ratio: float = 0.0,
    nearest_indices=None,
) -> AssignmentPlan:
    """Assign target channels by projecting target vertices onto source weights.

    This reads target vertex groups as evidence and writes only mapping assignments.
    It does not mutate target mesh weights.
    """

    if len(source_field.points) == 0:
        return AssignmentPlan(assignments=())

    target_clouds = build_target_seam_clusters(
        target_clouds,
        position_tolerance=seam_position_tolerance,
        weight_tolerance=seam_weight_tolerance,
    )
    compressed_targets = tuple(
        deterministic_point_cloud_compression(cloud, point_target=point_target)
        for cloud in target_clouds
        if _has_usable_points(cloud)
    )
    assignments: list[Assignment] = []
    nearest_indices = nearest_indices or (lambda query_points: _nearest_source_indices_bruteforce(query_points, source_field.points))

    for target in compressed_targets:
        assignment = _project_target_cloud_to_source(
            source_field,
            target,
            nearest_indices=nearest_indices,
            max_projection_distance=max_projection_distance,
            min_winner_ratio=min_winner_ratio,
        )
        if assignment is not None:
            assignments.append(assignment)

    return AssignmentPlan(assignments=tuple(assignments))


def _project_target_cloud_to_source(
    source_field: SourceWeightField,
    target: WeightedPointCloud,
    *,
    nearest_indices,
    max_projection_distance: float | None,
    min_winner_ratio: float,
) -> Assignment | None:
    positive = target.weights > WEIGHT_EPSILON
    if not bool(np.any(positive)):
        return None

    query_points = target.points[positive]
    query_weights = target.weights[positive]
    source_indices = np.asarray(nearest_indices(query_points), dtype=np.intp)
    if source_indices.shape[0] != query_points.shape[0]:
        raise ValueError("nearest_indices must return one source index per query point")

    scores = np.zeros(len(source_field.channel_names), dtype=np.float64)
    for query_point, target_weight, source_index in zip(query_points, query_weights, source_indices):
        source_index = int(source_index)
        if source_index < 0 or source_index >= len(source_field.points):
            continue
        if max_projection_distance is not None:
            delta = query_point - source_field.points[source_index]
            if float(np.dot(delta, delta)) > float(max_projection_distance) * float(max_projection_distance):
                continue
        for channel_index, source_weight in zip(
            source_field.influence_indices[source_index],
            source_field.influence_weights[source_index],
        ):
            scores[int(channel_index)] += float(target_weight) * float(source_weight)

    best_index = int(np.argmax(scores)) if len(scores) else -1
    if best_index < 0:
        return None
    best_score = float(scores[best_index])
    if best_score <= WEIGHT_EPSILON:
        return None

    total_score = float(np.sum(scores))
    if total_score <= WEIGHT_EPSILON:
        return None
    winner_ratio = best_score / total_score
    if winner_ratio < float(min_winner_ratio):
        return None

    return Assignment(
        source_name=source_field.channel_names[best_index],
        target_names=target.channel_names,
        score=winner_ratio,
    )


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


def _nearest_source_indices_bruteforce(query_points: np.ndarray, source_points: np.ndarray) -> np.ndarray:
    if len(query_points) == 0:
        return np.asarray([], dtype=np.intp)
    if len(source_points) == 0:
        return np.full(len(query_points), -1, dtype=np.intp)

    query_points = np.asarray(query_points, dtype=np.float64)
    source_points = np.asarray(source_points, dtype=np.float64)
    chunk_size = max(1, MAX_VECTORIZED_DISTANCE_PAIRS // max(1, len(source_points)))
    nearest_indices = np.empty(len(query_points), dtype=np.intp)
    for start in range(0, len(query_points), chunk_size):
        stop = min(len(query_points), start + chunk_size)
        deltas = query_points[start:stop, np.newaxis, :] - source_points[np.newaxis, :, :]
        distances_squared = np.einsum("ijk,ijk->ij", deltas, deltas)
        nearest_indices[start:stop] = np.argmin(distances_squared, axis=1)
    return nearest_indices


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


def _points_diag(points: np.ndarray) -> float:
    if len(points) == 0:
        return 0.0
    bounds_min = np.min(points, axis=0)
    bounds_max = np.max(points, axis=0)
    return float(np.linalg.norm(bounds_max - bounds_min))


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
