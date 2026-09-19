import unittest

from research.live_control.first_action_boundary_v1 import first_boundary


class FirstActionBoundaryTests(unittest.TestCase):
    def test_feedback_wins_when_first(self):
        rows = [{"event": "observation", "id": "a", "capture_ns": 10},
                {"event": "terminal", "id": "a", "terminal_ns": 20}]
        result = first_boundary(rows, "a")
        self.assertEqual(result["status"], "FEEDBACK")
        self.assertTrue(result["program_terminal_pending"])

    def test_terminal_short_circuits_missing_feedback(self):
        result = first_boundary([{"event": "terminal", "id": "a",
                                  "status": "needs_decision"}], "a")
        self.assertEqual(result["status"], "TERMINAL")
        self.assertFalse(result["program_terminal_pending"])
        self.assertFalse(result["grants_input_authority"])

    def test_unrelated_records_remain_pending(self):
        self.assertEqual(first_boundary([{"event": "terminal", "id": "b"}], "a")["status"],
                         "PENDING")


if __name__ == "__main__": unittest.main()
