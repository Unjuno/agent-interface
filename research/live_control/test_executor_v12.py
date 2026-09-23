import sys
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from executor_v12 import Executor


class Backend:
    sequence = 1
    def validate(self, steps): pass
    def execute(self, step, lease, identifier, index):
        self.started.set()
        while lease.interruption_snapshot() is None:
            time.sleep(.001)
        time.sleep(.08)  # artifact/finalization remains deliberately pending
        from executor_v3 import Cancelled
        raise Cancelled()
    def release_all(self):
        return {"event": "owner_release", "reason": "release", "verified": True,
                "keys_down": [], "buttons_down": [], "verified_ns": time.perf_counter_ns()}
    def __init__(self): self.started = threading.Event()


class ExecutorV12Tests(unittest.TestCase):
    def test_release_publishes_before_terminal_and_binds_intent(self):
        events, backend = [], Backend()
        executor = Executor(backend, events.append)
        executor.submit("p", [{"op": "x"}], 1, time.perf_counter_ns() + 1_000_000_000)
        backend.started.wait(1)
        accepted = next(row for row in events if row["event"] == "accepted")
        lease = executor.active[1]
        def owner():
            while not lease.cancel.is_set(): time.sleep(.001)
            lease.record_interruption({"event": "owner_release", "reason": "cancelled",
                "verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": time.perf_counter_ns(), "valid_until_ns": lease.deadline})
        threading.Thread(target=owner).start()
        executor.cancel("p")
        executor.close()
        released = next(row for row in events if row["event"] == "input_released")
        terminal = next(row for row in events if row["event"] == "terminal")
        self.assertEqual(released["intent_token"], accepted["intent_token"])
        self.assertLess(released["published_ns"], terminal["terminal_ns"])
        self.assertEqual(terminal["status"], "cancelled")
        self.assertFalse(released["grants_input_authority"])

    def test_unmatched_cancel_publishes_no_release(self):
        events, executor = [], Executor(Backend(), lambda row: events.append(row))
        self.assertFalse(executor.cancel("missing"))
        self.assertFalse(any(row["event"] == "input_released" for row in events))
        executor.close()


if __name__ == "__main__": unittest.main()
