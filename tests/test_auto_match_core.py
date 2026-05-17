from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = REPO_ROOT / "bone_remap" / "auto_match_core.py"


def load_core():
    spec = importlib.util.spec_from_file_location("bone_remap_auto_match_core", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


core = load_core()


def cloud(name: str, points, weights, channels=None, seam_ids=None):
    return core.WeightedPointCloud(
        name=name,
        channel_names=tuple(channels or (name,)),
        points=np.asarray(points, dtype=np.float64),
        weights=np.asarray(weights, dtype=np.float64),
        seam_ids=seam_ids,
    )


def source_field(channel_names, points, influences):
    return core.SourceWeightField(
        channel_names=tuple(channel_names),
        points=np.asarray(points, dtype=np.float64),
        influence_indices=tuple(tuple(index for index, _weight in row) for row in influences),
        influence_weights=tuple(tuple(weight for _index, weight in row) for row in influences),
    )


class AutoMatchCoreTests(unittest.TestCase):
    def test_assignment_plan_uses_visible_space_weighted_point_clouds(self):
        sources = (
            cloud("SourceArm", [(0.0, 0.0, 0.0), (0.0, 0.1, 0.0)], [1.0, 0.8]),
            cloud("SourceLeg", [(5.0, 0.0, 0.0), (5.0, 0.1, 0.0)], [1.0, 0.8]),
        )
        targets = (
            cloud("TargetArm", [(0.0, 0.0, 0.0), (0.0, 0.1, 0.0)], [1.0, 0.8]),
        )

        plan = core.build_assignment_plan(sources, targets)

        self.assertEqual(
            [(assignment.source_name, assignment.target_names) for assignment in plan.assignments],
            [("SourceArm", ("TargetArm",))],
        )

    def test_assignment_plan_clusters_target_channels_connected_by_matching_seam_points(self):
        sources = (
            cloud(
                "SourceSleeve",
                [(0.0, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 1.0, 0.0), (0.0, 1.5, 0.0)],
                [1.0, 0.8, 0.5, 1.0],
            ),
        )
        targets = (
            cloud("TargetSleeveA", [(0.0, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 1.0, 0.0)], [1.0, 0.8, 0.5]),
            cloud("TargetSleeveB", [(0.0, 1.0, 0.0), (0.0, 1.5, 0.0)], [0.5, 1.0]),
        )

        plan = core.build_assignment_plan(sources, targets)

        self.assertEqual(len(plan.assignments), 1)
        self.assertEqual(plan.assignments[0].source_name, "SourceSleeve")
        self.assertEqual(plan.assignments[0].target_names, ("TargetSleeveA", "TargetSleeveB"))

    def test_target_seam_cluster_requires_distinct_seam_vertices(self):
        targets = (
            cloud("TargetA", [(0.0, 0.0, 0.0)], [1.0], seam_ids=(("mesh", 7),)),
            cloud("TargetB", [(0.0, 0.0, 0.0)], [1.0], seam_ids=(("mesh", 7),)),
            cloud("TargetC", [(1.0, 0.0, 0.0)], [1.0], seam_ids=(("mesh", 8),)),
            cloud("TargetD", [(1.0, 0.0, 0.0)], [1.0], seam_ids=(("mesh", 9),)),
        )

        clusters = core.build_target_seam_clusters(targets)

        cluster_names = {tuple(cluster.channel_names) for cluster in clusters}
        self.assertIn(("TargetA",), cluster_names)
        self.assertIn(("TargetB",), cluster_names)
        self.assertIn(("TargetC", "TargetD"), cluster_names)

    def test_target_seam_cluster_pairs_matching_weight_signatures(self):
        targets = (
            cloud("SplitAHigh", [(0.0, 0.0, 0.0)], [0.7], seam_ids=(("mesh_a", 1),)),
            cloud("SplitALow", [(0.0, 0.0, 0.0)], [0.3], seam_ids=(("mesh_a", 1),)),
            cloud("SplitBHigh", [(0.0, 0.0, 0.0)], [0.7], seam_ids=(("mesh_b", 9),)),
            cloud("SplitBLow", [(0.0, 0.0, 0.0)], [0.3], seam_ids=(("mesh_b", 9),)),
        )

        clusters = core.build_target_seam_clusters(targets)

        cluster_names = {tuple(cluster.channel_names) for cluster in clusters}
        self.assertIn(("SplitAHigh", "SplitBHigh"), cluster_names)
        self.assertIn(("SplitALow", "SplitBLow"), cluster_names)

    def test_target_seam_cluster_skips_ambiguous_equal_weight_signatures(self):
        targets = (
            cloud("SplitAOne", [(0.0, 0.0, 0.0)], [0.5], seam_ids=(("mesh_a", 1),)),
            cloud("SplitATwo", [(0.0, 0.0, 0.0)], [0.5], seam_ids=(("mesh_a", 1),)),
            cloud("SplitBOne", [(0.0, 0.0, 0.0)], [0.5], seam_ids=(("mesh_b", 9),)),
            cloud("SplitBTwo", [(0.0, 0.0, 0.0)], [0.5], seam_ids=(("mesh_b", 9),)),
        )

        clusters = core.build_target_seam_clusters(targets)

        self.assertEqual(
            {tuple(cluster.channel_names) for cluster in clusters},
            {("SplitAOne",), ("SplitATwo",), ("SplitBOne",), ("SplitBTwo",)},
        )

    def test_deterministic_point_cloud_compression_keeps_weight_peak_and_spatial_coverage(self):
        points = [(float(index), 0.0, 0.0) for index in range(101)]
        weights = [0.1 for _index in range(101)]
        weights[50] = 10.0
        original = cloud("LongRegion", points, weights)

        compressed = core.deterministic_point_cloud_compression(original, point_target=5)

        xs = sorted(float(point[0]) for point in compressed.points)
        self.assertEqual(len(xs), 5)
        self.assertIn(50.0, xs)
        self.assertLessEqual(xs[0], 5.0)
        self.assertGreaterEqual(xs[-1], 95.0)

    def test_bidirectional_score_rejects_one_way_containment_match(self):
        sources = (
            cloud("SmallSource", [(0.0, 0.0, 0.0), (0.0, 0.1, 0.0)], [1.0, 1.0]),
            cloud("LargeSource", [(0.0, 0.0, 0.0), (0.0, 0.1, 0.0), (0.0, 2.0, 0.0)], [1.0, 1.0, 1.0]),
        )
        targets = (
            cloud("SmallTarget", [(0.0, 0.0, 0.0), (0.0, 0.1, 0.0)], [1.0, 1.0]),
        )

        plan = core.build_assignment_plan(sources, targets)

        self.assertEqual(plan.assignments[0].source_name, "SmallSource")

    def test_visible_space_position_is_match_evidence(self):
        sources = (
            cloud("LeftSource", [(0.0, 0.0, 0.0), (0.0, 0.2, 0.0)], [1.0, 1.0]),
            cloud("RightSource", [(10.0, 0.0, 0.0), (10.0, 0.2, 0.0)], [1.0, 1.0]),
        )
        targets = (
            cloud("RightTarget", [(10.0, 0.0, 0.0), (10.0, 0.2, 0.0)], [1.0, 1.0]),
        )

        plan = core.build_assignment_plan(sources, targets)

        self.assertEqual(plan.assignments[0].source_name, "RightSource")

    def test_assignment_plan_can_reject_targets_above_score_limit(self):
        sources = (
            cloud("SourceOnly", [(0.0, 0.0, 0.0), (0.0, 0.2, 0.0)], [1.0, 1.0]),
        )
        targets = (
            cloud("FarTarget", [(10.0, 0.0, 0.0), (10.0, 0.2, 0.0)], [1.0, 1.0]),
        )

        plan = core.build_assignment_plan(sources, targets, max_score=1.0)

        self.assertEqual(plan.assignments, ())

    def test_candidate_gap_filters_candidates_without_rejecting_by_score(self):
        sources = (
            cloud("SourceOnly", [(0.0, 0.0, 0.0), (0.0, 0.2, 0.0)], [1.0, 1.0]),
        )
        targets = (
            cloud("FarTarget", [(10.0, 0.0, 0.0), (10.0, 0.2, 0.0)], [1.0, 1.0]),
        )

        broad_plan = core.build_assignment_plan(sources, targets, candidate_max_gap=20.0)
        narrow_plan = core.build_assignment_plan(sources, targets, candidate_max_gap=1.0)

        self.assertEqual(broad_plan.assignments[0].source_name, "SourceOnly")
        self.assertEqual(narrow_plan.assignments, ())

    def test_candidate_cap_keeps_nearest_centroid_when_bounds_overlap(self):
        sources = []
        for index in range(40):
            x = 0.1 + index * 0.02
            sources.append(
                cloud(
                    f"Source{index:02d}",
                    [(0.0, 0.0, 0.0), (x, 0.0, 0.0), (1.0, 0.0, 0.0)],
                    [0.1, 10.0, 0.1],
                )
            )
        target = cloud(
            "TargetLate",
            [(0.0, 0.0, 0.0), (0.1 + 39 * 0.02, 0.0, 0.0), (1.0, 0.0, 0.0)],
            [0.1, 10.0, 0.1],
        )

        plan = core.build_assignment_plan(tuple(sources), (target,), max_score=1.0)

        self.assertEqual(plan.assignments[0].source_name, "Source39")

    def test_projection_assignment_uses_source_weights_at_overlapping_target_vertices(self):
        source = source_field(
            ("Shoulder", "UpperArm"),
            [(0.0, 0.0, 0.0), (0.2, 0.0, 0.0), (1.0, 0.0, 0.0)],
            (
                ((0, 0.9), (1, 0.1)),
                ((0, 0.8), (1, 0.2)),
                ((0, 0.1), (1, 0.9)),
            ),
        )
        targets = (
            cloud("TargetShoulderPiece", [(0.0, 0.0, 0.0), (0.2, 0.0, 0.0)], [1.0, 1.0]),
            cloud("TargetArmPiece", [(1.0, 0.0, 0.0)], [1.0]),
        )

        plan = core.build_projection_assignment_plan(source, targets)

        self.assertEqual(
            [(assignment.source_name, assignment.target_names) for assignment in plan.assignments],
            [
                ("Shoulder", ("TargetShoulderPiece",)),
                ("UpperArm", ("TargetArmPiece",)),
            ],
        )

    def test_projection_assignment_keeps_target_seam_pieces_together(self):
        source = source_field(
            ("Neck", "Head"),
            [(0.0, 0.0, 1.0), (0.0, 0.0, 1.2)],
            (
                ((0, 0.85), (1, 0.15)),
                ((0, 0.2), (1, 0.8)),
            ),
        )
        targets = (
            cloud("NeckSeamA", [(0.0, 0.0, 1.0)], [1.0], seam_ids=(("mesh_a", 7),)),
            cloud("NeckSeamB", [(0.0, 0.0, 1.0)], [1.0], seam_ids=(("mesh_b", 9),)),
        )

        plan = core.build_projection_assignment_plan(source, targets)

        self.assertEqual(len(plan.assignments), 1)
        self.assertEqual(plan.assignments[0].source_name, "Neck")
        self.assertEqual(plan.assignments[0].target_names, ("NeckSeamA", "NeckSeamB"))


if __name__ == "__main__":
    unittest.main()
