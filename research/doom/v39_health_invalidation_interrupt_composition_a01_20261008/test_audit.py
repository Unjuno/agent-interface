import copy
import json
import unittest
from pathlib import Path

from .audit import validate


class HealthInvalidationCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((Path(__file__).parent / "RESULT.json").read_text(encoding="utf-8"))

    def test_full_composition_and_soft_control(self):
        self.assertTrue(validate(self.result))
        self.assertFalse(self.result["cases"][0]["answer_eligible"])
        self.assertTrue(self.result["cases"][1]["answer_eligible"])

    def test_event_order_mutation_is_rejected(self):
        altered = copy.deepcopy(self.result)
        events = altered["cases"][0]["events"]
        cancel = next(row for row in events if row["event"] == "executor_cancel_write")
        interrupt = next(row for row in events if row["event"] == "planner_interrupt_transport")
        cancel_index, interrupt_index = events.index(cancel), events.index(interrupt)
        events[cancel_index], events[interrupt_index] = events[interrupt_index], events[cancel_index]
        with self.assertRaisesRegex(ValueError, "order mismatch"):
            validate(altered)

    def test_stale_answer_mutation_is_rejected(self):
        altered = copy.deepcopy(self.result)
        altered["cases"][0]["answer_eligible"] = True
        with self.assertRaisesRegex(ValueError, "was admitted"):
            validate(altered)

    def test_cancel_write_error_must_follow_empty_terminal(self):
        altered = copy.deepcopy(self.result)
        events = altered["cases"][2]["events"]
        error = next(row for row in events if row["event"] == "helper_error")
        terminal = next(row for row in events if row["event"] == "cover_terminal")
        error_index, terminal_index = events.index(error), events.index(terminal)
        events[error_index], events[terminal_index] = events[terminal_index], events[error_index]
        with self.assertRaisesRegex(ValueError, "failure must be retained"):
            validate(altered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
