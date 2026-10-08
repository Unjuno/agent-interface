import json
import unittest
from pathlib import Path

import auditor
import candidate

FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text())


class BenefitMethodTests(unittest.TestCase):
    def test_independent_reconstruction_and_assignment_denominator(self):
        raw = candidate.run(FIXTURE)
        audit = auditor.audit(FIXTURE, raw)
        self.assertEqual(audit["errors"], [])
        self.assertEqual(audit["cases"], 7)
        self.assertEqual(audit["assigned_pairs"], 13)
        self.assertEqual(audit["refused_offers_retained"], 2)
        self.assertEqual(raw["offer_assignment"], "RANDOMIZED_ASSIST_OFFER_WITHIN_MATCHED_PAIR")

    def test_planted_reversal_requires_verified_matched_support(self):
        raw = candidate.run(FIXTURE)
        byid = {c["case_id"]: c for c in raw["cases"]}
        reversal = byid["pooled_within_reversal"]
        self.assertEqual(reversal["pooled_benchmark_delta_s"], 10)
        self.assertEqual(reversal["within_person_delta_s"], -10)
        self.assertEqual(reversal["valid_matched_pair_count"], 2)
        self.assertEqual(reversal["verdict"], "REVERSAL")
        self.assertEqual(byid["under_supported"]["verdict"], "HOLD_INSUFFICIENT_SUPPORT")

    def test_same_direction_is_not_reversal(self):
        raw = candidate.run(FIXTURE)
        row = next(c for c in raw["cases"] if c["case_id"] == "same_direction")
        self.assertEqual(row["pooled_benchmark_delta_s"], -10)
        self.assertEqual(row["within_person_delta_s"], -10)
        self.assertEqual(row["verdict"], "NO_REVERSAL_SAME_DIRECTION")

    def test_wrong_missing_refused_and_changed_config_are_hold(self):
        raw = candidate.run(FIXTURE)
        byid = {c["case_id"]: c for c in raw["cases"]}
        self.assertEqual(byid["fast_wrong_effect"]["verdict"], "HOLD_OUTCOME_OR_TIME")
        self.assertEqual(byid["offer_refusal"]["verdict"], "HOLD_REFUSAL_RETAINED")
        self.assertEqual(byid["missing_outcome"]["verdict"], "HOLD_OUTCOME_OR_TIME")
        self.assertEqual(byid["changed_configuration"]["verdict"], "HOLD_CONFIG_CHANGED")

    def test_agency_remains_separate_from_time_contrast(self):
        row = next(c for c in candidate.run(FIXTURE)["cases"] if c["case_id"] == "pooled_within_reversal")
        self.assertEqual(row["agency_ratings_separate"], [4, 5])
        self.assertEqual(row["within_person_delta_s"], -10)

    def test_corruption_controls(self):
        raw = candidate.run(FIXTURE)
        mutations = (
            "omit_assigned_pair", "wrong_effect_as_verified", "refusal_as_use",
            "missing_as_zero", "erase_config_change", "pooled_only_win", "agency_as_time",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertTrue(auditor.audit(FIXTURE, auditor.corrupt(raw, mutation))["errors"])


if __name__ == "__main__":
    unittest.main()
