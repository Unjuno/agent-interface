import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit import validate_events


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.events = [
            {"at": 0, "kind": "OFFER", "task_id": 0, "receipt_id": "a"},
            {"at": 1, "kind": "OFFER", "task_id": 1, "receipt_id": "b"},
            {"at": 2, "kind": "VERIFIED_TERMINAL", "task_id": 0, "receipt_id": "c"},
            {"at": 3, "kind": "RIGHT_CENSORED", "task_id": 1, "receipt_id": "d"},
        ]

    def test_conserves_terminal_and_censored_tasks(self):
        self.assertEqual(validate_events(self.events, [0, 1]),
                         {"offered": 2, "verified_terminal": 1,
                          "right_censored": 1, "active_at_end": 0})

    def test_rejects_duplicate_terminal_receipt(self):
        with self.assertRaisesRegex(ValueError, "duplicate receipt id"):
            validate_events(self.events + [{"at": 4, "kind": "VERIFIED_TERMINAL",
                                            "task_id": 0, "receipt_id": "c"}], [0, 1])

    def test_rejects_second_terminal_transition_with_distinct_receipt(self):
        with self.assertRaisesRegex(ValueError, "duplicate terminal/censor"):
            validate_events(self.events + [{"at": 4, "kind": "VERIFIED_TERMINAL",
                                            "task_id": 0, "receipt_id": "e"}], [0, 1])

    def test_rejects_dropped_task_disposition(self):
        with self.assertRaisesRegex(ValueError, "missing task disposition"):
            validate_events(self.events[:-1], [0, 1])

    def test_rejects_disappearing_offer(self):
        with self.assertRaisesRegex(ValueError, "offer denominator mismatch"):
            validate_events(self.events, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
