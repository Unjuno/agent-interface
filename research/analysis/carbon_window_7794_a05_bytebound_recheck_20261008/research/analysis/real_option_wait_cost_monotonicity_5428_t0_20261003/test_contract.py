import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit
import candidate


class DecisionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("research/analysis/real_option_wait_cost_monotonicity_5428_t0_20261003/design.json", encoding="utf-8") as f:
            cls.design = json.load(f)
        cls.result = candidate.run(cls.design)

    def test_full_factorial_size_and_unique_rows(self):
        rows = self.result["rows"]
        self.assertEqual(len(rows), 235)
        self.assertEqual(len({row["id"] for row in rows}), 235)

    def test_wait_cost_increase_never_changes_commit_to_wait(self):
        verified = audit.audit(self.design, self.result)
        self.assertEqual(verified["wait_cost_monotonicity_violations"], 0)

    def test_lost_flexibility_increase_never_changes_wait_to_commit(self):
        verified = audit.audit(self.design, self.result)
        self.assertEqual(verified["lost_flexibility_monotonicity_violations"], 0)

    def test_hard_gates_and_unpriceable_uncertainty_hold(self):
        by_id = {row["id"]: row["decision"] for row in self.result["rows"]}
        for name in ("authority_missing", "stale_evidence", "hard_safety_block", "commit_window_closed", "uncalibrated_unpriceable"):
            self.assertEqual(by_id[name], "HOLD")

    def test_tie_deadline_and_no_route_are_explicit(self):
        by_id = {row["id"]: row["decision"] for row in self.result["rows"]}
        self.assertEqual(by_id["tie_commits"], "COMMIT")
        self.assertEqual(by_id["wait_deadline_expired_commit_still_open"], "COMMIT")
        self.assertEqual(by_id["no_alternative_wait_route"], "COMMIT")

    def test_uninformative_wait_pays_cost_but_useful_signal_can_wait(self):
        by_id = {row["id"]: row["decision"] for row in self.result["rows"]}
        self.assertEqual(by_id["no_new_information_positive_wait_cost"], "COMMIT")
        self.assertEqual(by_id["useful_information_negligible_wait_cost"], "WAIT")

    def test_auditor_rejects_mutated_decision_and_missing_row(self):
        altered = copy.deepcopy(self.result)
        altered["rows"][0]["decision"] = "WAIT" if altered["rows"][0]["decision"] != "WAIT" else "COMMIT"
        self.assertEqual(audit.audit(self.design, altered)["status"], "FAIL_AUDIT")
        altered = copy.deepcopy(self.result)
        altered["rows"].pop()
        self.assertEqual(audit.audit(self.design, altered)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
