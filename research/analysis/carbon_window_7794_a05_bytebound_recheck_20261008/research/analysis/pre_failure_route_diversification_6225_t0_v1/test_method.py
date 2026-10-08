import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent


class FiniteRouteDiversificationMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
        cls.result = candidate.run(cls.inputs)
        cls.checked = auditor.audit(cls.inputs, cls.result)

    def test_complete_session_frame_and_predeclared_allocations(self):
        self.assertEqual(len(candidate.masks(8, 2)), 28)
        self.assertEqual(len(self.result["blocks"]), self.checked["block_count"])
        self.assertEqual(self.checked["unique_sessions"], len(self.result["blocks"]))
        self.assertTrue(all(len(b["rows"]) == 8 and b["offered"] == 8 for b in self.result["blocks"]))

    def test_hidden_regime_mixture_is_within_budget_and_reduces_tail(self):
        g = self.checked["gates"]
        self.assertTrue(g["hidden_shock_tail_reduced"])
        self.assertTrue(g["hidden_mixture_within_mean_cost_budget"])

    def test_observable_and_shared_failure_negative_controls(self):
        self.assertTrue(self.checked["gates"]["observable_regime_context_policy_not_worse_than_mixture"])
        self.assertTrue(self.checked["gates"]["shared_failure_control_no_mixture_gain"])

    def test_idle_decay_and_no_eligible_fail_closed(self):
        self.assertTrue(self.checked["gates"]["idle_decay_never_claims_stale_b_ready"])
        self.assertTrue(self.checked["gates"]["no_eligible_b_never_called"])

    def test_auditor_reconstructs_and_rejects_all_mutations(self):
        self.assertEqual(self.checked["disposition"], "METHOD_PASS_SCOPED")
        self.assertTrue(all(self.checked["gates"].values()))


if __name__ == "__main__":
    unittest.main()
