import copy
import json
import unittest
from pathlib import Path

from .audit import validate_result


HERE = Path(__file__).resolve().parent


class ObservationPumpAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        cls.events = [json.loads(line) for line in
                      (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_retained_queue_pump_reaches_monitor_before_terminal_and_cancels(self):
        self.assertTrue(validate_result(self.result, self.events, self.freeze))
        kinds = [event["event"] for event in self.events]
        self.assertLess(kinds.index("monitor_invalidated"),
                        kinds.index("executor_cancel_write"))
        self.assertLess(kinds.index("executor_cancel_write"),
                        kinds.index("planner_interrupt_transport"))
        self.assertLess(kinds.index("planner_interrupt_transport"),
                        kinds.index("terminal_dequeued"))

    def test_mutated_planner_pending_claim_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["planner_pending_at_observation"] = False
        with self.assertRaisesRegex(ValueError, "planner pending"):
            validate_result(result, self.events, self.freeze)

    def test_missing_monitor_delivery_is_rejected(self):
        events = [row for row in self.events if row["event"] != "monitor_received"]
        with self.assertRaisesRegex(ValueError, "monitor delivery"):
            validate_result(self.result, events, self.freeze)

    def test_cancel_before_invalidation_is_rejected(self):
        events = copy.deepcopy(self.events)
        first = next(i for i, row in enumerate(events)
                     if row["event"] == "monitor_invalidated")
        second = next(i for i, row in enumerate(events)
                      if row["event"] == "executor_cancel_write")
        events[first], events[second] = events[second], events[first]
        with self.assertRaisesRegex(ValueError, "event order"):
            validate_result(self.result, events, self.freeze)

    def test_nonempty_release_is_rejected(self):
        events = copy.deepcopy(self.events)
        terminal = next(row for row in events if row["event"] == "terminal_dequeued")
        terminal["release"]["keys_down"] = ["fire"]
        with self.assertRaisesRegex(ValueError, "empty release"):
            validate_result(self.result, events, self.freeze)


if __name__ == "__main__":
    unittest.main(verbosity=2)
