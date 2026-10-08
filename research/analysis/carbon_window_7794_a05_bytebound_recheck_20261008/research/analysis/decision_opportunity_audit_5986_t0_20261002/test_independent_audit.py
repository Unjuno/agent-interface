import json
import unittest
from pathlib import Path

import independent_audit as ia

ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "frozen/fixture.json").read_text())
RAW = json.loads((ROOT / "frozen/candidate.json").read_text())


class IndependentAuditTests(unittest.TestCase):
    def test_all_six_rows_reconstruct_exactly(self):
        self.assertEqual(RAW["rows"], ia.reconstruct(FIXTURE))

    def test_delivered_late_is_not_an_opportunity(self):
        row = ia.reconstruct(FIXTURE)[1]
        self.assertEqual(row["classification"], "DELIVERED_BUT_NO_DECISION_WINDOW")
        self.assertEqual(row["arrival_only"], "CAPTURE_BEFORE_DEADLINE")

    def test_undelivered_capture_is_not_decision_value(self):
        self.assertEqual(ia.reconstruct(FIXTURE)[2]["classification"], "EARLY_BUT_NOT_DELIVERED")

    def test_stale_generation_yields(self):
        self.assertEqual(ia.reconstruct(FIXTURE)[4]["classification"], "STALE_OR_MISLEADING_YIELD")

    def test_synthetic_effect_never_becomes_verified_value(self):
        self.assertEqual(ia.reconstruct(FIXTURE)[0]["simulated_effect_delta"], 1)
        self.assertTrue(all(not r["verified_value_claim"] for r in ia.reconstruct(FIXTURE)))

    def test_mandatory_safety_withholding_refused(self):
        row = ia.reconstruct(FIXTURE)[5]
        self.assertTrue(row["withholding_refused"])
        self.assertEqual(row["classification"], "MANDATORY_SAFETY_CUE_INELIGIBLE_FOR_WITHHOLDING")

    def test_original_frozen_raw_passes_new_independent_audit(self):
        result = ia.audit(FIXTURE, RAW)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["mutations_rejected"], 6)

    def test_unknown_action_is_rejected(self):
        fixture = json.loads(json.dumps(FIXTURE))
        fixture["cases"][0]["action_with_cue"] = "FORGED"
        with self.assertRaises(ValueError):
            ia.reconstruct(fixture)

    def test_counterfeit_effect_is_rejected(self):
        fixture = json.loads(json.dumps(FIXTURE))
        fixture["cases"][0]["effect_with_cue"] = False
        with self.assertRaises(ValueError):
            ia.reconstruct(fixture)


if __name__ == "__main__":
    unittest.main()
