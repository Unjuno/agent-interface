import unittest

from candidate import evaluate_episode, summarize


class PostSuccessCollateralTests(unittest.TestCase):
    def test_late_collateral_changes_long_horizon_not_first_terminal_success(self):
        episode = {
            "id": "late", "launch": 0,
            "events": [
                {"type": "verified_success", "time": 1},
                {"type": "collateral_observed", "time": 4},
                {"type": "followup_complete", "time": 6},
            ],
        }
        result = evaluate_episode(episode, [3, 6])
        self.assertEqual(result["first_terminal_type"], "verified_success")
        self.assertEqual(result["first_terminal_time"], 1)
        self.assertEqual(result["horizons"]["3"]["status"], "NO_COLLATERAL_COMPLETE")
        self.assertEqual(result["horizons"]["6"]["status"], "COLLATERAL_OBSERVED")

    def test_lost_followup_is_unknown_not_clean(self):
        episode = {
            "id": "lost", "launch": 0,
            "events": [
                {"type": "verified_success", "time": 1},
                {"type": "followup_lost", "time": 4},
            ],
        }
        result = evaluate_episode(episode, [3, 6])
        self.assertEqual(result["horizons"]["3"]["status"], "NO_COLLATERAL_COMPLETE")
        self.assertEqual(result["horizons"]["6"]["status"], "FOLLOWUP_UNKNOWN")

    def test_terminal_failure_and_safe_stop_are_not_clean_success(self):
        cohort = [
            {"id": "s", "launch": 0, "task_contract": "T", "events": [{"type": "verified_success", "time": 1}, {"type": "followup_complete", "time": 6}]},
            {"id": "f", "launch": 0, "task_contract": "T", "events": [{"type": "verified_failure", "time": 2}, {"type": "followup_complete", "time": 6}]},
            {"id": "z", "launch": 0, "task_contract": "T", "events": [{"type": "policy_safe_stop", "time": 2}, {"type": "followup_complete", "time": 6}]},
        ]
        result = summarize(cohort, [6])
        self.assertEqual(result["all_launched_n"], 3)
        self.assertEqual(result["first_terminal_counts"], {"verified_success": 1, "verified_failure": 1, "policy_safe_stop": 1})
        self.assertEqual(result["horizons"]["6"]["clean_lower_n"], 1)
        self.assertEqual(result["horizons"]["6"]["clean_upper_n"], 1)

    def test_followup_must_reach_horizon_to_be_called_clean(self):
        episode = {"id": "short", "launch": 0, "events": [
            {"type": "verified_success", "time": 1},
            {"type": "followup_complete", "time": 4},
        ]}
        result = evaluate_episode(episode, [6])
        self.assertEqual(result["horizons"]["6"]["status"], "FOLLOWUP_PENDING")

    def test_first_terminal_estimand_is_unchanged_by_post_success_events(self):
        cohort = [
            {"id": "a", "launch": 0, "task_contract": "T", "events": [{"type": "verified_success", "time": 1}, {"type": "collateral_observed", "time": 4}, {"type": "followup_complete", "time": 6}]},
            {"id": "b", "launch": 0, "task_contract": "T", "events": [{"type": "verified_success", "time": 2}, {"type": "followup_complete", "time": 6}]},
            {"id": "c", "launch": 0, "task_contract": "T", "events": [{"type": "verified_failure", "time": 2}, {"type": "followup_complete", "time": 6}]},
            {"id": "d", "launch": 0, "task_contract": "T", "events": [{"type": "policy_safe_stop", "time": 2}, {"type": "followup_complete", "time": 6}]},
        ]
        result = summarize(cohort, [3, 6])
        self.assertEqual(result["first_terminal_success_n"], 2)
        self.assertEqual(result["first_terminal_success_fraction"], 0.5)
        self.assertEqual(result["horizons"]["6"]["clean_lower_n"], 1)

    def test_rejects_mixed_task_contracts_in_one_cohort(self):
        cohort = [
            {"id": "a", "launch": 0, "task_contract": "A", "events": [{"type": "verified_success", "time": 1}]},
            {"id": "b", "launch": 0, "task_contract": "B", "events": [{"type": "verified_success", "time": 1}]},
        ]
        with self.assertRaises(ValueError):
            summarize(cohort, [2])


if __name__ == "__main__":
    unittest.main()
