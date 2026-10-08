"""Actual V39 main boundary tests; synthetic transport, no GUI or OS input."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import copy
import json
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


NEUTRAL = {"verified": True, "keys_down": [], "buttons_down": []}


class NextBoundary(RuntimeError):
    """Stop before any unrelated downstream behavior is exercised."""


class CoverTerminalTests(unittest.TestCase):
    def exercise(self, name, status, release, *, pending=True, renewed=False,
                 complete_at_terminal=False, executor_failure=False,
                 interrupt_failure=False, interrupt_request_error=False,
                 interrupt_ack_only=False, complete_during_interrupt=False,
                 abort_failure=False, abort_terminal_race=False,
                 planner_wait_cap=2):
        trace = {"case": name, "commands": [], "events": [], "timeline": []}
        started = threading.Event()
        complete = threading.Event()
        futures = []
        testcase = self
        terminal = {"event": "terminal", "status": status, "release": release,
                    "terminal_ns": 120, "error": "injected input error"}

        class Incoming(queue.Queue):
            def get(self, *args, **kwargs):
                row = super().get(*args, **kwargs)
                if row["event"] == "terminal" and pending:
                    testcase.assertTrue(started.wait(2))
                    if complete_at_terminal:
                        complete.set()
                        futures[0].result(timeout=2)
                    trace["pending_at_terminal"] = not futures[0].done()
                trace["events"].append(copy.deepcopy(row))
                trace["timeline"].append("read:" + row["event"])
                return row

        incoming = Incoming()
        incoming.put({"event": "ready", "fixture": {"loaded": True}})
        incoming.put({"event": "observation", "sequence": 1, "capture_ns": 100,
                      "image": "synthetic.png", "step": 0,
                      "pointer_binding": {"focus": 7, "surface": 7}})
        executor = None
        if executor_failure:
            from executor_v13 import Executor

            class ErrorBackend:
                sequence = 1
                def validate(self, steps): pass
                def execute(self, step, lease, identifier, index):
                    raise OSError("inert backend execute failure")
                def release_all(self): return dict(NEUTRAL)

            def emit(row):
                # Exercise the producer and consumer across JSON serialization.
                incoming.put(json.loads(json.dumps(row)))

            executor = Executor(ErrorBackend(), emit)

        class Stdin:
            def write(self, value):
                command = json.loads(value)
                trace["commands"].append(command)
                trace["timeline"].append("write:" + command["op"])
                if command["op"] == "submit":
                    count = sum(row["op"] == "submit" for row in trace["commands"])
                    if count > (2 if renewed else 1):
                        complete.set()
                        raise NextBoundary("renewal")
                    identifier = command["id"]
                    if executor is not None:
                        executor.submit(identifier, command["steps"], 1,
                                        time.perf_counter_ns() + 1_000_000_000)
                        return
                    incoming.put({"event": "accepted", "id": identifier,
                                  "accepted_ns": 105, "steps": [],
                                  "program_sha256": "synthetic", "intent_token": "test"})
                    if pending:
                        result = (dict(terminal, status="completed", release=NEUTRAL)
                                  if renewed and count == 1 else terminal)
                        incoming.put(dict(result, id=identifier))
                elif command["op"] == "cancel":
                    incoming.put(dict(terminal, id=command["id"]))
            def flush(self): pass

        process = SimpleNamespace(stdin=Stdin(), stdout=iter(()),
                                  poll=lambda: None)

        class Planner:
            thread_id = "synthetic-thread"
            def initialize(self): pass
            def start_session(self): pass
            def close(self): complete.set()
            def await_turn(self, handle, timeout):
                started.set()
                trace["planner_timeout_requested"] = timeout
                if pending and not complete.wait(min(timeout, planner_wait_cap)):
                    trace["timeline"].append("planner_wait_expired")
                    raise RuntimeError("test planner was not interrupted")
                trace["timeline"].append("planner_return")
                return SimpleNamespace(answer={"state": "active"}, usage={},
                                       handle=handle, status="completed",
                                       answer_eligible=True, cancellation_requested=False)
            def interrupt(self, handle):
                trace["timeline"].append("interrupt:" + handle.turn_id)
                if interrupt_failure:
                    raise KeyboardInterrupt("synthetic interrupt transport error")
                if interrupt_request_error:
                    return {"outcome": "request_error", "response": {"error": "synthetic"}}
                if interrupt_ack_only:
                    return {"outcome": "requested", "response": {}}
                complete.set()
                if complete_during_interrupt:
                    futures[0].result(timeout=2)
                return {"status": "interrupted"}
            def abort_pending_turn(self):
                trace["timeline"].append("abort_transport")
                complete.set()
                if abort_failure:
                    raise OSError("synthetic close fault after waiter wakeup")
                if abort_terminal_race:
                    return {"outcome": "already_terminal", "status": "completed"}
                return {"outcome": "aborted"}

        planner = Planner()

        class Pool(ThreadPoolExecutor):
            def submit(self, *args, **kwargs):
                future = super().submit(*args, **kwargs)
                futures.append(future)
                if pending:
                    testcase.assertTrue(started.wait(2))
                else:
                    future.result(timeout=2)
                return future

        class Reader:
            def __init__(self, *args, signal_id): self.signal_id = signal_id
            def read(self, observation):
                return {"format": "observable-signal-v1", "status": "observed",
                        "signal_id": self.signal_id, "value": 90,
                        "sequence": observation["sequence"],
                        "capture_ns": observation["capture_ns"],
                        "binding": observation["pointer_binding"]}

        class CleanupSpy:
            # Only verify that main reaches its existing failure handler.
            # Physical release and production cleanup are outside this fixture.
            def __init__(self, *args): self.reader = None
            def __enter__(self): return self
            def __exit__(self, kind, error, tb):
                complete.set()
                self.reader.join(timeout=2)
                trace["cleanup_error"] = type(error).__name__
            def track(self, *args): pass
            def observe_output(self, events, reader, *args): self.reader = reader
            def set_stage(self, name): trace["stage"] = name

        def final_admission(*args):
            trace["timeline"].append("final_admission")
            raise NextBoundary("final_admission")

        monitor = SimpleNamespace(event_types=set(), soft_event_count=0,
                                  latest_soft_event=None)
        with tempfile.TemporaryDirectory() as temp:
            argv = ["controller", "--out", str(Path(temp) / "out"),
                    "--iterations", "1", "--model", "synthetic", "--effort", "low",
                    "--load-fixture-manifest", str(Path(temp) / "fixture.json")]
            original_read = Path.read_text

            def read_text(path, *args, **kwargs):
                if path.name == "map01_cover_policy_schema_v6.json": return "{}"
                if path.name == "map01_motor_responder_v10.txt": return "synthetic"
                return original_read(path, *args, **kwargs)

            replacements = [
                patch.object(sys, "argv", argv),
                patch.object(controller, "CodexAppServerClient", return_value=planner),
                patch.object(controller, "PersistentPlannerAdapter", return_value=planner),
                patch.object(controller, "ThreadPoolExecutor", Pool),
                patch.object(controller.subprocess, "Popen", return_value=process),
                patch.object(controller.queue, "Queue", return_value=incoming),
                patch.object(controller, "ControllerFailureCleanup", CleanupSpy),
                patch.object(controller, "DoomStatusNumberReader", Reader),
                patch.object(controller, "refresh_source", side_effect=lambda latest, *a: (
                    latest, {"status": "already_observed"})),
                patch.object(controller, "build_cover_monitor", return_value=(
                    monitor, {"status": "admitted", "authored": None})),
                patch.object(controller, "temporal_sheet"),
                patch.object(controller, "begin_model_turn", return_value=SimpleNamespace(
                    turn_id="synthetic-turn", thread_id=planner.thread_id)),
                patch.object(controller, "final_admission_from_planner_result", final_admission),
                patch.object(controller, "win", side_effect=str),
                patch.object(Path, "read_text", read_text),
            ]
            with ExitStack() as stack:
                for replacement in replacements: stack.enter_context(replacement)
                started_ns = time.perf_counter_ns()
                try:
                    controller.main()
                except RuntimeError as error:
                    trace["error"] = {"type": type(error).__name__, "message": str(error)}
                    trace["error_notes"] = getattr(error, "__notes__", [])
                finally:
                    trace["main_elapsed_ns"] = time.perf_counter_ns() - started_ns
                    complete.set()
                    if executor is not None:
                        executor.close()
                        trace["executor_inactive"] = executor.active is None
                        trace["executor_watchers_retired"] = all(
                            not watcher.is_alive() for watcher in executor.release_watchers)
                    controller.atexit.unregister(planner.close)
        trace["all_futures_done"] = all(future.done() for future in futures)
        trace_root = os.environ.get("V39_COVER_TERMINAL_TRACE")
        if trace_root:
            destination = Path(trace_root) / (name + ".json")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x") as output:
                json.dump(trace, output, indent=2)
        return trace

    def assert_rejected(self, trace, *, pending=True, renewed=False):
        self.assertEqual(trace["error"]["type"], "RuntimeError", trace)
        self.assertIn("cover terminal", trace["error"]["message"])
        self.assertEqual(sum(row["op"] == "submit" for row in trace["commands"]),
                         2 if renewed else 1)
        self.assertNotIn("final_admission", trace["timeline"])
        self.assertEqual(trace["timeline"].count("interrupt:synthetic-turn"),
                         1 if pending else 0)
        self.assertEqual(trace["cleanup_error"], "RuntimeError")
        self.assertTrue(trace["all_futures_done"])

    def test_pending_rejects_failed_decision_and_unrequested_cancel(self):
        for status in ("failed", "needs_decision", "cancelled", "unknown"):
            with self.subTest(status=status):
                self.assert_rejected(self.exercise("pending-" + status, status, NEUTRAL))

    def test_pending_rejects_bad_release(self):
        releases = {"unverified": dict(NEUTRAL, verified=False),
                    "numeric_verified": dict(NEUTRAL, verified=1),
                    "keys": dict(NEUTRAL, keys_down=["a"]),
                    "buttons": dict(NEUTRAL, buttons_down=[1]),
                    "missing_lists": {"verified": True}, "null": None}
        for name, release in releases.items():
            with self.subTest(release=name):
                self.assert_rejected(self.exercise("pending-" + name, "completed", release))

    def test_renewed_cover_rejects_failure_before_another_submit(self):
        self.assert_rejected(self.exercise("renewed-failed", "failed", NEUTRAL,
                                           renewed=True), renewed=True)

    def test_answer_completion_race_still_checks_terminal(self):
        trace = self.exercise("completion-race", "failed", NEUTRAL,
                              complete_at_terminal=True)
        self.assertFalse(trace["pending_at_terminal"])
        self.assert_rejected(trace, pending=False)

    def test_actual_executor_failure_reaches_controller_without_renewal(self):
        trace = self.exercise("executor-failed", "failed", NEUTRAL, executor_failure=True)
        self.assert_rejected(trace)
        terminal = next(row for row in trace["events"] if row["event"] == "terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["release"], NEUTRAL)
        self.assertIn("inert backend execute failure", terminal["error"])
        self.assertTrue(trace["executor_inactive"])
        self.assertTrue(trace["executor_watchers_retired"])

    def test_interrupt_transport_error_keeps_terminal_failure_primary(self):
        trace = self.exercise("interrupt-error", "failed", NEUTRAL,
                              interrupt_request_error=True, planner_wait_cap=0.15)
        self.assert_rejected(trace)
        self.assertIn("injected input error", trace["error"]["message"])
        self.assertEqual(trace["error_notes"], [
            "planner interrupt transport failed",
            "pending planner turn transport aborted"])
        self.assertEqual(trace["planner_timeout_requested"], 90)
        self.assertIn("abort_transport", trace["timeline"])
        self.assertLess(trace["main_elapsed_ns"], 100_000_000)

    def test_interrupt_exception_aborts_pending_transport_and_keeps_failure_primary(self):
        trace = self.exercise("interrupt-exception", "failed", NEUTRAL,
                              interrupt_failure=True, planner_wait_cap=0.15)
        self.assert_rejected(trace)
        self.assertIn("injected input error", trace["error"]["message"])
        self.assertEqual(trace["error_notes"], ["planner interrupt failed: KeyboardInterrupt",
                                               "pending planner turn transport aborted"])
        self.assertIn("abort_transport", trace["timeline"])
        self.assertLess(trace["main_elapsed_ns"], 100_000_000)

    def test_post_answer_cancel_rejects_bad_terminal(self):
        cases = {"failed": ("failed", NEUTRAL), "decision": ("needs_decision", NEUTRAL),
                 "unknown": ("unknown", NEUTRAL),
                 "unverified": ("cancelled", dict(NEUTRAL, verified=False)),
                 "keys": ("completed", dict(NEUTRAL, keys_down=["a"])),
                 "buttons": ("expired", dict(NEUTRAL, buttons_down=[1])),
                 "null": ("cancelled", None)}
        for name, (status, release) in cases.items():
            with self.subTest(case=name):
                self.assert_rejected(self.exercise("post-answer-" + name, status, release,
                                                   pending=False), pending=False)

    def test_interrupt_ack_without_completion_reaches_cleanup_without_planner_timeout(self):
        trace = self.exercise("interrupt-ack-only", "failed", NEUTRAL,
                              interrupt_ack_only=True, planner_wait_cap=0.15)
        self.assert_rejected(trace)
        self.assertEqual(trace["planner_timeout_requested"], 90)
        self.assertNotIn("planner_wait_expired", trace["timeline"])
        self.assertLess(trace["timeline"].index("abort_transport"),
                        trace["timeline"].index("planner_return"))
        self.assertIn("pending planner turn transport aborted", trace["error_notes"])

    def test_completion_during_interrupt_needs_no_transport_abort(self):
        trace = self.exercise("interrupt-ack-complete", "failed", NEUTRAL,
                              complete_during_interrupt=True)
        self.assert_rejected(trace)
        self.assertNotIn("abort_transport", trace["timeline"])
        self.assertNotIn("planner_wait_expired", trace["timeline"])

    def test_abort_fault_after_ack_keeps_original_terminal_failure(self):
        trace = self.exercise("interrupt-ack-abort-fault", "failed", NEUTRAL,
                              interrupt_ack_only=True, abort_failure=True,
                              planner_wait_cap=0.15)
        self.assert_rejected(trace)
        self.assertIn("injected input error", trace["error"]["message"])
        self.assertNotIn("planner_wait_expired", trace["timeline"])
        self.assertEqual(trace["error_notes"], ["planner transport abort failed: OSError"])

    def test_completion_racing_abort_does_not_claim_transport_closed(self):
        trace = self.exercise("interrupt-abort-terminal-race", "failed", NEUTRAL,
                              interrupt_ack_only=True, abort_terminal_race=True,
                              planner_wait_cap=0.15)
        self.assert_rejected(trace)
        self.assertNotIn("planner_wait_expired", trace["timeline"])
        self.assertNotIn("pending planner turn transport aborted", trace["error_notes"])

    def test_neutral_natural_terminals_keep_renewal(self):
        for status in ("completed", "expired"):
            with self.subTest(status=status):
                trace = self.exercise("allowed-pending-" + status, status, NEUTRAL)
                self.assertEqual(trace["error"], {"type": "NextBoundary", "message": "renewal"})
                self.assertEqual(len(trace["commands"]), 2)
                self.assertNotIn("interrupt:synthetic-turn", trace["timeline"])

    def test_neutral_cancellation_races_keep_final_admission(self):
        for status in ("completed", "expired", "cancelled"):
            with self.subTest(status=status):
                trace = self.exercise("allowed-post-answer-" + status, status, NEUTRAL,
                                      pending=False)
                self.assertEqual(trace["error"], {"type": "NextBoundary", "message": "final_admission"})
                self.assertEqual([row["op"] for row in trace["commands"]], ["submit", "cancel"])
                self.assertNotIn("interrupt:synthetic-turn", trace["timeline"])


if __name__ == "__main__":
    unittest.main()
