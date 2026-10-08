import unittest

from run_experiment import run


class DiscardedActionCoverReuseTests(unittest.TestCase):
    def test_discarded_remainder_is_not_reused_but_valid_cases_are(self):
        result = run()
        self.assertTrue(result["partial_stale_action"]["baseline_reuses_cover"])
        self.assertFalse(result["partial_stale_action"]["candidate_reuses_cover"])
        self.assertTrue(result["completed_action_control"]["candidate_reuses_cover"])
        self.assertTrue(result["legacy_record_control"]["candidate_reuses_cover"])


if __name__ == "__main__":
    unittest.main()
