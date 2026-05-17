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
    def test_assignment_plan_projects_target_vertices_to_source_weights(self):
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

        plan = core.build_assignment_plan(source, targets)

        self.assertEqual(
            [(assignment.source_name, assignment.target_names) for assignment in plan.assignments],
            [
                ("Shoulder", ("TargetShoulderPiece",)),
                ("UpperArm", ("TargetArmPiece",)),
            ],
        )

    def test_assignment_plan_uses_visible_space_nearest_source_weights(self):
        source = source_field(
            ("LeftArm", "RightArm"),
            [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)],
            (
                ((0, 1.0),),
                ((1, 1.0),),
            ),
        )
        targets = (
            cloud("VisibleRightTarget", [(10.0, 0.0, 0.0), (10.0, 0.2, 0.0)], [1.0, 0.5]),
        )

        plan = core.build_assignment_plan(source, targets)

        self.assertEqual(plan.assignments[0].source_name, "RightArm")
        self.assertEqual(plan.assignments[0].target_names, ("VisibleRightTarget",))

    def test_assignment_plan_keeps_target_seam_pieces_together(self):
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

        plan = core.build_assignment_plan(source, targets)

        self.assertEqual(len(plan.assignments), 1)
        self.assertEqual(plan.assignments[0].source_name, "Neck")
        self.assertEqual(plan.assignments[0].target_names, ("NeckSeamA", "NeckSeamB"))

    def test_assignment_plan_rejects_targets_outside_projection_distance(self):
        source = source_field(
            ("Body",),
            [(0.0, 0.0, 0.0)],
            (((0, 1.0),),),
        )
        targets = (
            cloud("FarTarget", [(10.0, 0.0, 0.0)], [1.0]),
        )

        plan = core.build_assignment_plan(source, targets, max_projection_distance=1.0)

        self.assertEqual(plan.assignments, ())

    def test_assignment_plan_can_require_clear_winner(self):
        source = source_field(
            ("Left", "Right"),
            [(0.0, 0.0, 0.0)],
            (((0, 0.51), (1, 0.49)),),
        )
        targets = (
            cloud("AmbiguousTarget", [(0.0, 0.0, 0.0)], [1.0]),
        )

        accepted = core.build_assignment_plan(source, targets, min_winner_ratio=0.5)
        rejected = core.build_assignment_plan(source, targets, min_winner_ratio=0.75)

        self.assertEqual(accepted.assignments[0].source_name, "Left")
        self.assertEqual(rejected.assignments, ())

    def test_assignment_plan_does_not_mutate_target_cloud_weights(self):
        source = source_field(
            ("Root",),
            [(0.0, 0.0, 0.0)],
            (((0, 1.0),),),
        )
        target = cloud("Target", [(0.0, 0.0, 0.0)], [0.75])
        original_weights = target.weights.copy()

        core.build_assignment_plan(source, (target,))

        np.testing.assert_array_equal(target.weights, original_weights)

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


if __name__ == "__main__":
    unittest.main()
