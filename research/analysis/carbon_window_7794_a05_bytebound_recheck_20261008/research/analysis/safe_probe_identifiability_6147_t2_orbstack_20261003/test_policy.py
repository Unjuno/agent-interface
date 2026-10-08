import unittest

from policy import next_step


class PolicyContractTests(unittest.TestCase):
    def test_passive_policy_yields_on_action_different_alias(self):
        self.assertEqual(next_step("separable", "no_probe", [], []), "YIELD")

    def test_action_equivalent_alias_needs_no_identity_probe(self):
        self.assertEqual(
            next_step("action_equivalent", "adaptive", ["READY"], []), "ACT_COMMON"
        )

    def test_initial_alias_can_converge_to_action_equivalent_terminal_state(self):
        self.assertEqual(next_step("convergent", "adaptive", ["READY"], []), "PROBE_P")
        self.assertEqual(
            next_step("convergent", "adaptive", ["READY", "READY"], ["P"]),
            "PROBE_Q",
        )
        self.assertEqual(
            next_step("convergent", "adaptive", ["READY", "READY", "BOTH"], ["P", "Q"]),
            "ACT_COMMON",
        )
        self.assertEqual(next_step("convergent", "no_probe", ["READY"], []), "YIELD")

    def test_one_safe_probe_does_not_claim_a_distinction(self):
        self.assertEqual(next_step("separable", "one_step", ["READY"], []), "PROBE_P")
        self.assertEqual(
            next_step("separable", "one_step", ["READY", "READY"], ["P"]),
            "YIELD",
        )

    def test_adaptive_policy_uses_only_observed_current_output(self):
        self.assertEqual(
            next_step("separable", "adaptive", ["READY", "READY"], ["P"]),
            "PROBE_Q",
        )
        self.assertEqual(
            next_step("separable", "adaptive", ["READY", "READY", "LEFT"], ["P", "Q"]),
            "ACT_LEFT",
        )
        self.assertEqual(
            next_step("separable", "adaptive", ["READY", "READY", "RIGHT"], ["P", "Q"]),
            "ACT_RIGHT",
        )

    def test_nonseparation_and_expired_terminal_state_yield(self):
        self.assertEqual(
            next_step("impossible", "adaptive", ["READY", "READY", "UNKNOWN"], ["P", "Q"]),
            "YIELD",
        )
        self.assertEqual(
            next_step("stale", "adaptive", ["READY", "READY", "EXPIRED_LEFT"], ["P", "Q"]),
            "YIELD",
        )

    def test_policy_never_emits_unsafe_probe(self):
        for family in ("separable", "action_equivalent", "impossible", "stale", "convergent"):
            for arm in ("no_probe", "one_step", "adaptive"):
                self.assertNotEqual(next_step(family, arm, ["READY"], []), "PROBE_U")


if __name__ == "__main__":
    unittest.main()
