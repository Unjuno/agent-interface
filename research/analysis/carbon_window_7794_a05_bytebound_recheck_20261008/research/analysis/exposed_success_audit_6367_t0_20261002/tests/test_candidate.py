import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import candidate


class ExposedSuccessLedgerTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))

    def test_all_assigned_offers_survive_suppression_and_shift(self):
        result = candidate.evaluate(self.load("primary.json"))
        self.assertEqual(result["denominators"], {"fixed": 8, "adaptive": 8})
        self.assertEqual(result["offers"]["suppression-01"]["adaptive"]["classification"], "VERIFIED_NON_SUCCESS")
        self.assertEqual(result["offers"]["shift-01"]["adaptive"]["classification"], "UNKNOWN_NONCOMPARABLE_CHALLENGE")

    def test_stale_cue_cannot_become_verified_adaptive_success(self):
        result = candidate.evaluate(self.load("primary.json"))
        row = result["offers"]["stale-cue-01"]["adaptive"]
        self.assertEqual(row["classification"], "INVALID_ADAPTATION_PROVENANCE")
        self.assertFalse(row["eligible_success"])

    def test_missing_effect_or_physical_occupancy_stays_unknown(self):
        result = candidate.evaluate(self.load("primary.json"))
        self.assertEqual(result["offers"]["missing-effect-01"]["adaptive"]["classification"], "UNKNOWN_EFFECT_EVIDENCE")
        self.assertEqual(result["offers"]["missing-occupancy-01"]["adaptive"]["classification"], "UNKNOWN_PHYSICAL_OCCUPANCY")

    def test_boolean_is_not_a_qualified_occupancy_timestamp(self):
        fixture = self.load("selection_trap.json")
        fixture["arms"]["adaptive"]["trap-01"]["occupancy"]["down_ms"] = True
        result = candidate.evaluate(fixture)
        self.assertEqual(result["offers"]["trap-01"]["adaptive"]["classification"], "UNKNOWN_PHYSICAL_OCCUPANCY")

    def test_verified_success_with_release_violation_fails_safety(self):
        result = candidate.evaluate(self.load("primary.json"))
        self.assertEqual(result["offers"]["unsafe-01"]["adaptive"]["classification"], "FAIL_SAFETY")
        self.assertEqual(result["decision"], "FAIL_SAFETY")

    def test_post_policy_adaptation_subset_does_not_replace_all_offer_contrast(self):
        result = candidate.evaluate(self.load("selection_trap.json"))
        expected = {"offers": 4, "verified_successes": 2, "verified_non_successes": 2, "unknowns": 0, "safety_failures": 0, "success_rate": 0.5}
        self.assertEqual(result["arms"]["fixed"], expected)
        self.assertEqual(result["arms"]["adaptive"], expected)
        self.assertEqual(result["post_policy_diagnostic"]["adaptive_triggered_successes"], 2)
        self.assertEqual(result["decision"], "NULL_ALL_OFFER_EFFECT")
        self.assertTrue(result["conditioning_warning"])

    def test_missing_assigned_arm_row_is_unknown_not_denominator_drop(self):
        fixture = self.load("selection_trap.json")
        del fixture["arms"]["adaptive"]["trap-04"]
        result = candidate.evaluate(fixture)
        self.assertEqual(result["denominators"]["adaptive"], 4)
        self.assertEqual(result["offers"]["trap-04"]["adaptive"]["classification"], "UNKNOWN_MISSING_ARM_ROW")
        self.assertEqual(result["decision"], "HOLD_INCOMPLETE_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
