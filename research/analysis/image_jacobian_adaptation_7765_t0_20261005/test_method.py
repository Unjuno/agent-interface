import unittest

from candidate import run_trial
from runner import PROTOCOL, trial
from auditor import audit_rows


class MethodTests(unittest.TestCase):
    def test_stale_generation_yields_after_single_action(self):
        n = 0
        def observe():
            nonlocal n
            n += 1
            return {"error": [4.0, 0.0], "generation": n, "target_id": "x", "fresh": True}
        result = run_trial("online_jacobian", observe, lambda _: {"acknowledged": True})
        self.assertEqual(result["status"], "yield_unbound_or_stale")
        self.assertEqual(result["corrections"], 1)

    def test_missing_ack_yields(self):
        obs = lambda: {"error": [4.0, 0.0], "generation": 1, "target_id": "x", "fresh": True}
        result = run_trial("online_jacobian", obs, lambda _: {"acknowledged": False})
        self.assertEqual(result["status"], "yield_unbound_or_stale")

    def test_action_respects_bound(self):
        actions = []
        error = [40.0, 30.0]
        def observe(): return {"error": list(error), "generation": 1, "target_id": "x", "fresh": True}
        def act(u):
            actions.append(u)
            error[0] -= u[0] * .9
            error[1] -= u[1] * .9
            return {"acknowledged": True}
        run_trial("fixed_gain", observe, act, max_action=3.0)
        self.assertTrue(actions)
        self.assertTrue(all((u[0]**2+u[1]**2)**.5 <= 3.0 + 1e-9 for u in actions))

    def test_independent_audit_reconstructs_pair_and_rejects_forged_transition(self):
        rows = [trial(seed, condition, arm) for condition in PROTOCOL["conditions"]
                for seed in range(30) for arm in PROTOCOL["arms"]]
        audit = audit_rows(rows)
        self.assertFalse(audit["errors"])
        changed = [dict(row) for row in rows]
        changed[0] = {**changed[0], "terminal_error": 0.0}
        self.assertTrue(audit_rows(changed)["errors"])


if __name__ == "__main__": unittest.main()
