from __future__ import annotations

import copy
import unittest

from protocol import (EVAL_CENTERS_PER_QUADRANT, QUADRANTS, design,
                      edge_margin, nearest_support_distance, validate_design)
from auditor import independent_design
from auditor import model_hash as audit_model_hash, refit as audit_refit


class T1ConstructionTests(unittest.TestCase):
    def test_frozen_geometry_is_deterministic_and_auditable(self):
        first = design()
        self.assertEqual(first, design())
        self.assertEqual(first, independent_design())
        self.assertEqual(validate_design(first), [])
        for cohort in ("position_random", "spatial_block"):
            self.assertEqual({q: len(first["cohorts"][cohort][q]) for q in QUADRANTS},
                             {q: EVAL_CENTERS_PER_QUADRANT for q in QUADRANTS})

    def test_opposite_region_transpose_matches_all_geometry_covariates(self):
        payload = design()["cohorts"]
        for cohort in ("position_random", "spatial_block"):
            for ne, sw in zip(payload[cohort]["northeast"], payload[cohort]["southwest"]):
                self.assertEqual([ne[1], ne[0]], sw)
                self.assertEqual(nearest_support_distance(tuple(ne)), nearest_support_distance(tuple(sw)))
                self.assertEqual(edge_margin(tuple(ne)), edge_margin(tuple(sw)))
                self.assertAlmostEqual(((ne[0] - 4) ** 2 + (ne[1] - 4) ** 2) ** 0.5,
                                       ((sw[0] - 4) ** 2 + (sw[1] - 4) ** 2) ** 0.5)

    def test_same_region_block_has_distance_contrast(self):
        sites = [tuple(p) for p in design()["cohorts"]["spatial_block"]["northwest"]]
        self.assertTrue(any(abs(nearest_support_distance(a) - nearest_support_distance(b)) >= 5
                            for i, a in enumerate(sites) for b in sites[i + 1:]))

    def test_corrupted_center_table_fails_closed(self):
        payload = copy.deepcopy(design())
        payload["cohorts"]["spatial_block"]["northeast"].pop()
        self.assertIn("design_reconstruction_mismatch", validate_design(payload))

    def test_candidate_and_independent_auditor_rebuild_source_rows(self):
        from protocol import make_rows
        from auditor import build_rows
        centers = [tuple(p) for p in design()["cohorts"]["position_random"]["northeast"]]
        candidate_x, candidate_y, candidate_rows = make_rows(65901001, centers, None, 64, "source-control")
        auditor_x, auditor_y, auditor_rows = build_rows(65901001, centers, None, 64, "source-control")
        self.assertEqual(candidate_x.tobytes(), auditor_x.tobytes())
        self.assertEqual(candidate_y.tobytes(), auditor_y.tobytes())
        self.assertEqual(candidate_rows, auditor_rows)

    def test_training_arms_share_paired_labels_and_negative_images(self):
        from protocol import SUPPORT, make_rows
        control_x, control_y, _ = make_rows(65902001, None, (72, 72), 80, "paired")
        treatment_x, treatment_y, _ = make_rows(65902001, list(SUPPORT), None, 80, "paired")
        self.assertEqual(control_y.tobytes(), treatment_y.tobytes())
        self.assertEqual(control_x[1::2].tobytes(), treatment_x[1::2].tobytes())
        self.assertNotEqual(control_x[0::2].tobytes(), treatment_x[0::2].tobytes())

    def test_candidate_updates_first_layer_and_matches_independent_refit(self):
        from protocol import init_model, fit, digest_model
        from protocol import make_rows
        x, y, _ = make_rows(65903001, None, (72, 72), 80, "w1-update-control")
        initial = init_model(65903002)
        candidate = fit(x, y, 65903002)
        independent = audit_refit(x, y, 65903002)
        self.assertNotEqual(candidate[0].tobytes(), initial[0].tobytes())
        self.assertEqual(digest_model(candidate), audit_model_hash(independent))
        self.assertTrue(all(a.tobytes() == b.tobytes() for a, b in zip(candidate, independent)))

    def test_centers_are_supported_and_far_cohort_is_outside_random_shell(self):
        payload = design()
        for q in QUADRANTS:
            self.assertTrue(all(nearest_support_distance(tuple(p)) >= 27
                                for p in payload["cohorts"]["spatial_block"][q]))
            self.assertTrue(all(9 <= nearest_support_distance(tuple(p)) < 27
                                for p in payload["cohorts"]["position_random"][q]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
