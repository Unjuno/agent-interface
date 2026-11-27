"""Keep failure receipts tied to the lifecycle phase that actually failed."""
import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name("map01_overlap_controller_v39.py")


def stage_calls():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        owner = node.func.value
        if (node.func.attr == "set_stage" and isinstance(owner, ast.Name) and
                owner.id == "failure_cleanup" and node.args and
                isinstance(node.args[0], ast.Constant) and
                isinstance(node.args[0].value, str)):
            rows.append((node.lineno, node.args[0].value))
    return sorted(rows)


class FailureStageTests(unittest.TestCase):
    def test_stage_advances_after_source_check_through_report_write(self):
        calls = stage_calls()
        labels = [label for _, label in calls]
        expected = [
            "action_source_health_ammo",
            "planner_input_prepare",
            "planner_turn",
            "planner_result_validation",
            "action_admission",
            "action_guard_setup",
            "active_action_execution",
            "session_finish",
            "report_write",
        ]
        positions = [labels.index(label) for label in expected]
        self.assertEqual(positions, sorted(positions))

        source = SOURCE.read_text(encoding="utf-8").splitlines()
        line_for = {label: line for line, label in calls}
        find_line = lambda token: next(
            index for index, line in enumerate(source, start=1) if token in line)
        self.assertGreater(line_for["planner_input_prepare"],
                           find_line('source_ammo_signal["status"] != "observed"'))
        self.assertLess(line_for["action_source_health_ammo"],
                        find_line("source_health_signal=signal_reader.read("))
        self.assertLess(line_for["planner_turn"], find_line("planner_handle=begin_model_turn("))
        self.assertGreater(line_for["planner_result_validation"],
                           find_line("planner_result=future.result()"))
        self.assertLess(line_for["action_admission"],
                        find_line("final_action_admission=prepare_action_admission("))
        self.assertLess(line_for["action_guard_setup"],
                        find_line("running_guard=RunningActionGuardV3("))
        self.assertLess(line_for["active_action_execution"],
                        find_line("for segment_end in boundaries:"))
        self.assertLess(line_for["session_finish"], find_line('process.stdin.write(\'{"op":"finish"}'))
        self.assertLess(line_for["report_write"],
                        find_line('(args.out/"report.json").write_text('))


if __name__ == "__main__":
    unittest.main()
