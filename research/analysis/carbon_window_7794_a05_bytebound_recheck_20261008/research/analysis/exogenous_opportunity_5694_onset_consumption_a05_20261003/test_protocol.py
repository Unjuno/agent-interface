import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
ORACLE = json.loads((ROOT / "oracle.json").read_text(encoding="utf-8"))


class OnsetConsumptionTests(unittest.TestCase):
    def setUp(self):
        self.raw = candidate.run(FIXTURE)

    def test_phase_pair_differs_only_in_onset(self):
        cases = {c["case_id"]: c for c in FIXTURE["cases"]}
        left, right = (cases[x] for x in FIXTURE["phase_pair"])
        a, b = copy.deepcopy(left), copy.deepcopy(right)
        onset_a = a["cue_window"].pop("onset_ms")
        onset_b = b["cue_window"].pop("onset_ms")
        a.pop("case_id"); b.pop("case_id")
        self.assertEqual(a, b)
        self.assertEqual((onset_a, onset_b), (9, 11))

    def test_candidate_consumes_onset_and_reports_first_capture(self):
        rows = {r["case_id"]: r for r in self.raw["rows"]}
        self.assertEqual(rows["c01"]["first_acquisition_capture_ms"], 10)
        self.assertEqual(rows["c02"]["first_acquisition_capture_ms"], None)
        self.assertEqual(rows["c01"]["boundary"], "acquired_not_delivered")
        self.assertEqual(rows["c02"]["boundary"], "not_acquired")

    def test_changing_only_onset_crosses_the_capture_boundary(self):
        mutant = copy.deepcopy(FIXTURE)
        case = next(c for c in mutant["cases"] if c["case_id"] == "c01")
        case["cue_window"]["onset_ms"] = 11
        row = next(r for r in candidate.run(mutant)["rows"] if r["case_id"] == "c01")
        self.assertIsNone(row["first_acquisition_capture_ms"])
        self.assertEqual(row["boundary"], "not_acquired")

    def test_fixture_does_not_preencode_capture_membership_or_outcome(self):
        forbidden = {"opportunity_ids", "acquired", "boundary", "phase_label"}
        for case in FIXTURE["cases"]:
            self.assertFalse(forbidden.intersection(case))
            for capture in case.get("captures", []):
                self.assertFalse(forbidden.intersection(capture))

    def test_all_nine_case_results_match_frozen_oracle(self):
        got = {r["case_id"]: (r["boundary"], r["reason"], r["first_acquisition_capture_ms"], r["effect_receipt_id"]) for r in self.raw["rows"]}
        want = {case_id: (value["boundary"], value["reason"], value["first_acquisition_capture_ms"], value["effect_receipt_id"]) for case_id, value in ORACLE["expected"].items()}
        self.assertEqual(got, want)
        self.assertEqual(len(got), 9)

    def test_independent_auditor_reconstructs_rows_and_rejects_five_mutations(self):
        result = auditor.audit(FIXTURE, ORACLE, self.raw)
        self.assertEqual(result["result"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["rows_replayed"], 9)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["corruptions_rejected"], 5)
        self.assertTrue(all(result["corruption_controls"].values()))

    def test_auditor_rejects_a_forged_phase_capture_time(self):
        mutant = copy.deepcopy(self.raw)
        next(r for r in mutant["rows"] if r["case_id"] == "c02")["first_acquisition_capture_ms"] = 10
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, mutant)["errors"])

    def test_auditor_rejects_changed_capture_schedule(self):
        mutant = copy.deepcopy(self.raw)
        next(r for r in mutant["rows"] if r["case_id"] == "c02")["capture_times_ms"] = [10, 51]
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, mutant)["errors"])

    def test_auditor_rejects_a_forged_effect_receipt(self):
        mutant = copy.deepcopy(self.raw)
        row = next(r for r in mutant["rows"] if r["case_id"] == "c05")
        row["boundary"] = "eligible_effect"
        row["reason"] = "verified_effect"
        row["effect_receipt_id"] = "forged"
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, mutant)["errors"])

    def test_candidate_is_deterministic(self):
        self.assertEqual(candidate.run(FIXTURE), candidate.run(FIXTURE))


if __name__ == "__main__":
    unittest.main()
