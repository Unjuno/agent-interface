import unittest
import copy

import candidate
import auditor


class SimulationTests(unittest.TestCase):
    def test_full_targets_rows_controlled_targets_transferable_strata(self):
        full = candidate.run_arm(17, "FULL")
        controlled = candidate.run_arm(17, "CONTROLLED")
        self.assertTrue(all(q["proposal"]["kind"] == "PATCH_ID" for q in full["queries"]))
        self.assertTrue(all(q["proposal"]["kind"] == "TRANSFER_STRATUM" for q in controlled["queries"]))
        self.assertGreaterEqual(controlled["fresh_correct"], full["fresh_correct"])

    def test_hard_failure_is_exactly_disclosed_and_vetoed(self):
        for arm in ("FULL", "CONTROLLED"):
            run = candidate.run_arm(1, arm)
            q = run["queries"][6]
            self.assertTrue(q["hard_failure"])
            self.assertTrue(q["exact_safety_disclosed"])
            self.assertTrue(q["veto"])
            self.assertFalse(q["accepted"])

    def test_fresh_cohort_is_not_read_until_lock(self):
        for arm in ("FULL", "CONTROLLED"):
            run = candidate.run_arm(3, arm)
            self.assertTrue(all(not q["fresh_read"] for q in run["queries"]))
            self.assertTrue(run["locked_before_fresh"])

    def test_independent_auditor_reconstructs_and_rejects_mutations(self):
        raw = {"schema": "issue8072-finite-v1", "seeds": 100,
               "arms": [candidate.run_arm(s, a) for s in range(100) for a in ("FULL", "CONTROLLED")]}
        result = auditor.audit(raw)
        self.assertEqual(result["decision"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["errors"], [])
        corrupted = copy.deepcopy(raw)
        corrupted["arms"][0]["queries"][0]["fresh_read"] = True
        corrupted["arms"][1]["queries"][6]["exact_safety_disclosed"] = False
        self.assertTrue(auditor.audit(corrupted)["errors"])


if __name__ == "__main__":
    unittest.main()
