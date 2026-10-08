import copy
import json
import tempfile
import unittest
from pathlib import Path
from fractions import Fraction

import audit
import simulate


class AttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "raw.jsonl"
            simulate.main(str(target))
            cls.rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]

    def test_exact_coalition_tables_pass_independent_audit(self):
        result = audit.audit_records(self.rows)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["cases"], 5)
        self.assertEqual(result["feasible_arms"], 23)
        self.assertEqual(result["attempts"], 460)
        self.assertTrue(result["three_factor_rank_reversal"])
        self.assertTrue(result["infeasible_case_held"])

    def test_two_factor_nonadditivity_and_no_rank_reversal(self):
        rows = {r["case_id"]: r for r in self.rows}
        self.assertEqual(rows["additive_2f"]["interaction_2f"], "0")
        self.assertEqual(rows["positive_interaction_2f"]["interaction_2f"], "1/10")
        self.assertEqual(rows["negative_interaction_2f"]["interaction_2f"], "-1/20")
        for case_id in ("additive_2f", "positive_interaction_2f", "negative_interaction_2f"):
            row = rows[case_id]
            self.assertEqual(Fraction(row["shapley"]["A"]) - Fraction(row["shapley"]["B"]), Fraction(row["baseline_marginals"]["A"]) - Fraction(row["baseline_marginals"]["B"]))

    def test_three_factor_reversal_matches_frozen_issue_example(self):
        row = next(r for r in self.rows if r["case_id"] == "three_factor_reversal")
        self.assertEqual(row["shapley"], {"A": "3/20", "B": "11/40", "C": "1/8"})

    def test_infeasible_coalition_is_not_imputed(self):
        row = next(r for r in self.rows if r["case_id"] == "infeasible_missing_B")
        self.assertEqual(row["disposition"], "HOLD_NO_FEASIBLE_FACTORIAL")
        self.assertEqual(row["infeasible_coalitions"], ["B"])
        self.assertIsNone(row["shapley"])

    def test_auditor_rejects_swapped_factor_labels(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r["case_id"] == "positive_interaction_2f")
        next(a for a in row["arms"] if a["coalition"] == "A")["coalition"] = "B"
        self.assertTrue(audit.audit_records(rows)["errors"])

    def test_auditor_rejects_omitted_feasible_arm(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r["case_id"] == "additive_2f")
        row["arms"] = [a for a in row["arms"] if a["coalition"] != "B"]
        self.assertIn("feasible_arm_set:additive_2f", audit.audit_records(rows)["errors"])

    def test_auditor_rejects_slow_failure_relabel(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r["case_id"] == "additive_2f")
        arm = next(a for a in row["arms"] if a["coalition"] == "-")
        attempt = next(a for a in arm["attempts"] if not a["oracle_effect"])
        attempt["reported_effect"] = True
        self.assertIn("effect_oracle_mismatch:additive_2f:-", audit.audit_records(rows)["errors"])

    def test_auditor_rejects_safety_scalarization(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["safety_scalarized"] = True
        rows[0]["utility"] = "success_rate - safety_events"
        errors = audit.audit_records(rows)["errors"]
        self.assertIn("endpoint_contract:additive_2f", errors)
        self.assertIn("scalarized_endpoint_present:additive_2f", errors)

    def test_auditor_rejects_latency_cost_mutation(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["arms"][0]["attempts"][0]["latency_ms"] += 1000
        self.assertTrue(any(e.startswith("frozen_cost_endpoint:additive_2f:") for e in audit.audit_records(rows)["errors"]))


if __name__ == "__main__":
    unittest.main()
