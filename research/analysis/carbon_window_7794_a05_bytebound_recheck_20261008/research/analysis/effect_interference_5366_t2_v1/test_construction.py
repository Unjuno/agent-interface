import copy
import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text())


class ConstructionTests(unittest.TestCase):
    def test_three_policies_emit_all_case_rows(self):
        result = candidate.run(FIXTURE)
        self.assertEqual(result["row_count"], 15)
        self.assertEqual(len({(r["case_id"], r["policy"]) for r in result["rows"]}), 15)

    def test_dual_dimension_gates_only_over_budget_or_unknown(self):
        rows = [r for r in candidate.run(FIXTURE)["rows"] if r["policy"] == "semantic_plus_resource"]
        decisions = {r["case_id"]: r["decision"] for r in rows}
        self.assertEqual(decisions, {
            "fast-read": "ADMIT",
            "slow-read": "DENY_RESOURCE_DEADLINE",
            "cache-hit": "ADMIT",
            "cache-miss": "DENY_RESOURCE_DEADLINE",
            "unknown-envelope": "UNKNOWN_RESOURCE_ENVELOPE",
        })

    def test_unknown_observation_does_not_mint_admission(self):
        row = next(r for r in candidate.run(FIXTURE)["rows"] if r["case_id"] == "unknown-envelope" and r["policy"] == "semantic_plus_resource")
        self.assertFalse(row["admitted"])
        self.assertFalse(row["deadline_missed"])

    def test_semantic_only_exposes_deadline_misses(self):
        rows = [r for r in candidate.run(FIXTURE)["rows"] if r["policy"] == "semantic_only"]
        self.assertEqual(sum(r["deadline_missed"] for r in rows), 3)

    def test_independent_audit_and_mutations(self):
        raw = candidate.run(FIXTURE)
        self.assertEqual(audit.audit(FIXTURE, raw)["status"], "PASS_METHOD_SCOPED")
        mutations = []
        altered = copy.deepcopy(raw); altered["rows"][0]["admitted"] = not altered["rows"][0]["admitted"]; mutations.append(altered)
        altered = copy.deepcopy(raw); altered["rows"][0]["controller_completion_ms"] += 1; mutations.append(altered)
        altered = copy.deepcopy(raw); altered["rows"].pop(); altered["row_count"] -= 1; mutations.append(altered)
        altered = copy.deepcopy(raw); altered["rows"][0]["semantic_effect"] = "write(file)"; mutations.append(altered)
        altered = copy.deepcopy(raw); altered["rows"][-1]["decision"] = "ADMIT"; altered["rows"][-1]["admitted"] = True; mutations.append(altered)
        for broken in mutations:
            self.assertNotEqual(audit.audit(FIXTURE, broken)["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
