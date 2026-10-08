"""Regression for report metrics when the loop ends on a terminal observation."""
import ast
import unittest
from collections import Counter
from pathlib import Path


SOURCE = Path(__file__).with_name("map01_overlap_controller_v39.py")


def load_report_metrics():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(item for item in tree.body
                if isinstance(item, ast.FunctionDef)
                and item.name == "terminal_safe_report_metrics")
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {"Counter": Counter}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["terminal_safe_report_metrics"]


class TerminalSafeReportMetricsTests(unittest.TestCase):
    def test_terminal_row_without_admission_is_not_counted_as_planner_turn(self):
        metrics = load_report_metrics()([
            {"iteration": 1, "model_session_id": "thread-1",
             "final_action_admission": {"status": "ADMITTED"}},
            {"iteration": 2, "terminal_observation": {"health": 0},
             "plan_terminal": "terminal_environment_observed"},
        ])
        self.assertEqual(metrics["planner_turns"], 1)
        self.assertEqual(metrics["historical_final_action_admission_statuses"],
                         {"ADMITTED": 1})

    def test_missing_admission_on_nonterminal_decision_fails_closed(self):
        with self.assertRaises(KeyError):
            load_report_metrics()([{"iteration": 1, "model_session_id": "thread-1"}])


if __name__ == "__main__":
    unittest.main()
