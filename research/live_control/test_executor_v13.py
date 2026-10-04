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
    def __init__(self, reason=None):
        self.reason = reason; self.started = threading.Event(); self.releases = 0
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
        self.releases += 1
        return {"verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": time.perf_counter_ns()}


class ExecutorV13Tests(unittest.TestCase):
    def test_release_all_baseexception_preserves_custody_in_failed_terminal(self):
        publication = {
            "schema": "release-batch-delivery-v1", "identifier": "cleanup-interrupt",
            "step": 0, "size": 1,
            "positions": [{"position": 0, "step": 0, "key": "a", "state": "unknown"}],
        }
        error = KeyboardInterrupt("release sink interrupted during cleanup")

        class CleanupInterruptedBackend(Backend):
            def execute(self, step, lease, identifier, index):
                self.started.set()

            def release_all(self):
                error.release_batch_publication = publication
                raise error

        backend = CleanupInterruptedBackend()
        events = []
        terminal_received = threading.Event()
        escaped = []
        escaped_event = threading.Event()

        def emit(event):
            events.append(event)
            if event.get("event") == "terminal":
                terminal_received.set()

        previous_hook = threading.excepthook
        threading.excepthook = lambda args: (escaped.append(args.exc_value),
                                             escaped_event.set())
        executor = Executor(backend, emit)
        try:
            executor.submit("cleanup-interrupt", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
            self.assertTrue(terminal_received.wait(1), "terminal event timeout")
            self.assertTrue(escaped_event.wait(1), "worker interruption did not propagate")
            executor.close()
        finally:
            threading.excepthook = previous_hook

        terminal = next(row for row in events if row.get("event") == "terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["error"], repr(error))
        self.assertEqual(terminal["release"]["release_batch_delivery"], publication)
        self.assertEqual(escaped, [error])
        self.assertTrue(backend.started.is_set())
        self.assertIsNone(executor.active)

    def test_release_all_unrelated_baseexception_fails_terminal_then_propagates(self):
        error = KeyboardInterrupt("unrelated release cleanup interruption")

        class InterruptedCleanupBackend(Backend):
            def execute(self, step, lease, identifier, index):
                self.started.set()

            def release_all(self):
                raise error

        backend = InterruptedCleanupBackend()
        events = []
        terminal_received = threading.Event()
        escaped = []
        escaped_event = threading.Event()

        def emit(event):
            events.append(event)
            if event.get("event") == "terminal":
                terminal_received.set()

        previous_hook = threading.excepthook
        threading.excepthook = lambda args: (escaped.append(args.exc_value),
                                             escaped_event.set())
        executor = Executor(backend, emit)
        try:
            executor.submit("unrelated-cleanup-interrupt", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
            self.assertTrue(terminal_received.wait(1), "terminal event timeout")
            self.assertTrue(escaped_event.wait(1), "worker interruption did not propagate")
            executor.close()
        finally:
            threading.excepthook = previous_hook

        terminal = next(row for row in events if row.get("event") == "terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["error"], repr(error))
        self.assertEqual(terminal["release"]["verified"], False)
        self.assertNotIn("release_batch_delivery", terminal["release"])
        self.assertEqual(escaped, [error])
        self.assertTrue(backend.started.is_set())
        self.assertIsNone(executor.active)

    def test_worker_and_cleanup_baseexceptions_preserve_both_custody_ledgers(self):
        worker_publication = {
            "status": "delivery_unknown", "identifier": "double-custody",
            "step": 0, "size": 1, "position": 0,
            "event": "input_release_transition", "key": "a",
        }
        cleanup_publication = {
            "status": "delivery_unknown", "identifier": "double-custody",
            "step": 0, "size": 1, "position": 1,
            "event": "input_release_transition", "key": "b",
        }
        worker_error = KeyboardInterrupt("worker interruption")
        cleanup_error = KeyboardInterrupt("cleanup interruption")

        class DoubleInterruptedBackend(Backend):
            def execute(self, step, lease, identifier, index):
                worker_error.release_batch_publication = worker_publication
                raise worker_error

            def release_all(self):
                cleanup_error.release_batch_publication = cleanup_publication
                raise cleanup_error

        backend = DoubleInterruptedBackend()
        events = []
        terminal_received = threading.Event()
        escaped = []
        escaped_event = threading.Event()

        def emit(event):
            events.append(event)
            if event.get("event") == "terminal":
                terminal_received.set()

        previous_hook = threading.excepthook
        threading.excepthook = lambda args: (escaped.append(args.exc_value),
                                             escaped_event.set())
        executor = Executor(backend, emit)
        try:
            executor.submit("double-custody", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
            self.assertTrue(terminal_received.wait(1), "terminal event timeout")
            self.assertTrue(escaped_event.wait(1), "worker interruption did not propagate")
            executor.close()
        finally:
            threading.excepthook = previous_hook

        terminal = next(row for row in events if row.get("event") == "terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["error"], repr(worker_error))
        self.assertEqual(terminal["release"]["release_batch_delivery"], worker_publication)
        self.assertEqual(terminal["release"]["release_batch_cleanup_delivery"], cleanup_publication)
        self.assertEqual(terminal["release"]["error"], repr(cleanup_error))
        self.assertEqual(escaped, [worker_error])
        self.assertIsNone(executor.active)

    def test_base_exception_fails_terminal_before_propagating_publication_custody(self):
        publication = {
            "status": "delivery_unknown", "identifier": "interrupt-failure",
            "step": 0, "size": 2, "position": 1,
            "confirmed_positions": [0], "not_attempted_positions": [],
            "event": "input_release_transition", "key": "b",
            "error_type": "OSError",
        }
        error = KeyboardInterrupt("process-level interruption")

        class InterruptedBackend(Backend):
            def execute(self, step, lease, identifier, index):
                error.release_batch_publication = publication
                raise error

        events = []
        escaped = []
        escaped_event = threading.Event()
        executor = Executor(InterruptedBackend(), events.append)
        previous_hook = threading.excepthook
        def capture_process_exception(args):
            escaped.append(args.exc_value)
            escaped_event.set()
        threading.excepthook = capture_process_exception
        try:
            executor.submit("interrupt-failure", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
            deadline = time.monotonic() + 1
            while not any(row.get("event") == "terminal" for row in events) and time.monotonic() < deadline:
                time.sleep(.002)
            self.assertTrue(escaped_event.wait(max(0, deadline - time.monotonic())))
            executor.close()
        finally:
            threading.excepthook = previous_hook

        terminal = next(row for row in events if row.get("event") == "terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertIn("KeyboardInterrupt", terminal["error"])
        self.assertEqual(terminal["release"]["release_batch_delivery"], publication)
        self.assertEqual(escaped, [error])

    def test_terminal_preserves_release_batch_sink_delivery_uncertainty(self):
        class PublicationFailureBackend(Backend):
            def execute(self, step, lease, identifier, index):
                error = OSError("release sink acknowledgement lost")
                error.release_batch_publication = {
                    "status": "delivery_unknown", "identifier": identifier,
                    "step": index, "size": 2, "position": 1,
                    "confirmed_positions": [0], "not_attempted_positions": [],
                    "event": "input_release_transition", "key": "b",
                    "error_type": "OSError",
                }
                raise error

        events = []
        executor = Executor(PublicationFailureBackend(), events.append)
        executor.submit("sink-failure", [{"op": "pointer_drag"}], 1,
                        time.perf_counter_ns() + 1_000_000_000)
        deadline = time.monotonic() + 1
        while not any(row.get("event") == "terminal" for row in events) and time.monotonic() < deadline:
            time.sleep(.002)
        executor.close()
        terminal = next(row for row in events if row.get("event") == "terminal")
        self.assertEqual(terminal["release"]["release_batch_delivery"], {
            "status": "delivery_unknown", "identifier": "sink-failure",
            "step": 0, "size": 2, "position": 1,
            "confirmed_positions": [0], "not_attempted_positions": [],
            "event": "input_release_transition", "key": "b",
            "error_type": "OSError",
        })

    def test_close_reentered_from_accepted_sink_prevents_worker_start(self):
        backend = Backend()
        events = []
        executor = None

        def emit(event):
            events.append(event)
            if event.get("event") == "accepted":
                executor.close()

        executor = Executor(backend, emit)
        executor.submit("reentrant-close", [{"op": "pointer_drag"}], 1,
                        time.perf_counter_ns() + 1_000_000_000)
        self.assertTrue(executor.closed)
        self.assertIsNone(executor.active)
        self.assertIsNone(executor.release_watch_stops.get("reentrant-close"))
        self.assertFalse(backend.started.is_set())
        self.assertEqual(backend.releases, 1)
        self.assertFalse(any(row.get("event") == "step_started" for row in events))
        self.assertTrue(any(row.get("event") == "terminal" and
                            row.get("status") == "cancelled" for row in events))

    def test_reentrant_close_reports_unverified_release_without_starting_worker(self):
        backend = Backend()
        backend.release_all = lambda: {"verified": False, "keys_down": ["x"]}
        events = []
        executor = None

        def emit(event):
            events.append(event)
            if event.get("event") == "accepted":
                executor.close()

        executor = Executor(backend, emit)
        executor.submit("reentrant-close-unverified", [{"op": "pointer_drag"}], 1,
                        time.perf_counter_ns() + 1_000_000_000)
        terminal = next(row for row in events if row.get("event") == "terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertFalse(terminal["release"]["verified"])
        self.assertEqual(terminal["release"]["keys_down"], ["x"])
        self.assertIsNone(executor.active)
        self.assertFalse(backend.started.is_set())

    def test_reentrant_close_terminal_delivery_unknown_stays_fail_closed(self):
        backend = Backend()
        events = []
        executor = None

        def emit(event):
            events.append(event)
            if event.get("event") == "accepted":
                try:
                    executor.close()
                except OSError:
                    pass
            elif event.get("event") == "terminal":
                raise OSError("terminal acknowledgement lost")

        executor = Executor(backend, emit)
        with self.assertRaisesRegex(RuntimeError, "delivery is unknown"):
            executor.submit("reentrant-close-terminal-error", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
        self.assertEqual(sum(row.get("event") == "terminal" for row in events), 1)
        self.assertEqual(executor.terminal_publication_errors[
            "reentrant-close-terminal-error"]["status"], "delivery_unknown")
        self.assertIsNotNone(executor.active)
        self.assertFalse(backend.started.is_set())
        with self.assertRaisesRegex(ValueError, "closed or busy"):
            executor.submit("must-stay-blocked", [{"op": "pointer_drag"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)

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
            self.assertIn("sink-error", executor.release_publication_attempted_ids)
            self.assertNotIn("sink-error", executor.published_release_ids)
        finally:
            executor.close()


if __name__ == "__main__": unittest.main()
