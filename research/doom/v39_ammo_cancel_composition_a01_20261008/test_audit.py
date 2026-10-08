import copy
import json
import unittest
from pathlib import Path

from .audit import validate


class AmmoCancelCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((Path(__file__).parent / "RESULT.json").read_text(encoding="utf-8"))

    def test_ammo_boundary_composes_into_pending_answer_lifecycle(self):
        self.assertTrue(validate(self.result))

    def test_cancel_order_mutation_is_rejected(self):
        altered = copy.deepcopy(self.result)
        events = altered["cases"][1]["events"]
        cancel = next(row for row in events if row["event"] == "executor_cancel_write")
        interrupt = next(row for row in events if row["event"] == "planner_interrupt_transport")
        i, j = events.index(cancel), events.index(interrupt)
        events[i], events[j] = events[j], events[i]
        with self.assertRaisesRegex(ValueError, "order mismatch"):
            validate(altered)

    def test_invalidated_answer_mutation_is_rejected(self):
        altered = copy.deepcopy(self.result)
        altered["cases"][1]["answer_eligible"] = True
        with self.assertRaisesRegex(ValueError, "invalidated answer"):
            validate(altered)

    def test_cancel_failure_must_be_preserved_after_terminal(self):
        altered = copy.deepcopy(self.result)
        events = altered["cases"][2]["events"]
        failure = next(row for row in events if row["event"] == "helper_error")
        terminal = next(row for row in events if row["event"] == "cover_terminal")
        i, j = events.index(failure), events.index(terminal)
        events[i], events[j] = events[j], events[i]
        with self.assertRaisesRegex(ValueError, "failure must still interrupt"):
            validate(altered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
