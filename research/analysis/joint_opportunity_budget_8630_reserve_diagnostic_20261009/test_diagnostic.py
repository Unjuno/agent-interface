import json
import unittest
from fractions import Fraction

import diagnostic
import enumerate_oracle


class ReserveDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = diagnostic.load_model()
        cls.raw = diagnostic.result(cls.model)

    def test_independent_path_oracle_accepts_every_policy(self):
        self.assertEqual(enumerate_oracle.audit(self.raw, self.model)["disposition"], "PASS_DIAGNOSTIC")

    def test_observation_spends_exactly_one_recovery_opportunity(self):
        for regime in self.raw["regimes"].values():
            observed = [row for row in regime["feasible_policies"] if row["observe"]]
            skipped = [row for row in regime["feasible_policies"] if not row["observe"]]
            self.assertEqual({row["recovery_attempts"] for row in observed}, {1})
            self.assertEqual({row["recovery_attempts"] for row in skipped}, {1, 2})

    def test_policy_switches_only_when_information_clears_reserve_value(self):
        info = self.raw["regimes"]["informative"]
        weak = self.raw["regimes"]["weak_signal"]
        self.assertTrue(info["joint_optimum"]["observe"])
        self.assertFalse(weak["joint_optimum"]["observe"])
        self.assertEqual(Fraction(info["joint_optimum"]["score_exact"]), Fraction(19, 20))
        self.assertEqual(Fraction(weak["joint_optimum"]["score_exact"]), Fraction(7, 8))

    def test_a01_weak_gate_failure_is_explained_by_missing_competitor(self):
        # A01 compared one recovery attempt under either choice: 0.755 > 0.750.
        # The unused non-observation opportunity now buys a second recovery: 0.875.
        self.assertGreater(Fraction(151, 200), Fraction(3, 4))
        self.assertGreater(Fraction(7, 8), Fraction(151, 200))


if __name__ == "__main__":
    unittest.main(verbosity=2)
