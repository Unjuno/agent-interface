import copy
import json
import unittest
from pathlib import Path

import audit
import candidate

ROOT = Path(__file__).resolve().parent


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.raw = candidate.run(cls.fixture)

    def test_independent_audit_and_frozen_decision_gates(self):
        report = audit.audit(self.fixture, self.raw)
        self.assertEqual(report["disposition"], "PASS_METHOD_SCOPED", report["errors"])
        feasible = report["cases"]["feasible_tradeoff"]
        self.assertEqual(feasible["blackwell"]["verified_useful"], 12)
        self.assertEqual(feasible["independent_freeze"]["verified_useful"], 0)
        self.assertLess(feasible["scalar"]["verified_useful"],
                        feasible["blackwell"]["verified_useful"])

    def _rejected(self, mutate):
        raw = copy.deepcopy(self.raw)
        mutate(raw)
        report = audit.audit(self.fixture, raw)
        self.assertNotEqual(report["disposition"], "PASS_METHOD_SCOPED")
        self.assertTrue(report["errors"])

    def test_zero_imputation_of_missing_feedback_is_rejected(self):
        def mutate(raw):
            arm = raw["policies"]["delayed_missing_feedback"]["blackwell"]
            arm["feedback"].append({"row": 7, "route": "fast", "vector": [0.0, 0.0],
                                    "useful_verified": False, "received_tick": 12})
            arm["unknown_feedback_rows"].remove(7)
            arm["complete_feedback"] = True
        self._rejected(mutate)

    def test_hard_gate_bypass_is_rejected(self):
        def mutate(raw):
            step = raw["policies"]["feasible_tradeoff"]["blackwell"]["steps"][0]
            step["route"] = "forbidden"
            step["forecast"] = [0.0, 0.0]
            step["hard_gate_pass"] = True
        self._rejected(mutate)

    def test_false_infeasible_target_convergence_is_rejected(self):
        def mutate(raw):
            raw["policies"]["infeasible_target"]["blackwell"]["target_claim"] = "WITHIN_TARGET"
        self._rejected(mutate)

    def test_attempted_action_cannot_be_relabelled_verified(self):
        def mutate(raw):
            arm = raw["policies"]["infeasible_target"]["scalar"]
            row = next(e for e in arm["feedback"] if e["row"] == 0)
            self.assertEqual(row["route"], "conservative")
            row["useful_verified"] = True
            arm["verified_useful_count"] += 1
        self._rejected(mutate)


if __name__ == "__main__":
    unittest.main()

