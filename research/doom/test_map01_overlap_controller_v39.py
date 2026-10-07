"""Regression for the v38 rejected-action -> unauthored coast interrupt loop."""
import ast
import types
import sys
import unittest
from argparse import Namespace
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


def extract_renewal_invalidation_branch():
    tree = ast.parse(Path(controller.__file__).read_bytes())
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    branch = next(node for node in ast.walk(main)
                  if isinstance(node, ast.If) and
                  any(isinstance(child, ast.Name) and child.id == "next_accepted"
                      for child in ast.walk(node.test)) and
                  "policy_invalidation" in ast.dump(node.test))
    resolver = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "resolve_invalidated_cover_submission")
    factory = ast.parse(
        "def factory(next_accepted, next_cover, planner, planner_handle, "
        "process, wait, cover_terminals, cover_ids, current_cover, current_terminal):\n"
        "    invalidation = None\n"
        "    planner_interrupt = None\n"
        "    renewal_admission_resolution = None\n").body[0]
    factory.body = [ast.While(test=ast.Constant(value=True),
                              body=[branch, ast.parse("break").body[0]], orelse=[])]
    factory.body += ast.parse(
        "return (invalidation, current_cover, planner_interrupt, current_terminal, "
        "cover_terminals, cover_ids, renewal_admission_resolution)\n").body
    module = ast.fix_missing_locations(ast.Module(body=[resolver, factory], type_ignores=[]))
    scope = {"cancel_invalidated_cover": controller.cancel_invalidated_cover}
    exec(compile(module, str(controller.__file__), "exec"), scope)
    return scope["factory"]



class Map01V39CoastTests(unittest.TestCase):
    def test_invalidation_frame_requires_matching_epoch_capture_and_binding(self):
        invalidation = {"sequence": 11, "capture_ns": 110,
                        "pointer_binding": {"focus": 7, "surface": 7},
                        "frame_rgb_sha256": "a" * 64}
        stale = {"event": "observation", "sequence": 12, "capture_ns": 105,
                 "image": "pre-invalidation.png",
                 "pointer_binding": {"focus": 7, "surface": 7}}
        wrong_binding = {"event": "observation", "sequence": 12, "capture_ns": 115,
                         "image": "wrong-window.png",
                         "pointer_binding": {"focus": 8, "surface": 8},
                         "frame_rgb_sha256": "a" * 64}
        wrong_frame = {"event": "observation", "sequence": 12, "capture_ns": 115,
                       "image": "different-frame.png",
                       "pointer_binding": {"focus": 7, "surface": 7},
                       "frame_rgb_sha256": "b" * 64}
        fresh = {"event": "observation", "sequence": 11, "capture_ns": 110,
                 "image": "paired.png",
                 "pointer_binding": {"focus": 7, "surface": 7},
                 "frame_rgb_sha256": "a" * 64}
        queued = iter((wrong_binding, wrong_frame, fresh))
        seen = []

        def wait(predicate, timeout):
            while True:
                candidate = next(queued)
                seen.append(candidate)
                if predicate(candidate):
                    return candidate

        result = controller.wait_for_invalidation_frame(stale, invalidation, wait)
        self.assertIs(result, fresh)
        self.assertEqual(seen, [wrong_binding, wrong_frame, fresh])

    def test_invalidation_frame_rejects_incomplete_identity(self):
        for invalidation in (
            {"sequence": 11, "capture_ns": 110},
            {"sequence": 11, "capture_ns": 0,
             "pointer_binding": {"focus": 7}},
            {"sequence": 11, "capture_ns": 110,
             "pointer_binding": {"focus": 7}, "frame_rgb_sha256": "bad"},
        ):
            with self.subTest(invalidation=invalidation):
                with self.assertRaisesRegex(RuntimeError, "observation identity"):
                    controller.wait_for_invalidation_frame(None, invalidation,
                        lambda *args, **kwargs: self.fail("must reject before waiting"))

    def test_session_command_keeps_v12_default_and_selects_v15_only_when_opted_in(self):
        args = Namespace(seed=990605, load_fixture_manifest=Path("fixture.json"))
        default = controller.session_command(args, Path("runtime"))
        self.assertEqual(Path(default[1]).name, "session_map01_v12.py")
        self.assertIn("--out", default)
        self.assertIn("--load-fixture-manifest", default)

        args.measurement_session = True
        measured = controller.session_command(args, Path("runtime"))
        self.assertEqual(Path(measured[1]).name, "session_map01_v15.py")
        self.assertEqual(measured[2:], default[2:])

    def test_rejected_action_followup_keeps_model_turn_alive_on_damage(self):
        previous = {"iteration": 1, "model_action_discarded": True,
                    "action": {"state": "active", "next_cover": [
                        {"action": "strafe_left", "extent": "short"}],
                        "next_cover_validity": [{"signal_id": "health",
                            "critical_health_minimum": 35,
                            "maximum_health_loss": 12,
                            "max_source_age_ms": 30000}]}}
        commands, validity, source = controller.reusable_cover([previous])
        self.assertEqual((commands, validity, source), ([], None, None))
        default_receipt = {"authored": None, "effective": {
            "hard_minimum": 85, "maximum_health_loss": 0}}
        selected, receipt = controller.select_cover_monitor(
            object(), default_receipt, commands, source)
        self.assertIsInstance(selected, controller.UnauthoredCoastMonitor)
        self.assertEqual(receipt["monitor_mode"], "unauthored_coast_no_policy")
        self.assertEqual(selected.event_types, frozenset())
        self.assertEqual(selected.soft_event_count, 0)
        self.assertIsNone(selected.latest_soft_event)
        # The exact frame still updates latest in the caller, while the
        # unauthored coast publishes no policy event that can interrupt.
        self.assertEqual(default_receipt["effective"]["hard_minimum"], 85)

    def test_authored_cover_still_uses_original_guard(self):
        guard = object()
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        selected, receipt = controller.select_cover_monitor(
            guard, {"authored": authored},
            [{"action": "strafe_left", "extent": "short"}], 0)
        self.assertIs(selected, guard)
        self.assertEqual(receipt["monitor_mode"], "authored_policy_guard")
        self.assertEqual(receipt["authored"], authored)

    def test_running_invalidation_interrupts_planner_and_requires_verified_empty_release(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()
        class Planner:
            def __init__(self): self.interrupted = []
            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"status": "interrupted"}
        terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        process, planner, handle = Process(), Planner(), object()

        interruption, result = controller.cancel_invalidated_cover(
            planner, handle, process, lambda predicate: terminal, "cover-0")

        self.assertIs(result, terminal)
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(interruption, {"status": "interrupted"})
        self.assertIn('"op": "cancel"', process.stdin.writes[0])

    def test_running_invalidation_rejects_nonempty_or_unverified_release(self):
        class Stdin:
            def write(self, value): pass
            def flush(self): pass
        class Process:
            stdin = Stdin()
        class Planner:
            def interrupt(self, handle): return {"status": "interrupted"}
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": []},
            {"verified": True, "keys_down": [], "buttons_down": ["fire"]},
        ):
            terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                        "release": release}
            with self.subTest(release=release):
                with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                    controller.cancel_invalidated_cover(
                        Planner(), object(), Process(), lambda predicate: terminal, "cover-0")

    def test_policy_invalidation_handoff_waits_for_fresh_frame_before_next_plan(self):
        self._exercise_invalidation_handoff()

    def test_real_health_monitor_hard_invalidation_reaches_next_plan(self):
        self._exercise_invalidation_handoff(health_mode="hard")

    def test_real_health_monitor_unknown_invalidation_reaches_next_plan(self):
        self._exercise_invalidation_handoff(health_mode="unknown")

    def test_pending_health_invalidation_interrupts_before_completion(self):
        self._exercise_invalidation_handoff(health_mode="hard", pending=True)

    def test_pending_unknown_health_interrupts_before_completion(self):
        self._exercise_invalidation_handoff(health_mode="unknown", pending=True)

    def test_pending_invalidation_does_not_replan_without_neutral_release(self):
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": []},
            {"verified": True, "keys_down": [], "buttons_down": [1]},
        ):
            with self.subTest(release=release):
                self._exercise_invalidation_handoff(
                    health_mode="hard", pending=True, bad_release=release)

    def _exercise_invalidation_handoff(self, health_mode=None, *, pending=False,
                                       bad_release=None):
        """A terminal can overtake its frame; never replan from pre-invalidation pixels."""
        testcase = self
        timeline = []
        started = Event()
        complete = Event()
        futures = []
        trace = {"timeline": timeline, "pending": pending,
                 "health_mode": health_mode, "bad_release": bad_release}

        class Reader:
            def __init__(self, *args, signal_id): self.signal_id = signal_id
            def read(self, observation):
                if health_mode == "unknown" and observation["sequence"] == 11:
                    raise ValueError("unreadable health fixture")
                health = 60 if observation["sequence"] == 11 else 90
                return {"format": "observable-signal-v1",
                        "status": "observed", "value": health if self.signal_id == "health" else 20,
                        "signal_id": self.signal_id,
                        "binding": observation["pointer_binding"],
                        "sequence": observation["sequence"], "capture_ns": observation["capture_ns"]}

        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value):
                self.writes.append(value)
                command = json.loads(value)
                timeline.append("command:" + command["op"] + ":" + command.get("id", ""))
            def flush(self): pass

        class Process:
            def __init__(self, *args, **kwargs):
                self.stdin = Stdin()
                self.stdout = iter(())
                self.stderr = SimpleNamespace(read=lambda: "")
                self._alive = True
            def poll(self): return None if self._alive else 0
            def wait(self, timeout=None): self._alive = False; return 0

        class Planner:
            thread_id = "thread"
            def __init__(self): self.calls = 0
            def start_session(self): pass
            def initialize(self): pass
            def await_turn(self, handle, timeout):
                if pending and handle.turn_id == "turn-1":
                    timeline.append("planner_wait_started")
                    started.set()
                    if not complete.wait(2):
                        raise RuntimeError("fixture planner was never interrupted")
                    timeline.append("planner_completed_after_interrupt")
                action = {"state": "dead", "commands": [], "action_validity": [],
                          "contingencies": [], "next_cover": [], "next_cover_validity": []}
                if pending and handle.turn_id == "turn-1":
                    action = {"state": "active",
                              "commands": [{"action": "forward", "extent": "short"}],
                              "action_validity": [{"critical_health_minimum": 35,
                                  "maximum_health_loss": 12, "minimum_ammo": 0,
                                  "max_current_age_ms": 1000}],
                              "contingencies": [],
                              "next_cover": [{"action": "strafe_left", "extent": "short"}],
                              "next_cover_validity": [{"signal_id": "health",
                                  "critical_health_minimum": 35, "maximum_health_loss": 12,
                                  "max_source_age_ms": 30000}]}
                    controller.validate_action(action)
                    source = Reader(signal_id="health").read(observations[1])
                    controller.build_action_contract(
                        action["commands"], action["action_validity"][0], source)
                    testcase.assertTrue(controller.bindings_equal_exact(
                        source["binding"], {"focus": 7, "surface": 7,
                                            "geometry": [0, 0, 640, 480]}))
                    timeline.append("active_answer_contract_validated")
                return SimpleNamespace(answer=action, usage={}, handle=handle,
                    status="completed", answer_eligible=True, cancellation_requested=False,
                    error=None)
            def close(self): complete.set()
            def interrupt(self, handle):
                if pending:
                    testcase.assertTrue(started.is_set())
                    testcase.assertTrue(futures and not futures[0].done())
                    timeline.append("interrupt:" + handle.turn_id)
                    complete.set()
                return {"status": "interrupted"}

        planner = Planner()
        observations = [
            {"event": "ready", "fixture": {"loaded": True}},
            {"event": "observation", "sequence": 10, "capture_ns": 100,
             "image": "old.png", "pointer_binding": {"focus": 7, "surface": 7}, "step": 0},
            {"event": "accepted", "id": "cover-0", "accepted_ns": 105,
             "steps": [], "program_sha256": "x", "intent_token": "cover0"},
            # Typed invalidation and cover terminal arrive before the frame
            # paired with that typed receipt. A later frame is also stale.
            {"event": "typed_observation", "sequence": 11, "capture_ns": 110,
             "pointer_binding": {"focus": 7, "surface": 7}},
            {"event": "terminal", "id": "cover-0", "status": "cancelled",
             "terminal_ns": 120, "release": {"verified": True, "keys_down": [],
             "buttons_down": []}},
            {"event": "observation", "sequence": 10, "capture_ns": 100,
             "image": "stale.png", "pointer_binding": {"focus": 7, "surface": 7}, "step": 0},
            {"event": "observation", "sequence": 12, "capture_ns": 130,
             "image": "fresh.png", "pointer_binding": {"focus": 7, "surface": 7}, "step": 0},
            {"event": "accepted", "id": "cover-1", "accepted_ns": 135,
             "steps": [], "program_sha256": "y", "intent_token": "cover1"},
            {"event": "terminal", "id": "cover-1", "status": "completed",
             "terminal_ns": 140, "release": {"verified": True, "keys_down": [],
             "buttons_down": []}},
            {"event": "post_control_score", "score": 1},
        ]
        if health_mode is not None:
            # The real health-only monitor consumes full observations. A later
            # frame overtakes terminal completion; identity must still name 11.
            observations[3] = dict(observations[3], event="observation",
                                   image="invalidation.png", step=0)
            observations[4:8] = [observations[6], observations[4], observations[7]]
        if pending:
            terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                        "terminal_ns": 120, "release": bad_release or {
                            "verified": True, "keys_down": [], "buttons_down": []}}
            wrong = {"event": "observation", "sequence": 12, "capture_ns": 115,
                     "image": "wrong-window.png", "step": 0,
                     "pointer_binding": {"focus": 8, "surface": 8}}
            stale = {"event": "observation", "sequence": 12, "capture_ns": 105,
                     "image": "stale-new-sequence.png", "step": 0,
                     "pointer_binding": {"focus": 7, "surface": 7}}
            fresh = {"event": "observation", "sequence": 12, "capture_ns": 130,
                     "image": "fresh.png", "step": 0,
                     "pointer_binding": {"focus": 7, "surface": 7}}
            observations = observations[:4] + [wrong, terminal, stale, fresh] + observations[6:]
            for row in observations:
                if "pointer_binding" in row:
                    row["pointer_binding"]["geometry"] = [0, 0, 640, 480]
        # Controller wait() normally consumes the reader thread's queue. Feed
        # the same order deterministically without a process or GUI.
        import queue
        class TraceQueue(queue.Queue):
            def get(self, *args, **kwargs):
                row = super().get(*args, **kwargs)
                timeline.append("row:" + row["event"] + ":" + str(row.get("id", row.get("sequence", ""))))
                return row
        incoming = TraceQueue()
        all_events = []
        for row in observations: incoming.put(row)
        fake_process = Process()

        def fake_popen(*args, **kwargs): return fake_process

        def fake_begin(*args, **kwargs):
            planner.calls += 1
            timeline.append("begin:turn-" + str(planner.calls))
            return SimpleNamespace(turn_id=f"turn-{planner.calls}", thread_id="thread")

        class ImmediateExecutor:
            def __init__(self, max_workers): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def submit(self, fn, *args):
                future = Future()
                future.set_result(fn(*args))
                return future

        class PendingExecutor:
            def __init__(self, max_workers):
                self.pool = ThreadPoolExecutor(max_workers=max_workers)
            def __enter__(self): return self
            def __exit__(self, *args):
                complete.set()
                self.pool.shutdown(wait=True)
            def submit(self, fn, *args):
                future = self.pool.submit(fn, *args)
                futures.append(future)
                if len(futures) == 1:
                    if not started.wait(2):
                        raise RuntimeError("fixture planner did not start")
                    if future.done():
                        raise RuntimeError("fixture planner must be pending")
                else:
                    future.result(timeout=2)
                return future

        # Patch queue construction so the controller sees the ordered rows;
        # its background stdout reader stays empty.
        class SuppliedQueue:
            def __new__(cls): return incoming

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            argv = ["controller", "--out", str(out), "--iterations", "2",
                    "--model", "test", "--effort", "low",
                    "--load-fixture-manifest", str(Path(temp) / "fixture.json")]
            (Path(temp) / "fixture.json").write_text("{}")
            sheets = []
            def save_sheet(paths, target):
                sheets.append([Path(p).name for p in paths])
                Path(target).write_bytes(b"test sheet")

            class Cleanup:
                def __init__(self, *args): pass
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def track(self, *args): pass
                def observe_output(self, *args): pass
                def set_stage(self, *args): pass
            invalidation_monitor = SimpleNamespace(event_types={"typed_observation"},
                observe=lambda row: {"sequence": 11, "capture_ns": 110,
                    "pointer_binding": {"focus": 7, "surface": 7},
                    "event": "hard_change"},
                soft_event_count=0, latest_soft_event=None)
            monitor_factory = controller.build_cover_monitor

            def build_real_monitor(*args, **kwargs):
                monitor, receipt = monitor_factory(*args, **kwargs)
                self.assertIsInstance(monitor, controller.ObservableSignalPolicyMonitor)
                if pending:
                    original_observe = monitor.observe
                    def observe(row):
                        if row["sequence"] == 11:
                            self.assertTrue(futures and not futures[0].done())
                            timeline.append("observe_invalidation_while_pending")
                        return original_observe(row)
                    monitor.observe = observe
                return monitor, receipt

            frame_barrier = controller.wait_for_invalidation_frame
            barrier_events = []

            def checked_frame_barrier(latest, invalidation, wait, timeout=5):
                barrier_events.append(invalidation)
                timeline.append("frame_barrier_enter")
                result = frame_barrier(latest, invalidation, wait, timeout)
                self.assertEqual(invalidation["sequence"], 11)
                self.assertEqual(invalidation["capture_ns"], 110)
                if health_mode is not None:
                    self.assertEqual(invalidation["outcome"]["status"],
                                     "HARD_INVALIDATED" if health_mode == "hard" else "UNKNOWN")
                if pending:
                    self.assertEqual(Path(result["image"]).name, "fresh.png")
                timeline.append("frame_barrier_pass:" + Path(result["image"]).name)
                return result

            replacements = [
                patch.object(sys, "argv", argv),
                patch.object(controller.subprocess, "Popen", fake_popen),
                patch.object(controller.queue, "Queue", SuppliedQueue),
                patch.object(controller, "ThreadPoolExecutor", PendingExecutor if pending else ImmediateExecutor),
                patch.object(controller, "DoomStatusNumberReader", Reader),
                patch.object(controller, "CodexAppServerClient", return_value=planner),
                patch.object(controller, "PersistentPlannerAdapter", return_value=planner),
                patch.object(controller, "begin_model_turn", fake_begin),
                patch.object(controller, "temporal_sheet", save_sheet),
                patch.object(controller, "refresh_source", side_effect=lambda latest, *a: (
                    latest, {"status": "already_observed"})),
                patch.object(controller, "build_cover_monitor", side_effect=(
                    build_real_monitor if health_mode is not None else
                    lambda *a, **k: (invalidation_monitor, {
                        "authored": {"signal_id": "health"}, "status": "admitted"}))),
                patch.object(controller, "wait_for_invalidation_frame", checked_frame_barrier),
                patch.object(controller, "session_command", return_value=["fake"]),
                patch.object(controller, "win", side_effect=lambda value: str(value)),
                patch.object(Path, "read_text", autospec=True, side_effect=lambda path, *a, **k: (
                    "{}" if path.name == "map01_cover_policy_schema_v6.json" else "instructions")),
                patch.object(controller, "latest_soft_event_summary", return_value=None),
                patch.object(controller, "ControllerFailureCleanup", Cleanup),
                patch.object(controller.atexit, "unregister"),
            ]
            if pending:
                # The planner transport is synthetic, but authored-policy
                # selection, compilation and final admission remain production.
                replacements.append(patch.object(controller, "reusable_cover", return_value=(
                    [{"action": "strafe_left", "extent": "short"}],
                    {"signal_id": "health", "critical_health_minimum": 35,
                     "maximum_health_loss": 12, "max_source_age_ms": 30000}, 0)))
            else:
                replacements.extend([
                    patch.object(controller, "admitted_cover_commands", return_value=[]),
                    patch.object(controller, "select_cover_monitor", side_effect=lambda monitor, admission, *a: (monitor, admission)),
                    patch.object(controller, "compile_cover", return_value=[]),
                    patch.object(controller, "final_admission_from_planner_result", return_value={
                        "format": "final-action-admission-v2", "status": "discarded"}),
                    patch.object(controller, "record_controller_no_input", side_effect=lambda receipt, reason: dict(receipt, status=reason)),
                ])
            with ExitStack() as stack:
                for replacement in replacements: stack.enter_context(replacement)
                if bad_release is None:
                    controller.main()
                else:
                    with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                        controller.main()
            report = json.loads((out / "report.json").read_text()) if (out / "report.json").exists() else None

        commands = [json.loads(value) for value in fake_process.stdin.writes]
        trace.update(commands=commands, planner_calls=planner.calls,
                     barrier_events=barrier_events, sheets=sheets, report=report)
        import os
        trace_root = os.environ.get("AI_PENDING_TEST_OUT")
        if trace_root and pending:
            suffix = "neutral" if bad_release is None else (
                "unverified" if not bad_release["verified"] else
                "keys-down" if bad_release["keys_down"] else "buttons-down")
            trace_path = Path(trace_root) / (health_mode + "-" + suffix + ".json")
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            with trace_path.open("x") as handle:
                json.dump(trace, handle, indent=2)
        if pending:
            self.assertIn("active_answer_contract_validated", timeline)
            self.assertIn("observe_invalidation_while_pending", timeline)
            self.assertLess(timeline.index("observe_invalidation_while_pending"), timeline.index("interrupt:turn-1"))
            self.assertLess(timeline.index("interrupt:turn-1"), timeline.index("planner_completed_after_interrupt"))
            self.assertEqual([row["id"] for row in commands if row["op"] == "cancel"],
                             ["cover-0"] if bad_release is not None else ["cover-0", "cover-1"])
            self.assertFalse(any(row.get("id", "").startswith("plan-") for row in commands))
            if bad_release is not None:
                self.assertEqual(planner.calls, 1)
                self.assertEqual(barrier_events, [])
                self.assertEqual([row["id"] for row in commands if row["op"] == "submit"], ["cover-0"])
                return
            self.assertLess(timeline.index("row:terminal:cover-0"), timeline.index("frame_barrier_enter"))
            self.assertLess(timeline.index("frame_barrier_pass:fresh.png"), timeline.index("begin:turn-2"))
            self.assertTrue(report["decisions"][0]["model_action_discarded"])
            self.assertEqual(report["decisions"][0]["discard_reason"], "policy_dependency_invalidated")
            self.assertFalse(report["decisions"][0]["final_action_admission"]["input_authority_admitted"])

        self.assertEqual(planner.calls, 2)
        self.assertEqual(len(barrier_events), 1)
        self.assertEqual(sheets[1][-1], "fresh.png")


    def test_accepted_first_renewal_keeps_monitor_until_final_plan_admission(self):
        source = Path(controller.__file__).read_text(encoding="utf-8")
        self.assertIn(
            "observation_monitor=invalidation_monitor)",
            source[source.index("while not future.done():"):source.index("planner_result=future.result()")],
        )
        invalidation_path = source[
            source.index("final_action_admission=final_admission_from_planner_result("):
            source.index('"terminal_candidate":True')
        ]
        self.assertIn("if invalidation is not None:", invalidation_path)
        self.assertIn('"model_action_discarded":True', invalidation_path)
        self.assertIn('"plan_terminal":"not_admitted"', invalidation_path)
        self.assertLess(
            source.index('"plan_terminal":"not_admitted"'),
            source.index("failure_cleanup.set_stage(\"action_admission\")"),
        )


    def test_running_invalidation_accepts_naturally_completed_cover_only_when_neutral(self):
        class Stdin:
            def write(self, value): pass
            def flush(self): pass
        class Process:
            stdin = Stdin()
        class Planner:
            def interrupt(self, handle): return {"status": "interrupted"}

        def wait_for_matching_terminal(terminal):
            unrelated = dict(terminal, id="other-cover")
            rows = (unrelated, terminal)

            def wait(predicate):
                return next((row for row in rows if predicate(row)), None)

            return wait

        for status in ("completed", "expired"):
            neutral_terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
            result = controller.cancel_invalidated_cover(
                Planner(), object(), Process(), wait_for_matching_terminal(neutral_terminal),
                "cover-0")
            self.assertIs(result[1], neutral_terminal)

            held_terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": ["space"], "buttons_down": []}}
            with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                controller.cancel_invalidated_cover(
                    Planner(), object(), Process(), wait_for_matching_terminal(held_terminal),
                    "cover-0")

        for status in ("failed", "needs_decision"):
            terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
            with self.subTest(status=status):
                with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                    controller.cancel_invalidated_cover(
                        Planner(), object(), Process(), wait_for_matching_terminal(terminal),
                        "cover-0")


    def test_renewal_invalidation_interrupts_planner_and_cancels_current_cover(self):
        invalidation = {"reason": "health_below_floor", "sequence": 18}
        terminal = {"event": "terminal", "id": "cover-renew-1",
                    "status": "cancelled", "release": {
                        "verified": True, "keys_down": [], "buttons_down": []}}

        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass

        class Planner:
            def __init__(self, trace): self.interrupted = []; self.trace = trace
            def interrupt(self, handle):
                self.interrupted.append(handle)
                self.trace.append("planner_interrupt")
                return {"status": "interrupted"}

        process = types.SimpleNamespace(stdin=Stdin())
        trace = []
        planner = Planner(trace)
        handle = object()
        accepted = {"event": "accepted", "id": "cover-renew-1"}
        responses = [accepted, terminal]

        def wait(predicate):
            row = responses.pop(0)
            trace.append("wait_" + row["event"])
            self.assertTrue(predicate(row))
            return row

        prior_terminal = {"event": "terminal", "id": "cover-0", "status": "expired",
                          "release": {"verified": True, "keys_down": [],
                                      "buttons_down": []}}
        cover_terminals = [prior_terminal]
        cover_ids = ["cover-0"]
        result = extract_renewal_invalidation_branch()(
            {"event": "policy_invalidation", "invalidation": invalidation},
            "cover-renew-1", planner, handle, process, wait, cover_terminals,
            cover_ids, "cover-0", prior_terminal)

        self.assertEqual(result[:2], (invalidation, "cover-renew-1"))
        self.assertEqual(result[2], {"status": "interrupted"})
        self.assertIs(result[3], terminal)
        self.assertEqual(result[4], [prior_terminal, terminal])
        self.assertEqual(result[5], ["cover-0", "cover-renew-1"])
        self.assertEqual(result[6], {"status": "accepted", "response": accepted})
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(trace, ["planner_interrupt", "wait_accepted", "wait_terminal"])
        self.assertEqual(json.loads(process.stdin.writes[0]),
                         {"op": "cancel", "id": "cover-renew-1"})


    def test_rejected_invalidated_renewal_interrupts_without_cancel_or_new_terminal(self):
        invalidation = {"reason": "health_below_floor", "sequence": 19}
        prior_terminal = {"event": "terminal", "id": "cover-0", "status": "expired",
                          "release": {"verified": True, "keys_down": [],
                                      "buttons_down": []}}

        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass

        class Planner:
            def __init__(self, trace): self.interrupted = []; self.trace = trace
            def interrupt(self, handle):
                self.interrupted.append(handle)
                self.trace.append("planner_interrupt")
                return {"status": "interrupted"}

        process = types.SimpleNamespace(stdin=Stdin())
        trace = []
        planner = Planner(trace)
        handle = object()
        rejected = {"event": "rejected",
                    "reason": "latest observation sequence required before input"}
        waits = []

        def wait(predicate):
            waits.append(rejected)
            trace.append("wait_rejected")
            self.assertTrue(predicate(rejected))
            return rejected

        cover_terminals = [prior_terminal]
        cover_ids = ["cover-0"]
        result = extract_renewal_invalidation_branch()(
            {"event": "policy_invalidation", "invalidation": invalidation},
            "cover-renew-1", planner, handle, process, wait, cover_terminals,
            cover_ids, "cover-0", prior_terminal)

        self.assertEqual(result[:2], (invalidation, "cover-0"))
        self.assertEqual(result[2], {"status": "interrupted"})
        self.assertIs(result[3], prior_terminal)
        self.assertEqual(result[4], [prior_terminal])
        self.assertEqual(result[5], ["cover-0"])
        self.assertEqual(result[6], {"status": "rejected", "response": rejected})
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(waits, [rejected])
        self.assertEqual(trace, ["planner_interrupt", "wait_rejected"])
        self.assertEqual(process.stdin.writes, [])



if __name__ == "__main__":
    unittest.main()
