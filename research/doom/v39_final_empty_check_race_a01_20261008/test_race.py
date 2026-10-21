import unittest

from run_experiment import run


class FinalEmptyRaceTests(unittest.TestCase):
    def test_observation_after_empty_return_is_missed_but_not_admitted(self):
        result = run()
        self.assertEqual(result["scenario"]["drain_latest_sequence"], 11)
        self.assertFalse(result["scenario"]["drain_pending_events"])
        self.assertEqual(result["scenario"]["queued_after_return"], 1)
        self.assertTrue(result["executor"]["rejected"])
        self.assertEqual(result["executor"]["admission_or_input_events"], 0)

    def test_controller_aborts_without_retry_or_session_continuity_claim(self):
        result = run()
        self.assertEqual(result["controller"]["submit_attempts"], 1)
        self.assertEqual(result["controller"]["retry_or_accept_event_count"], 0)
        self.assertIn("SESSION_CONTINUITY_NOT_ESTABLISHED", result["decision"])


if __name__ == "__main__":
    unittest.main()
