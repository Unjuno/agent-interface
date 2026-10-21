import unittest

from run_experiment import run


class FinalEmptyRecoveryTests(unittest.TestCase):
    def test_late_event_is_recovered_without_reissuing_action(self):
        result = run()
        self.assertEqual(result["scenario"]["drained_latest_sequence"], 11)
        self.assertFalse(result["scenario"]["pending_events_reported"])
        self.assertEqual(result["scenario"]["late_sequence_left_queued"], 12)
        self.assertEqual(result["candidate"]["recovered_latest_sequence"], 12)
        self.assertTrue(result["candidate"][
            "controller_recovery_and_discard_wiring_verified"])
        self.assertTrue(result["candidate"]["queued_late_event_consumed"])
        self.assertFalse(result["candidate"]["stale_candidate_authority"])
        self.assertTrue(result["candidate"]["fresh_decision_required"])
        self.assertFalse(result["candidate"]["retry_or_input_emitted"])


if __name__ == "__main__":
    unittest.main()
