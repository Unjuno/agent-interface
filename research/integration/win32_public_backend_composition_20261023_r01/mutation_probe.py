"""Negative control: inject premature recovery into the inert composition only."""
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from runtime.cli_v1.test_mcp_win32_backend_composition import GuardedWin32BackendCompositionTests
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor


if __name__ == "__main__":
    original = OperationCancellationSupervisor._retire_and_recover

    def premature_recovery(self, operation_id, generation):
        deadline = time.monotonic_ns() + 5_000_000_000
        self._exchange_helper("recovery", {
            "operation_id": operation_id, "target_generation": generation,
            "recovery_id": "f" * 32, "request_id": "f" * 32,
            "deadline_ns": deadline, "obligations": ["key:CTRL"],
        }, deadline)
        original(self, operation_id, generation)

    OperationCancellationSupervisor._retire_and_recover = premature_recovery
    suite = unittest.TestSuite([GuardedWin32BackendCompositionTests(
        "test_public_caller_backend_accept_before_return")])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # An assertion failure is expected. Success or a harness error invalidates
    # the negative control; the caller checks both return code and raw output.
    sys.exit(0 if result.wasSuccessful() else 1)
