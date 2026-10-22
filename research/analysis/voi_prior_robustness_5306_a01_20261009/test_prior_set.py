"""Behavioral regressions for task-relative prior-set VOI labels."""
import copy
import json
from pathlib import Path
import unittest

from auditor import audit_case
from candidate import evaluate_case


CASES = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))


class PriorSetDecisionTests(unittest.TestCase):
    def setUp(self):
        self.results = {case["id"]: evaluate_case(case) for case in CASES}

    def test_point_voi_hides_a_prior_sensitive_decision(self):
        row = self.results["point-near-reversal"]
        self.assertEqual(row["point_voi"]["decision"], "STOP")
        self.assertEqual(row["point_plus_margin"]["decision"], "STOP")
        self.assertEqual(row["prior_set_decision"], "PRIOR_SENSITIVE")
        self.assertEqual(
            [item["decision"] for item in row["prior_evaluations"]],
            ["CONTINUE", "STOP", "STOP"],
        )

    def test_robust_controls_remain_decidable(self):
        self.assertEqual(self.results["robust-stop"]["prior_set_decision"], "ROBUST_STOP")
        self.assertEqual(self.results["robust-continue"]["prior_set_decision"], "ROBUST_CONTINUE")

    def test_correlated_duplicate_has_no_incremental_information_value(self):
        row = self.results["correlated-duplicate"]
        self.assertEqual(row["prior_set_decision"], "ROBUST_STOP")
        self.assertEqual([item["gross_value"] for item in row["prior_evaluations"]], ["0", "0", "0"])

    def test_deadline_and_mandatory_gates_override_positive_voi(self):
        self.assertEqual(self.results["deadline-infeasible"]["prior_set_decision"], "YIELD_CHECK_INFEASIBLE")
        self.assertEqual(self.results["mandatory-gate-incomplete"]["prior_set_decision"], "YIELD_MANDATORY_INCOMPLETE")
        self.assertEqual(self.results["deadline-infeasible"]["point_voi"]["decision"], "YIELD_CHECK_INFEASIBLE")
        self.assertEqual(self.results["mandatory-gate-incomplete"]["point_voi"]["decision"], "YIELD_MANDATORY_INCOMPLETE")

    def test_independent_auditor_rejects_omitted_reversing_prior(self):
        case = CASES[0]
        row = copy.deepcopy(self.results[case["id"]])
        row["prior_evaluations"].pop(0)
        self.assertIn("prior_evaluations_do_not_match_frozen_set", audit_case(case, row))

    def test_independent_auditor_rejects_mandatory_gate_relabel(self):
        case = CASES[-1]
        row = copy.deepcopy(self.results[case["id"]])
        row["prior_set_decision"] = "ROBUST_STOP"
        self.assertIn("mandatory_gate_was_overridden", audit_case(case, row))

    def test_independent_auditor_rejects_infeasible_check_admission(self):
        case = CASES[-2]
        row = copy.deepcopy(self.results[case["id"]])
        row["prior_set_decision"] = "ROBUST_CONTINUE"
        self.assertIn("deadline_infeasible_check_admitted", audit_case(case, row))


if __name__ == "__main__":
    unittest.main(verbosity=2)
