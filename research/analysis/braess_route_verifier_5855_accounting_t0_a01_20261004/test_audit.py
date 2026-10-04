"""Construction controls for the independent #5855 event replay."""
import copy
import unittest

from audit import replay


def one_task_trace():
    return {
        "name": "fixture",
        "horizon": 2,
        "window_kind": "finite",
        "initial_pending": 0,
        "events": [
            {"tick": 0, "kind": "offer", "task_id": "t0", "event_id": "offer"},
            {"tick": 0, "kind": "start", "task_id": "t0", "attempt_id": 1, "event_id": "start"},
            {"tick": 1, "kind": "verified", "task_id": "t0", "attempt_id": 1,
             "receipt_id": "receipt", "event_id": "verified"},
            {"tick": 2, "kind": "horizon", "event_id": "horizon"},
        ],
    }


class ReplayTests(unittest.TestCase):
    def test_complete_trace_conserves_each_event(self):
        result = replay(one_task_trace())
        self.assertTrue(result["accepted"], result["errors"])
        self.assertTrue(all(s["conserved"] for s in result["ledger_snapshots"]))
        self.assertEqual(result["verified_ids"], ["t0"])

    def test_horizon_retains_unfinished_task_as_censored(self):
        trace = one_task_trace()
        trace["events"].remove(trace["events"][2])
        result = replay(trace)
        self.assertTrue(result["accepted"], result["errors"])
        self.assertEqual(result["censored_ids"], ["t0"])
        self.assertEqual(result["offered_count"], 1)
        self.assertEqual(result["verified_count"], 0)

    def test_duplicate_receipt_and_terminal_are_rejected(self):
        trace = one_task_trace()
        duplicate = copy.deepcopy(trace["events"][2])
        duplicate["tick"] = 2
        duplicate["event_id"] = "second-event"
        trace["events"].insert(3, duplicate)
        result = replay(trace)
        self.assertFalse(result["accepted"])
        self.assertIn("duplicate_receipt_id", result["errors"])
        self.assertIn("duplicate_or_unmatched_terminal", result["errors"])

    def test_unordered_or_post_horizon_event_is_rejected(self):
        trace = one_task_trace()
        trace["events"][1]["tick"] = 3
        result = replay(trace)
        self.assertFalse(result["accepted"])
        self.assertIn("event_order", result["errors"])
        self.assertIn("event_time", result["errors"])


if __name__ == "__main__":
    unittest.main()
