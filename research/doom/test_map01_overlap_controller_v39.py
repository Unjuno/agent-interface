"""Regression for the v38 rejected-action -> unauthored coast interrupt loop."""
import sys
import unittest
from argparse import Namespace
from concurrent.futures import Future
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


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
        """A terminal can overtake its frame; never replan from pre-invalidation pixels."""
        class Reader:
            def __init__(self, *args, signal_id): self.signal_id = signal_id
            def read(self, observation):
                return {"status": "observed", "value": 90 if self.signal_id == "health" else 20,
                        "sequence": observation["sequence"], "capture_ns": observation["capture_ns"]}

        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
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
                action = {"state": "dead", "commands": [], "action_validity": [],
                          "contingencies": [], "next_cover": [], "next_cover_validity": []}
                return SimpleNamespace(answer=action, usage={}, handle=handle,
                    status="completed", answer_eligible=True, cancellation_requested=False,
                    error=None)
            def close(self): pass
            def interrupt(self, handle): return {"status": "interrupted"}

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
        # Controller wait() normally consumes the reader thread's queue. Feed
        # the same order deterministically without a process or GUI.
        import queue
        incoming = queue.Queue()
        all_events = []
        for row in observations: incoming.put(row)
        fake_process = Process()

        def fake_popen(*args, **kwargs): return fake_process

        def fake_begin(*args, **kwargs):
            planner.calls += 1
            return SimpleNamespace(turn_id=f"turn-{planner.calls}", thread_id="thread")

        class ImmediateExecutor:
            def __init__(self, max_workers): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def submit(self, fn, *args):
                future = Future()
                future.set_result(fn(*args))
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
            replacements = [
                patch.object(sys, "argv", argv),
                patch.object(controller.subprocess, "Popen", fake_popen),
                patch.object(controller.queue, "Queue", SuppliedQueue),
                patch.object(controller, "ThreadPoolExecutor", ImmediateExecutor),
                patch.object(controller, "DoomStatusNumberReader", Reader),
                patch.object(controller, "CodexAppServerClient", return_value=planner),
                patch.object(controller, "PersistentPlannerAdapter", return_value=planner),
                patch.object(controller, "begin_model_turn", fake_begin),
                patch.object(controller, "temporal_sheet", save_sheet),
                patch.object(controller, "refresh_source", side_effect=lambda latest, *a: (
                    latest, {"status": "already_observed"})),
                patch.object(controller, "build_cover_monitor", return_value=(
                    invalidation_monitor, {"authored": {"signal_id": "health"},
                                           "status": "admitted"})),
                patch.object(controller, "admitted_cover_commands", return_value=[]),
                patch.object(controller, "select_cover_monitor", side_effect=lambda monitor, admission, *a: (monitor, admission)),
                patch.object(controller, "compile_cover", return_value=[]),
                patch.object(controller, "session_command", return_value=["fake"]),
                patch.object(controller, "win", side_effect=lambda value: str(value)),
                patch.object(Path, "read_text", autospec=True, side_effect=lambda path, *a, **k: (
                    "{}" if path.name == "map01_cover_policy_schema_v6.json" else "instructions")),
                patch.object(controller, "final_admission_from_planner_result", return_value={
                    "format": "final-action-admission-v2", "status": "discarded"}),
                patch.object(controller, "record_controller_no_input", side_effect=lambda receipt, reason: dict(receipt, status=reason)),
                patch.object(controller, "latest_soft_event_summary", return_value=None),
                patch.object(controller, "ControllerFailureCleanup", Cleanup),
                patch.object(controller.atexit, "unregister"),
            ]
            with ExitStack() as stack:
                for replacement in replacements: stack.enter_context(replacement)
                controller.main()

        self.assertEqual(planner.calls, 2)
        self.assertEqual(sheets[1][-1], "fresh.png")


if __name__ == "__main__":
    unittest.main()
