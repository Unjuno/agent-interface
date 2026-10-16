"""Ensure v13 cannot terminalize while release evidence publication is pending."""
import threading
import time
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import executor_v13
from executor_v3 import DecisionRequired


class GatedPublisherExecutor(executor_v13.Executor):
    def __init__(self, backend, emit):
        super().__init__(backend, emit)
        self.publisher_started = threading.Event()
        self.allow_publisher = threading.Event()

    def _publish_cause_once(self, identifier, lease, *, require_active=True):
        self.publisher_started.set()
        if not self.allow_publisher.wait(2):
            return None
        return super()._publish_cause_once(
            identifier, lease, require_active=require_active)


class Backend:
    sequence = 1

    def __init__(self):
        self.started = threading.Event()
        self.release_returned = threading.Event()

    def validate(self, _steps):
        pass

    def execute(self, _step, lease, _identifier, _index):
        self.started.set()
        lease.record_interruption({
            "event": "owner_release", "reason": "cancelled", "verified": True,
            "keys_down": [], "buttons_down": [],
            "verified_ns": time.perf_counter_ns(), "valid_until_ns": lease.deadline,
        })
        raise DecisionRequired("cancelled")

    def release_all(self):
        self.release_returned.set()
        return {"verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": time.perf_counter_ns()}


class ReleasePublicationOrderTests(unittest.TestCase):
    def test_release_publication_finishes_before_terminal(self):
        events = []
        terminal_seen = threading.Event()

        def emit(row):
            events.append(row)
            if row.get("event") == "terminal":
                terminal_seen.set()

        backend = Backend()
        executor = GatedPublisherExecutor(backend, emit)
        try:
            executor.submit("ordered", [{"op": "hold"}], 1,
                            time.perf_counter_ns() + 5_000_000_000)
            self.assertTrue(backend.started.wait(1))
            self.assertTrue(executor.publisher_started.wait(1))
            terminal_while_publisher_blocked = terminal_seen.wait(.1)

            executor.allow_publisher.set()
            worker = executor.active[2]
            worker.join(1)
            self.assertFalse(worker.is_alive())
            for watcher in executor.release_watchers:
                watcher.join(1)
                self.assertFalse(watcher.is_alive())

            self.assertFalse(terminal_while_publisher_blocked)
            released = next(row for row in events if row["event"] == "input_released")
            terminal = next(row for row in events if row["event"] == "terminal")
            self.assertEqual(released["owner_release"]["reason"], "cancelled")
            self.assertTrue(released["owner_release"]["verified"])
            self.assertLess(released["published_ns"], terminal["terminal_ns"])
            self.assertEqual(terminal["status"], "needs_decision")
        finally:
            executor.allow_publisher.set()
            executor.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
