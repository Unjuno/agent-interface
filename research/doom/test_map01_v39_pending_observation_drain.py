"""Regression for observations queued as the planner future completes."""
import queue
import unittest
from pathlib import Path

from map01_overlap_controller_v39 import drain_pending_observation_events


class Monitor:
    event_types = {"observation", "typed_observation"}

    def __init__(self, invalidate_on=None):
        self.invalidate_on = invalidate_on
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        if row["sequence"] == self.invalidate_on:
            return {"event": "policy_invalidation",
                    "reason": "health:below_hard_minimum",
                    "requires_new_decision": True}
        return None


class PendingObservationDrainTests(unittest.TestCase):
    def test_queued_hard_crossing_precedes_completed_answer(self):
        incoming = queue.Queue()
        incoming.put({"event": "typed_observation", "sequence": 12})
        incoming.put({"event": "terminal", "id": "cover-1",
                      "status": "completed",
                      "release": {"verified": True, "keys_down": [],
                                  "buttons_down": []}})
        monitor = Monitor(invalidate_on=12)

        result = drain_pending_observation_events(incoming, monitor, "cover-1")

        self.assertEqual(monitor.seen, [12])
        self.assertEqual(result["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertEqual(result["terminal"]["status"], "completed")
        self.assertTrue(incoming.empty())

    def test_soft_observation_and_terminal_preserve_completed_answer_path(self):
        incoming = queue.Queue()
        incoming.put({"event": "observation", "sequence": 20})
        incoming.put({"event": "terminal", "id": "cover-2",
                      "status": "completed"})
        monitor = Monitor()

        result = drain_pending_observation_events(incoming, monitor, "cover-2")

        self.assertEqual(result["latest"]["sequence"], 20)
        self.assertIsNone(result["invalidation"])
        self.assertEqual(result["terminal"]["id"], "cover-2")


    def test_completed_future_drain_is_wired_before_answer_read(self):
        source = Path(__file__).with_name("map01_overlap_controller_v39.py").read_text(
            encoding="utf-8")
        loop = source.index("while not future.done():")
        drain = source.index("drain_pending_observation_events(", loop)
        result = source.index("planner_result=future.result()", drain)
        discard = source.index("if invalidation is not None:", result)
        eligible = source.index("if not planner_result.answer_eligible:", discard)
        self.assertLess(loop, drain)
        self.assertLess(drain, result)
        self.assertLess(result, discard)
        self.assertLess(discard, eligible)

    def test_empty_backlog_is_nonblocking_and_returns_no_boundary(self):
        incoming = queue.Queue()
        monitor = Monitor()

        result = drain_pending_observation_events(incoming, monitor, "cover-3")

        self.assertEqual(result, {"latest": None, "terminal": None,
                                  "invalidation": None})
        self.assertEqual(monitor.seen, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
