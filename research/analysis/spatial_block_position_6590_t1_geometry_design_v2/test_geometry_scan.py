from __future__ import annotations

import copy
import unittest

from auditor import audit
from geometry_scan import scan


class GeometryScanTests(unittest.TestCase):
    def test_scan_is_deterministic_and_independently_reconstructed(self):
        first = scan()
        self.assertEqual(first, scan())
        result = audit(first)
        self.assertEqual(result["decision"], "PASS_GEOMETRY_SCREEN_AUDIT")
        self.assertEqual(result["errors"], [])

    def test_smallest_feasible_candidate_is_not_assumed(self):
        result = scan()
        outcomes = [(tuple(row["tile"]), row["decision"]) for row in result["tile_candidates"]]
        feasible = [tile for tile, decision in outcomes if decision == "GEOMETRY_FEASIBLE_CANDIDATE"]
        self.assertTrue(feasible)
        self.assertEqual(feasible[0], (96, 72))
        self.assertGreaterEqual(min(result["tile_candidates"][1]["eligible_counts"].values()), 8)

    def test_selected_112_by_84_candidate_has_block_headroom(self):
        candidate = scan()["tile_candidates"][2]
        self.assertEqual(candidate["tile"], [112, 84])
        self.assertEqual(candidate["eligible_counts"], {
            "northwest": 19, "northeast": 16, "southwest": 20, "southeast": 16})
        self.assertEqual(candidate["decision"], "GEOMETRY_FEASIBLE_CANDIDATE")

    def test_auditor_rejects_site_membership_corruption(self):
        result = copy.deepcopy(scan())
        result["tile_candidates"][1]["eligible_centers_by_block"]["northwest"].pop()
        audited = audit(result)
        self.assertEqual(audited["decision"], "HOLD_AUDIT_INTEGRITY")
        self.assertIn("design_1:eligible_sites_mismatch", audited["errors"])

    def test_auditor_rejects_decision_flip(self):
        result = copy.deepcopy(scan())
        result["tile_candidates"][0]["decision"] = "GEOMETRY_FEASIBLE_CANDIDATE"
        audited = audit(result)
        self.assertEqual(audited["decision"], "HOLD_AUDIT_INTEGRITY")
        self.assertIn("design_0:decision_mismatch", audited["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
