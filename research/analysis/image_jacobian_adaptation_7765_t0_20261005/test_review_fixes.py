"""Additive tests for the post-formal review corrections; no formal rerun."""
import unittest

from reviewed_candidate import run_trial
from reviewed_auditor import audit_rows
from runner import PROTOCOL, trial


class ReviewFixTests(unittest.TestCase):
    def test_stale_initial_observation_yields_before_act(self):
        actions = []
        observation = {"error": [4.0, 0.0], "generation": 1,
                       "target_id": "x", "fresh": False}
        result = run_trial("online_jacobian", lambda: observation,
                           lambda action: actions.append(action))
        self.assertEqual(result["status"], "yield_unbound_or_stale")
        self.assertEqual(result["corrections"], 0)
        self.assertEqual(result["rows"], [])
        self.assertEqual(actions, [])

    def test_incomplete_grid_returns_hold_without_pair_lookup(self):
        rows = [trial(seed, condition, arm)
                for condition in PROTOCOL["conditions"]
                for seed in range(30)
                for arm in PROTOCOL["arms"]]
        result = audit_rows(rows[:-1])
        self.assertEqual(result["status"], "HOLD_AUDIT_OR_OUTCOME")
        self.assertEqual(result["errors"], ["PAIR_GRID_INCOMPLETE_OR_DUPLICATE"])
        self.assertEqual(result["rows"], len(rows)-1)
        self.assertFalse(result["pair_grid_complete"])

    def test_empty_and_duplicate_grids_return_hold(self):
        for damaged in ([], [dict(condition="constant", seed=0, arm="fixed_gain")]*2):
            with self.subTest(rows=len(damaged)):
                result = audit_rows(damaged)
                self.assertEqual(result["status"], "HOLD_AUDIT_OR_OUTCOME")
                self.assertFalse(result["pair_grid_complete"])

    def test_unhashable_pair_identifier_returns_hold(self):
        result = audit_rows([{"condition": [], "seed": 0, "arm": "fixed_gain"}])
        self.assertEqual(result["status"], "HOLD_AUDIT_OR_OUTCOME")
        self.assertEqual(result["errors"], ["PAIR_GRID_INCOMPLETE_OR_DUPLICATE"])
        self.assertFalse(result["pair_grid_complete"])


if __name__ == "__main__":
    unittest.main()
