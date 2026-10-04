"""Mutation tests for retained-run terminal summary/exit validation."""
import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("cleanup_audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class Tests(unittest.TestCase):
    def test_candidate_log_and_zero_exit_are_accepted(self):
        self.assertTrue(audit.terminal_run_matches(
            "Ran 21 tests in 0.001s\n\nOK\n", 21, "exit=0", passed=True))

    def test_parent_failure_log_and_nonzero_exit_are_accepted(self):
        self.assertTrue(audit.terminal_run_matches(
            "Ran 1 test in 0.001s\n\nFAILED (failures=1)\n",
            1, "exit=1", passed=False))

    def test_failure_summary_after_ok_is_rejected(self):
        self.assertFalse(audit.terminal_run_matches(
            "Ran 21 tests in 0.001s\n\nOK\nFAILED (failures=1)\n",
            21, "exit=0", passed=True))

    def test_nonzero_exit_with_ok_summary_is_rejected(self):
        self.assertFalse(audit.terminal_run_matches(
            "Ran 21 tests in 0.001s\n\nOK\n", 21, "exit=1", passed=True))

    def test_multiple_test_summaries_are_rejected(self):
        self.assertFalse(audit.terminal_run_matches(
            "Ran 21 tests in 0.001s\nOK\nRan 21 tests in 0.001s\nOK\n",
            21, "exit=0", passed=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
