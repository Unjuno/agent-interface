import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("5370-priority-inheritance-t5-20261001.py")
SPEC = importlib.util.spec_from_file_location("priority_inheritance_t5", MODULE_PATH)
T5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(T5)


class PriorityInheritanceT5Tests(unittest.TestCase):
    def run_case(self, name, inheritance, order):
        return T5.simulate(name, T5.CASES[name], inheritance, order)

    def test_deadline_order_distinguishes_fifo_from_edf(self):
        baseline = self.run_case("deadline_order_conflict", False, "fifo")
        fifo = self.run_case("deadline_order_conflict", True, "fifo")
        edf = self.run_case("deadline_order_conflict", True, "edf")
        self.assertEqual({"H1", "H2"}, {row["id"] for row in baseline["stale_abstentions"]})
        self.assertEqual(["H2"], [row["id"] for row in fifo["stale_abstentions"]])
        self.assertEqual([], edf["stale_abstentions"])
        self.assertEqual(["H2", "H1"], [row["id"] for row in edf["completed_before_deadline"]])

    def test_equal_deadline_tie_is_deterministic_and_fifo_compatible(self):
        fifo = self.run_case("equal_deadline_control", True, "fifo")
        edf = self.run_case("equal_deadline_control", True, "edf")
        self.assertEqual(["H1", "H2"], [row["id"] for row in fifo["completed_before_deadline"]])
        self.assertEqual(fifo["completed_before_deadline"], edf["completed_before_deadline"])

    def test_unauthenticated_urgency_cannot_inherit_or_be_admitted(self):
        forged = self.run_case("forged_urgency_control", True, "edf")
        self.assertEqual(3, forged["max_inherited_priority"])
        self.assertEqual([{"id": "H2", "reason": "UNAUTHENTICATED_URGENCY"}], forged["rejected_unauthenticated"])
        self.assertNotIn("H2", {row["id"] for row in forged["completed_before_deadline"]})

    def test_inheritance_budget_and_freshness_are_fail_closed(self):
        for name, inheritance, order in (
            ("deadline_order_conflict", False, "fifo"),
            ("deadline_order_conflict", True, "fifo"),
            ("deadline_order_conflict", True, "edf"),
            ("equal_deadline_control", True, "edf"),
        ):
            row = self.run_case(name, inheritance, order)
            self.assertLessEqual(row["inherited_owner_ticks"], T5.INHERITANCE_BUDGET)
            self.assertTrue(all(item["finish"] <= item["deadline"] for item in row["completed_before_deadline"]))
            self.assertTrue(all(item["reason"] == "STALE_ABSTAIN" for item in row["stale_abstentions"]))


if __name__ == "__main__":
    unittest.main()
