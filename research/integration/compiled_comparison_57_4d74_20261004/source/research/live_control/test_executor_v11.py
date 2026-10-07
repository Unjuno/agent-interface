import threading
import time
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
from executor_v3 import Cancelled as EstablishedCancelled
from executor_v11 import Executor, program_sha256


class Backend:
    sequence = 7

    def __init__(self, cancel_on_execute=False):
        self.cancel_on_execute = cancel_on_execute
        self.executed = []

    def validate(self, steps):
        if not steps or any(step.get("op") != "done" for step in steps):
            raise ValueError("invalid program")

    def execute(self, step, cancel, identifier, index):
        self.executed.append(dict(step))
        if self.cancel_on_execute:
            raise EstablishedCancelled()
        self.sequence += 1

    def release_all(self):
        return {"verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": time.perf_counter_ns()}


def execute(backend, steps):
    events = []
    ended = threading.Event()

    def emit(row):
        events.append(row)
        if row["event"] == "terminal":
            ended.set()

    executor = Executor(backend, emit)
    try:
        executor.submit("p", steps, 7, time.perf_counter_ns() + 1_000_000_000)
        if not ended.wait(1):
            raise TimeoutError("test executor did not terminate")
    finally:
        executor.close()
    return events


class ExecutorV11Tests(unittest.TestCase):
    def test_attests_validated_immutable_snapshot(self):
        backend = Backend()
        steps = [{"op": "done", "payload": {"b": 2, "a": 1}}]
        expected = program_sha256(steps)
        events = execute(backend, steps)
        accepted = next(row for row in events if row["event"] == "accepted")
        self.assertEqual(accepted["program_sha256"], expected)
        self.assertEqual(program_sha256(backend.executed), expected)
        self.assertEqual(events[-1]["status"], "completed")

    def test_established_v3_cancelled_identity_reaches_cancelled_terminal(self):
        events = execute(Backend(cancel_on_execute=True), [{"op": "done"}])
        terminal = events[-1]
        self.assertEqual(terminal["status"], "cancelled")
        self.assertIsNone(terminal["error"])
        self.assertTrue(terminal["release"]["verified"])


if __name__ == "__main__":
    unittest.main()
