import unittest

from run_experiment import run


class StaleInitialCoverRecoveryTests(unittest.TestCase):
    def test_late_hard_crossing_is_observed_before_new_plan(self):
        result = run()
        self.assertEqual(result["baseline"]["latest_sequence"], 11)
        self.assertFalse(result["baseline"]["pending_events"])
        self.assertEqual(result["candidate"]["recovered_sequence"], 12)
        self.assertEqual(result["candidate"]["late_hard_crossing_observed"],
                         "health:below_hard_minimum")
        self.assertEqual(result["candidate"]["stale_cover_disposition"],
                         "discarded_until_fresh_plan")
        self.assertTrue(result["candidate"]["queue_empty_after_recovery"])
        self.assertFalse(result["candidate"]["stale_cover_resubmitted"])


if __name__ == "__main__":
    unittest.main()
