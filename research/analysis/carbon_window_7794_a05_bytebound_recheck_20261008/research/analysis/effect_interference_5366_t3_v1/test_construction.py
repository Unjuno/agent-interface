import copy
import json
import unittest
from pathlib import Path

import audit
import candidate


FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text())


class EnvelopeFreshnessTests(unittest.TestCase):
    def test_three_policies_cover_all_case_rows(self):
        raw = candidate.run(FIXTURE)
        self.assertEqual(raw["row_count"], 12)
        self.assertEqual(len({(r["case_id"], r["policy"]) for r in raw["rows"]}), 12)

    def test_stale_bound_is_optimistic_without_generation_binding(self):
        raw = candidate.run(FIXTURE)
        stale_bound = next(r for r in raw["rows"] if r["case_id"] == "stale-low" and r["policy"] == "resource_bound_only")
        stale_fresh = next(r for r in raw["rows"] if r["case_id"] == "stale-low" and r["policy"] == "generation_bound_resource")
        self.assertTrue(stale_bound["admitted"])
        self.assertTrue(stale_bound["deadline_missed"])
        self.assertEqual(stale_fresh["decision"], "UNKNOWN_STALE_RESOURCE_ENVELOPE")
        self.assertFalse(stale_fresh["admitted"])

    def test_fresh_bound_preserves_safe_read_and_refuses_overbudget(self):
        rows = [r for r in candidate.run(FIXTURE)["rows"] if r["policy"] == "generation_bound_resource"]
        decisions = {r["case_id"]: r["decision"] for r in rows}
        self.assertEqual(decisions, {
            "current-low": "ADMIT",
            "stale-low": "UNKNOWN_STALE_RESOURCE_ENVELOPE",
            "current-overbudget": "DENY_RESOURCE_DEADLINE",
            "current-unknown": "UNKNOWN_RESOURCE_ENVELOPE",
        })

    def test_unknown_does_not_authorize(self):
        row = next(r for r in candidate.run(FIXTURE)["rows"] if r["case_id"] == "current-unknown" and r["policy"] == "generation_bound_resource")
        self.assertFalse(row["admitted"])
        self.assertFalse(row["deadline_missed"])

    def test_independent_audit_rejects_four_corruptions(self):
        raw = candidate.run(FIXTURE)
        self.assertEqual(audit.audit(FIXTURE, raw)["status"], "PASS_METHOD_SCOPED")
        bad = []
        x = copy.deepcopy(raw); x["rows"][5]["decision"] = "ADMIT"; x["rows"][5]["admitted"] = True; bad.append(x)
        x = copy.deepcopy(raw); del x["rows"][0]["current_generation"]; bad.append(x)
        x = copy.deepcopy(raw); x["rows"][0]["controller_completion_ms"] += 1; bad.append(x)
        x = copy.deepcopy(raw); x["rows"].pop(); x["row_count"] -= 1; bad.append(x)
        for mutated in bad:
            self.assertNotEqual(audit.audit(FIXTURE, mutated)["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
