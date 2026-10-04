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

    def test_cancelled_release_watcher_and_v12_terminal_barrier_share_deduplication(self):
        events = []
        release_published = threading.Event()

        class CancelBackend(Backend):
            def execute(self, step, lease, identifier, index):
                self.started.set()
                deadline = time.monotonic() + 1
                while not lease.cancel.is_set() and time.monotonic() < deadline:
                    time.sleep(.001)
                if lease.cancel.is_set():
                    lease.record_interruption({"event": "owner_release", "reason": "cancelled",
                        "verified": True, "keys_down": [], "buttons_down": [],
                        "verified_ns": time.perf_counter_ns(), "valid_until_ns": lease.deadline})
                    # Hold the worker until ExecutorV13's submit-time watcher publishes.
                    if not release_published.wait(1):
                        raise AssertionError("V13 release watcher did not publish")
                from executor_v3 import Cancelled
                raise Cancelled()

            def release_all(self):
                # The V13 watcher must publish before its inherited terminal barrier.
                if not release_published.wait(1):
                    raise AssertionError("V13 release watcher did not publish")
                return super().release_all()

        def emit(event):
            events.append(event)
            if event.get("event") == "input_released":
                release_published.set()

        backend = CancelBackend()
        executor = Executor(backend, emit)
        try:
            executor.submit("cancelled-v13", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
            self.assertTrue(backend.started.wait(1))
            self.assertTrue(executor.cancel("cancelled-v13"))
            deadline = time.monotonic() + 1
            while not any(row["event"] == "terminal" for row in events) and time.monotonic() < deadline:
                time.sleep(.002)
            self.assertTrue(any(row["event"] == "terminal" for row in events))
            releases = [row for row in events if row["event"] == "input_released"]
            terminal = next(row for row in events if row["event"] == "terminal")
            self.assertEqual(len(releases), 1)
            self.assertEqual(releases[0]["owner_release"]["reason"], "cancelled")
            self.assertEqual(terminal["status"], "cancelled")
            self.assertIn("cancelled-v13", executor.published_release_ids)
        finally:
            executor.close()

    def test_release_sink_error_is_reported_by_terminal_without_retry(self):
        events = []; attempted = threading.Event(); attempts = []; accepted = []

        class SinkErrorBackend(Backend):
            def execute(self, step, lease, identifier, index):
                self.started.set()
                lease.record_interruption({"event": "owner_release", "reason": "focus_changed",
                    "verified": True, "keys_down": [], "buttons_down": [],
                    "verified_ns": time.perf_counter_ns(), "valid_until_ns": lease.deadline})
                if not attempted.wait(1):
                    raise AssertionError("release sink was not attempted")
                raise DecisionRequired("focus_changed")

        def emit(event):
            if event.get("event") == "input_released":
                attempts.append(event)
                # Model a sink that durably accepts the event, then loses its ack.
                accepted.append(event)
                events.append(event)
                attempted.set()
                raise OSError("release acknowledgement lost")
            events.append(event)

        executor = Executor(SinkErrorBackend(), emit)
        try:
            executor.submit("sink-error", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
            deadline = time.monotonic() + 1
            while not any(row["event"] == "terminal" for row in events) and time.monotonic() < deadline:
                time.sleep(.002)
            terminal = next(row for row in events if row["event"] == "terminal")
            self.assertEqual(len(attempts), 1)
            self.assertEqual(accepted, attempts)
            self.assertEqual(terminal["input_release_publication"],
                             {"status": "delivery_unknown", "error": {
                                 "type": "OSError", "message": "release acknowledgement lost"}})
        finally:
            executor.close()


if __name__ == "__main__": unittest.main()
