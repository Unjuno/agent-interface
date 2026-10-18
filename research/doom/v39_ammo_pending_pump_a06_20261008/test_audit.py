import copy
import json
import unittest
from pathlib import Path

from .audit import validate_result

HERE = Path(__file__).resolve().parent


class AmmoPendingPumpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
        cls.events = [json.loads(line) for line in
                      (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_ammo_zero_dispatches_during_pending_future_and_cancels(self):
        self.assertTrue(validate_result(self.result, self.events))

    def test_pending_future_claim_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["planner_pending_at_observation"] = False
        with self.assertRaisesRegex(ValueError, "result claim mismatch"):
            validate_result(result, self.events)

    def test_wrong_signal_invalidation_is_rejected(self):
        result = copy.deepcopy(self.result)
        events = copy.deepcopy(self.events)
        row = next(row for row in events if row["event"] == "monitor_invalidated")
        row["reason"] = "health:below_hard_minimum"
        result["events"] = copy.deepcopy(events)
        with self.assertRaisesRegex(ValueError, "ammo hard-invalidation"):
            validate_result(result, events)

    def test_cancel_after_interrupt_transport_is_rejected(self):
        result = copy.deepcopy(self.result)
        events = copy.deepcopy(self.events)
        cancel = next(i for i, row in enumerate(events) if row["event"] == "executor_cancel_write")
        transport = next(i for i, row in enumerate(events) if row["event"] == "planner_interrupt_transport")
        events[cancel], events[transport] = events[transport], events[cancel]
        result["events"] = copy.deepcopy(events)
        with self.assertRaisesRegex(ValueError, "event order mismatch"):
            validate_result(result, events)

    def test_nonempty_terminal_release_is_rejected(self):
        result = copy.deepcopy(self.result)
        events = copy.deepcopy(self.events)
        row = next(row for row in events if row["event"] == "terminal_dequeued")
        row["release"]["keys_down"] = ["space"]
        result["events"] = copy.deepcopy(events)
        with self.assertRaisesRegex(ValueError, "dequeued terminal does not verify empty"):
            validate_result(result, events)


if __name__ == "__main__":
    unittest.main(verbosity=2)
