import unittest

from candidate import solve
from run_experiment import EQ, MISSING, PARITY, WIDE


class ApproximateAdmissionTests(unittest.TestCase):
    def test_exact_admits_both_action_classes(self):
        for action in ("reversible", "compensable", "irreversible"):
            self.assertTrue(solve(EQ, True, 0.0, action)["admitted"])

    def test_approximate_defaults_to_reversible_or_compensable_only(self):
        self.assertTrue(solve(WIDE, True, 0.5, "reversible")["admitted"])
        self.assertTrue(solve(WIDE, True, 0.5, "compensable")["admitted"])
        self.assertFalse(solve(WIDE, True, 0.5, "irreversible")["admitted"])

    def test_explicit_contract_is_the_only_approximate_irreversible_override(self):
        self.assertTrue(solve(WIDE, True, 0.5, "irreversible", True)["admitted"])

    def test_zero_tolerance_refuses_nonzero_spread(self):
        self.assertEqual(solve(WIDE, True, 0.0, "reversible")["status"], "NO_GLOBAL_SECTION")

    def test_beyond_tolerance_empty_and_incomplete_never_admit(self):
        self.assertFalse(solve(WIDE, True, 0.25, "reversible")["admitted"])
        self.assertFalse(solve(PARITY, True, 1.0, "reversible")["admitted"])
        self.assertFalse(solve(MISSING, False, 1.0, "reversible")["admitted"])


if __name__ == "__main__":
    unittest.main()
