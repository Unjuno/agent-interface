import unittest
from scenarios import SCENARIOS
from simulator import POLICIES, run_one, safe_sequence


class SafeStateT2Tests(unittest.TestCase):
    def scenario(self, name):
        return next(s for s in SCENARIOS if s["id"] == name)

    def test_banker_witnesses_allow_truthful_safe_interleaving(self):
        row = run_one(self.scenario("safe_interleaving"), "banker")
        self.assertEqual(row["metrics"]["completed"], 3)
        self.assertEqual(row["metrics"]["unfinished"], 0)
        self.assertTrue(all(e["witness"] is not None for e in row["event_log"]
                            if e["kind"] == "grant"))

    def test_banker_avoids_quota_cycle_without_unrecovered_deadlock(self):
        s = self.scenario("truthful_cycle")
        banker = run_one(s, "banker")
        quota = run_one(s, "quota")
        self.assertEqual(banker["metrics"]["unrecovered_deadlocks"], 0)
        self.assertEqual(banker["metrics"]["completed"], 2)
        self.assertEqual(quota["metrics"]["unrecovered_deadlocks"], 1)

    def test_reactive_siphon_breaks_cycle_by_abort_and_logs_tradeoff(self):
        row = run_one(self.scenario("truthful_cycle"), "siphon")
        self.assertEqual(row["metrics"]["unrecovered_deadlocks"], 0)
        self.assertEqual(row["metrics"]["siphon_cycle_aborts"], 1)
        self.assertEqual(row["metrics"]["completed"], 1)

    def test_overclaim_can_create_banker_false_hold(self):
        row = run_one(self.scenario("overestimated_claim"), "banker")
        self.assertGreaterEqual(row["metrics"]["banker_false_holds"], 1)
        self.assertEqual(row["metrics"]["completed"], 2)

    def test_underclaim_expansion_invalidates_witness_and_releases(self):
        row = run_one(self.scenario("underestimated_claim_expansion"), "banker")
        self.assertEqual(row["metrics"]["claim_expansion_invalidations"], 1)
        self.assertEqual(row["metrics"]["unrecovered_deadlocks"], 0)
        self.assertEqual(row["allocation"]["A"], [0, 0, 0])

    def test_expiry_releases_and_unblocks_waiter(self):
        for policy in POLICIES:
            row = run_one(self.scenario("lease_expiry"), policy)
            self.assertEqual(row["metrics"]["expiries"], 1)
            self.assertEqual(row["metrics"]["completed"], 1)
            self.assertEqual(row["metrics"]["unfinished"], 0)

    def test_shared_fault_increments_generation_and_releases_affected(self):
        for policy in POLICIES:
            row = run_one(self.scenario("shared_fault_invalidation"), policy)
            self.assertEqual(row["resource_generation"][0], 1)
            self.assertEqual(row["metrics"]["shared_faults"], 1)
            self.assertEqual(row["allocation"]["A"], [0, 0, 0])

    def test_safe_sequence_rejects_cycle(self):
        available = [0, 0, 1]
        allocation = {"A": [1, 0, 0], "B": [0, 1, 0]}
        claims = {"A": [1, 1, 0], "B": [1, 1, 0]}
        status = {"A": "active", "B": "active"}
        self.assertIsNone(safe_sequence(available, allocation, claims, status))


if __name__ == "__main__":
    unittest.main()
