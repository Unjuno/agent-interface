import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate

ROOT = Path(__file__).resolve().parent
DESIGN = json.loads((ROOT / "design.json").read_text())
INPUT = json.loads((ROOT / "candidate_input.json").read_text())


class EmittedFrontierConstructionTests(unittest.TestCase):
    def test_identical_emitted_views_remain_unknown_for_both_hidden_outcomes(self):
        raw = candidate.run(INPUT)
        rows = {row["case_id"]: row for row in raw["rows"]}
        absent = rows["emitted_ack_effect_absent"]
        committed = rows["emitted_ack_effect_committed"]
        self.assertEqual(absent["view"], committed["view"])
        self.assertEqual(absent["phase_refined"], {"status": "UNKNOWN", "retry_eligible": False})
        self.assertEqual(committed["phase_refined"], absent["phase_refined"])
        self.assertEqual(committed["phase_blind_request_bound"],
                         {"status": "CANCELLED_NO_EFFECT", "retry_eligible": True})

    def test_pre_emission_positive_control_preserves_valid_cancel(self):
        raw = candidate.run(INPUT)
        row = next(row for row in raw["rows"]
                   if row["case_id"] == "queued_cancel_positive_control")
        expected = {"status": "CANCELLED_NO_EFFECT", "retry_eligible": True}
        self.assertEqual(row["phase_refined"], expected)
        self.assertEqual(row["phase_blind_request_bound"], expected)

    def test_neutral_release_after_emission_does_not_claim_semantic_cancel(self):
        raw = candidate.run(INPUT)
        row = next(row for row in raw["rows"]
                   if row["case_id"] == "emitted_neutral_release_no_ack")
        self.assertEqual(row["phase_refined"], {"status": "UNKNOWN", "retry_eligible": False})

    def test_independent_auditor_reconstructs_and_rejects_mutations(self):
        self.assertTrue(all("actual_effect_committed" not in case
                            for case in INPUT["cases"]))
        raw = candidate.run(INPUT)
        result = auditor.audit(raw, DESIGN, INPUT)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["phase_refined_unsafe_retry_count"], 0)
        self.assertEqual(result["phase_refined_false_no_effect_count"], 0)
        self.assertGreaterEqual(result["phase_blind_unsafe_retry_count"], 1)
        self.assertEqual(result["mutation_controls"]["rejected"], 3)
        self.assertEqual(result["mutation_controls"]["total"], 3)
        mutated = copy.deepcopy(raw)
        mutated["rows"][1]["phase_refined"]["retry_eligible"] = True
        self.assertFalse(auditor.audit(mutated, DESIGN, INPUT)["valid"])


if __name__ == "__main__":
    unittest.main()
