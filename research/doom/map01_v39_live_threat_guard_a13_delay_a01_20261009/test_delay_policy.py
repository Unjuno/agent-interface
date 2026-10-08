"""Construction checks for the A13 one-shot host relay treatment."""
import unittest
from run_live import DELAY_SECONDS, DELAY_TURN_NUMBER, should_delay_completion


class DelayPolicyTests(unittest.TestCase):
    def test_only_tenth_turn_completion_is_delayed_once(self):
        self.assertEqual(DELAY_TURN_NUMBER, 10)
        self.assertEqual(DELAY_SECONDS, 1.0)
        self.assertTrue(should_delay_completion("turn/completed", 10))
        self.assertFalse(should_delay_completion("turn/completed", 9))
        self.assertFalse(should_delay_completion("turn/started", 10))
        self.assertFalse(should_delay_completion("turn/completed", 10, True))


if __name__ == "__main__":
    unittest.main()
