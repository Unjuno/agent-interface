import threading
import time
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from executor_v13 import Executor
from executor_v3 import DecisionRequired


class Backend:
    sequence = 1
    def __init__(self, reason=None): self.reason = reason; self.started = threading.Event()
    def validate(self, steps): pass
    def execute(self, step, lease, identifier, index):
        self.started.set()
        if self.reason:
            lease.record_interruption({"event": "owner_release", "reason": self.reason,
                "verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": time.perf_counter_ns(), "valid_until_ns": lease.deadline})
            time.sleep(.04)
            raise DecisionRequired(self.reason)
        time.sleep(.01)
    def release_all(self):
        return {"verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": time.perf_counter_ns()}


class ExecutorV13Tests(unittest.TestCase):
    def run_reason(self, reason):
        events = []; backend = Backend(reason); executor = Executor(backend, events.append)
        executor.submit("p", [{"op": "pointer_drag"}], 1,
                        time.perf_counter_ns() + 1_000_000_000)
        deadline = time.monotonic() + 1
        while not any(row["event"] == "terminal" for row in events) and time.monotonic() < deadline:
            time.sleep(.002)
        executor.close()
        return events

    def test_focus_surface_and_expiry_publish_before_terminal(self):
        for reason in ("focus_changed", "surface_changed", "expired"):
            with self.subTest(reason=reason):
                events = self.run_reason(reason)
                accepted = next(row for row in events if row["event"] == "accepted")
                released = next(row for row in events if row["event"] == "input_released")
                terminal = next(row for row in events if row["event"] == "terminal")
                self.assertEqual(released["intent_token"], accepted["intent_token"])
                self.assertEqual(released["owner_release"]["reason"], reason)
                self.assertLess(events.index(released), events.index(terminal))
                self.assertFalse(released["grants_input_authority"])

    def test_normal_completion_has_no_release_interruption_event(self):
        events = self.run_reason(None)
        self.assertFalse(any(row["event"].startswith("input_release") for row in events))
        self.assertEqual(next(row for row in events if row["event"] == "terminal")["status"],
                         "completed")


if __name__ == "__main__": unittest.main()
