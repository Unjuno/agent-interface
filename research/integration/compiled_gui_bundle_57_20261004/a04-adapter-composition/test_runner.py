"""Exercise caller v3 and compiled runtime through the candidate composition runner."""
import importlib.util
from pathlib import Path
import unittest

RUNNER = Path(__file__).with_name("run.py")


def load_runner():
    if not RUNNER.is_file():
        raise AssertionError("candidate adapter composition runner must exist")
    spec = importlib.util.spec_from_file_location("compiled_adapter_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError("candidate runner must be importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AdapterCompositionTests(unittest.TestCase):
    def test_effect_gated_method_runs_two_transitions_through_caller(self):
        runner = load_runner()
        record = runner.run_case("positive")
        self.assertEqual(record["result"]["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(record["compiled"][0]["completed_transitions"], 2)
        self.assertEqual(record["compiled"][0]["frontier_model_resumptions"], 0)
        self.assertEqual([transition["action_id"]
                          for transition in record["compiled"][0]["transitions"]],
                         ["action-1", "action-2"])
        self.assertEqual(record["result"]["accounting"]["attempted_calls"], 0)
        self.assertEqual(record["result"]["attempt_ledger"], [])

    def test_submit_target_change_yields_before_second_transition(self):
        runner = load_runner()
        record = runner.run_case("changed")
        self.assertEqual(record["result"]["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(record["compiled"][0]["reason"], "unknown_state")
        self.assertEqual(record["compiled"][0]["completed_transitions"], 1)
        self.assertEqual(record["result"]["accounting"]["attempted_calls"], 0)
        self.assertEqual(record["result"]["attempt_ledger"], [])


if __name__ == "__main__":
    unittest.main()
