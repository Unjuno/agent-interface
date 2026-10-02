import copy
import json
import unittest
from pathlib import Path

import candidate
import auditor


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
ORACLE = json.loads((ROOT / "oracle.json").read_text(encoding="utf-8"))


class MatchedPhaseTests(unittest.TestCase):
    def setUp(self):
        self.raw = candidate.run(FIXTURE)

    def test_phase_arms_match_schedule_expiry_and_horizon(self):
        cases = {x["case_id"]: x for x in FIXTURE["cases"]}
        a, b = (cases[x] for x in FIXTURE["phase_pair"])
        self.assertEqual(a["capture_schedule_ms"], b["capture_schedule_ms"])
        self.assertEqual(a["observation_horizon_ms"], b["observation_horizon_ms"])
        self.assertEqual(a["opportunity"]["expiry_ms"], b["opportunity"]["expiry_ms"])
        self.assertNotEqual(a["opportunity"]["onset_ms"], b["opportunity"]["onset_ms"])

    def test_phase_only_outcomes(self):
        rows = {x["case_id"]: x for x in self.raw["rows"]}
        self.assertEqual(rows["c01"]["boundary"], "eligible_effect")
        self.assertEqual(rows["c02"]["boundary"], "not_acquired")
        self.assertEqual(rows["c01"]["capture_schedule_ms"], rows["c02"]["capture_schedule_ms"])
        self.assertEqual(rows["c01"]["observation_horizon_ms"], rows["c02"]["observation_horizon_ms"])

    def test_all_boundaries_and_n_a(self):
        got = {r["case_id"]: r["boundary"] for r in self.raw["rows"]}
        expected = {k: v["boundary"] for k, v in ORACLE["expected"].items()}
        self.assertEqual(got, expected)
        self.assertEqual(len(got), 9)

    def test_independent_auditor_accepts_candidate_raw(self):
        result = auditor.audit(FIXTURE, ORACLE, self.raw)
        self.assertEqual(result["result"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["rows_replayed"], 9)
        self.assertEqual(result["corruptions_rejected"], 5)
        self.assertTrue(all(result["corruption_controls"].values()))

    def test_rejects_missing_row(self):
        raw = copy.deepcopy(self.raw); raw["rows"].pop()
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, raw)["errors"])

    def test_rejects_wrong_phase_classification(self):
        raw = copy.deepcopy(self.raw)
        next(r for r in raw["rows"] if r["case_id"] == "c02")["boundary"] = "eligible_effect"
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, raw)["errors"])

    def test_rejects_changed_schedule(self):
        raw = copy.deepcopy(self.raw)
        next(r for r in raw["rows"] if r["case_id"] == "c02")["capture_schedule_ms"] = [10, 55]
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, raw)["errors"])

    def test_rejects_forged_effect_receipt(self):
        raw = copy.deepcopy(self.raw)
        row = next(r for r in raw["rows"] if r["case_id"] == "c05")
        row["boundary"] = "eligible_effect"; row["reason"] = "verified_effect"; row["effect_receipt_id"] = "forged"
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, raw)["errors"])

    def test_rejects_duplicate_row(self):
        raw = copy.deepcopy(self.raw); raw["rows"].append(copy.deepcopy(raw["rows"][0]))
        self.assertTrue(auditor.audit(FIXTURE, ORACLE, raw)["errors"])


if __name__ == "__main__":
    unittest.main()
