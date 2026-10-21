import unittest

from run_experiment import run


class InitialCoverAckBindingTests(unittest.TestCase):
    def test_recovery_uses_pre_submit_sequence_and_fresh_queued_event(self):
        result = run()
        self.assertEqual(result["baseline"]["latest_sequence"], 11)
        self.assertEqual(result["baseline"]["queued_late_sequence"], 12)
        self.assertTrue(result["candidate"]["wrapper_wired_into_main"])
        self.assertEqual(result["candidate"]["sequence_bound_before_submit"], 11)
        self.assertEqual(result["candidate"]["fresh_sequence_after_rejection"], 12)
        self.assertEqual(result["candidate"]["late_hard_crossing"],
                         "health:below_hard_minimum")
        self.assertEqual(result["candidate"]["old_cover_policy"],
                         "discarded_until_fresh_plan")
        self.assertTrue(result["candidate"]["queue_empty"])
        self.assertFalse(result["candidate"]["cover_retried"])


if __name__ == "__main__":
    unittest.main()
