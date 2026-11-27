import unittest
from audit_recovery_censoring import analyze


def guard(iteration, sequence):
    return {"iteration": iteration,
            "policy_invalidation": {"sequence": sequence,
                                    "reason": "health:below_hard_minimum"}}


class RecoveryCensoringTests(unittest.TestCase):
    def test_fresh_recovery_within_bound_is_counted(self):
        decisions = [guard(2, 50), {"iteration": 3, "fresh_sequence_at_plan": 51}]
        result = analyze(decisions, 10)
        self.assertEqual(result["classifications"]["recovered_within_two_decisions"], 1)

    def test_final_guard_without_followup_is_right_censored(self):
        result = analyze([guard(9, 200)], 10)
        self.assertEqual(result["classifications"]["right_censored_by_episode_or_decision_cap"], 1)

    def test_full_followup_without_fresh_recovery_is_observable_miss(self):
        decisions = [guard(2, 50), {"iteration": 3, "fresh_sequence_at_plan": 50},
                     {"iteration": 4, "fresh_sequence_at_plan": 49}]
        result = analyze(decisions, 10)
        self.assertEqual(result["classifications"]["observable_recovery_missed"], 1)


if __name__ == "__main__":
    unittest.main()
