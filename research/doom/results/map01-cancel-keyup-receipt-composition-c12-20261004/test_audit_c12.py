"""Regression tests for the retained-failure evidence audit."""
from pathlib import Path
import unittest

import audit_c12


ROOT = Path(__file__).resolve().parent


class RetainedInitialFailureTests(unittest.TestCase):
    def test_accepts_the_recorded_publication_control_failure(self) -> None:
        initial = (ROOT / "raw/initial-combined-suite-output.txt").read_text(
            encoding="utf-8"
        )
        self.assertTrue(audit_c12.has_expected_initial_failure(initial))

    def test_rejects_an_unrelated_stop_iteration_failure(self) -> None:
        unrelated = """\
ERROR: test_unrelated_operation (candidate.OtherTests.test_unrelated_operation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_other.py", line 9, in test_unrelated_operation
    next(item for item in items if item == "missing")
StopIteration

----------------------------------------------------------------------
Ran 7 tests in 0.022s

FAILED (errors=1)
        """
        self.assertFalse(audit_c12.has_expected_initial_failure(unrelated))

    def test_rejects_expected_test_name_without_input_released_failure_context(self) -> None:
        wrong_context = """\
ERROR: test_cancelled_release_is_published_before_terminal (candidate.live_control.test_executor_owner_cancel_cause_v1.ExecutorOwnerCancelCauseTests.test_cancelled_release_is_published_before_terminal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_executor_owner_cancel_cause_v1.py", line 100, in test_cancelled_release_is_published_before_terminal
    events["missing"]
StopIteration

----------------------------------------------------------------------
Ran 7 tests in 0.022s

FAILED (errors=1)
"""
        self.assertFalse(audit_c12.has_expected_initial_failure(wrong_context))


if __name__ == "__main__":
    unittest.main()
