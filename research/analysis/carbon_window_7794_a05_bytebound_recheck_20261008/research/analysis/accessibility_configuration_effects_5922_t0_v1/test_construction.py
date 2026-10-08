import json
import unittest
from pathlib import Path

import candidate
import auditor

ROOT = Path(__file__).parent


class AccessibilityFixtureConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.output = candidate.run(cls.fixture)

    def row(self, case, route):
        return next(r for r in self.output["rows"] if r["case_id"] == case and r["route"] == route)

    def test_fixture_covers_all_configs_and_three_routes(self):
        self.assertEqual(8, len(self.fixture["cases"]))
        self.assertEqual(24, len(self.output["rows"]))
        self.assertEqual(3, len(self.fixture["routes"]))

    def test_benign_reflow_rebinds_but_stale_coordinate_misses(self):
        self.assertEqual("SAVED", self.row("benign-reflow", "fresh_semantic_rebind")["disposition"])
        self.assertEqual("NO_EFFECT", self.row("benign-reflow", "raw_coordinate")["disposition"])

    def test_decoy_preserves_wrong_effect_and_rebind_selects_target(self):
        raw = self.row("reflow-old-coordinate-decoy", "raw_coordinate")
        self.assertEqual("FORBIDDEN_EFFECT", raw["disposition"])
        self.assertEqual("profile.delete_account", raw["action"]["object"])
        self.assertEqual("SAVED", self.row("reflow-old-coordinate-decoy", "fresh_semantic_rebind")["disposition"])

    def test_high_contrast_does_not_break_semantic_target(self):
        self.assertEqual("NO_EFFECT", self.row("high-contrast-color-inversion", "raw_coordinate")["disposition"])
        self.assertEqual("SAVED", self.row("high-contrast-color-inversion", "fresh_semantic_rebind")["disposition"])

    def test_missing_completion_receipt_is_not_promoted_to_success(self):
        row = self.row("reduced-motion-no-status-or-receipt", "fresh_semantic_rebind")
        self.assertEqual("UNKNOWN_EFFECT", row["disposition"])
        self.assertFalse(row["verified"])

    def test_stale_tree_and_removed_function_fail_closed(self):
        self.assertEqual("UNKNOWN_STALE_EVIDENCE", self.row("stale-accessibility-tree", "fresh_semantic_rebind")["disposition"])
        self.assertEqual("UNKNOWN_APP_FUNCTION", self.row("setting-removes-task-function", "fresh_semantic_rebind")["disposition"])

    def test_independent_audit_and_corruption_controls(self):
        result = auditor.check(self.fixture, self.output)
        self.assertEqual([], result["errors"])
        self.assertEqual(3, result["raw_coordinate_harms_on_semantics_preserving_settings"])
        self.assertEqual(5, result["fresh_semantic_verified_successes"])
        self.assertEqual(3, result["fresh_semantic_unknowns_for_missing_or_invalid_evidence"])
        self.assertTrue(all(result["controls"].values()))
        self.assertTrue(all(r["action"] is None or r["action"]["released"] for r in self.output["rows"]))
        decoy = self.row("reflow-old-coordinate-decoy", "raw_coordinate")["action"]
        self.assertEqual("save-display-name-only", decoy["authority"])
        self.assertEqual("profile.delete_account", decoy["object"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
