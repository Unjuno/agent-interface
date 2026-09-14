import threading
import time
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from executor_v10 import Executor, program_sha256


class Backend:
    sequence = 7

    def __init__(self):
        self.executed = []

    def validate(self, steps):
        if not steps or any(step.get("op") != "done" for step in steps):
            raise ValueError("invalid program")

    def execute(self, step, cancel, identifier, index):
        self.executed.append(dict(step))
        self.sequence += 1

    def release_all(self):
        return {"verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": time.perf_counter_ns()}


class ExecutorV10Tests(unittest.TestCase):
    def test_acceptance_attests_validated_snapshot_before_execution(self):
        backend = Backend()
        events = []
        ended = threading.Event()

        def emit(row):
            events.append(row)
            if row["event"] == "terminal":
                ended.set()

        executor = Executor(backend, emit)
        steps = [{"op": "done", "payload": {"b": 2, "a": 1}}]
        expected = program_sha256(steps)
        try:
            executor.submit("p", steps, 7, time.perf_counter_ns() + 1_000_000_000)
            steps[0]["payload"]["a"] = 99
            self.assertTrue(ended.wait(1))
        finally:
            executor.close()
        accepted = next(row for row in events if row["event"] == "accepted")
        self.assertEqual(accepted["program_sha256"], expected)
        self.assertEqual(program_sha256(backend.executed), expected)

    def test_canonical_hash_is_key_order_independent(self):
        left = [{"op": "done", "payload": {"a": 1, "b": 2}}]
        right = [{"payload": {"b": 2, "a": 1}, "op": "done"}]
        self.assertEqual(program_sha256(left), program_sha256(right))


if __name__ == "__main__":
    unittest.main()
