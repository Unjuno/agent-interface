import unittest

from research.integration.issue_3166_gate_integrity_rung2_v1.policy import (
    POLICIES, SCENARIOS, admits, context, dependency_current, gate_is_current,
)


class GateIntegrityPolicyTests(unittest.TestCase):
    def test_valid_context_admitted_by_all(self):
        prepared, current, gate = context("valid", 100_000_000_000)
        for policy in POLICIES:
            with self.subTest(policy=policy):
                self.assertTrue(admits(policy, prepared, current, gate, 100_000_000_000))

    def test_two_tier_fails_closed_for_all_invalid_contexts(self):
        for scenario in SCENARIOS[1:]:
            prepared, current, gate = context(scenario, 100_000_000_000)
            with self.subTest(scenario=scenario):
                self.assertFalse(admits("TWO_TIER_FRESH_GATE", prepared, current, gate, 100_000_000_000))

    def test_stale_dependency_keeps_live_target_and_gate_only_admits(self):
        prepared, current, gate = context("stale_dependency_version", 100_000_000_000)
        self.assertTrue(current["target_live"])
        self.assertFalse(dependency_current(prepared, current))
        self.assertTrue(gate_is_current(prepared, gate, 100_000_000_000))
        self.assertTrue(admits("GATE_ONLY", prepared, current, gate, 100_000_000_000))
        self.assertFalse(admits("TWO_TIER_FRESH_GATE", prepared, current, gate, 100_000_000_000))

    def test_each_gate_defect_is_rejected_by_gate_validators(self):
        for scenario in SCENARIOS[2:]:
            prepared, current, gate = context(scenario, 100_000_000_000)
            with self.subTest(scenario=scenario):
                self.assertFalse(gate_is_current(prepared, gate, 100_000_000_000))

    def test_policy_names_are_unique_and_matrix_is_ten_by_four(self):
        self.assertEqual(len(set(POLICIES)), 4)
        self.assertEqual(len(SCENARIOS), 10)
        self.assertEqual(len(POLICIES) * len(SCENARIOS), 40)


if __name__ == "__main__":
    unittest.main()
