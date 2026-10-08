import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_a16_recovery_strict import analyze as strict_analyze
from audit_recovery_censoring_frozen import analyze as frozen_analyze


def guard(iteration=2, sequence=50):
    return {"iteration": iteration,
            "policy_invalidation": {"sequence": sequence,
                                    "reason": "health:below_hard_minimum"}}


def exposed_guard(iteration=2, sequence=50):
    return {"iteration": iteration,
            "policy_invalidation": {"sequence": sequence,
                                    "outcomes": {"health": {
                                        "status": "HARD_INVALIDATED",
                                        "reason": "below_hard_minimum"}}}}


def classification(result, name):
    return result["classifications"][name]


class FrozenAuditorCounterexamples(unittest.TestCase):
    def test_missing_discarded_field_is_false_positive_in_frozen_auditor(self):
        decisions = [exposed_guard(), {"iteration": 3, "fresh_sequence_at_plan": 51}]
        self.assertEqual(classification(frozen_analyze(decisions + [{"iteration": 4, "fresh_sequence_at_plan": 52}], 10),
                                        "recovered_within_two_decisions"), 1)
        self.assertEqual(classification(strict_analyze(decisions, 10),
                                        "recovered_within_two_decisions"), 0)

    def test_null_discarded_field_is_false_positive_in_frozen_auditor(self):
        decisions = [exposed_guard(), {"iteration": 3, "fresh_sequence_at_plan": 51,
                               "model_action_discarded": None}]
        self.assertEqual(classification(frozen_analyze(decisions + [{"iteration": 4, "fresh_sequence_at_plan": 52}], 10),
                                        "recovered_within_two_decisions"), 1)
        self.assertEqual(classification(strict_analyze(decisions, 10),
                                        "recovered_within_two_decisions"), 0)

    def test_true_discarded_plan_is_not_recovery(self):
        decisions = [exposed_guard(), {"iteration": 3, "fresh_sequence_at_plan": 51,
                               "model_action_discarded": True},
                     {"iteration": 4, "fresh_sequence_at_plan": 52,
                      "model_action_discarded": True}]
        self.assertEqual(classification(strict_analyze(decisions, 10),
                                        "observable_recovery_missed"), 1)

    def test_explicit_false_and_fresh_sequence_is_recovery(self):
        decisions = [exposed_guard(), {"iteration": 3, "fresh_sequence_at_plan": 51,
                               "model_action_discarded": False}]
        self.assertEqual(classification(strict_analyze(decisions, 10),
                                        "recovered_within_two_decisions"), 1)

    def test_episode_ending_before_followup_horizon_is_censored(self):
        self.assertEqual(classification(strict_analyze([exposed_guard(9)], 10),
                                        "right_censored_by_episode_or_decision_cap"), 1)

    def test_duplicate_or_out_of_cap_iterations_fail_closed(self):
        with self.assertRaises(ValueError):
            strict_analyze([guard(2), {"iteration": 2}], 10)
        with self.assertRaises(ValueError):
            strict_analyze([guard(11)], 10)


if __name__ == "__main__":
    unittest.main()
