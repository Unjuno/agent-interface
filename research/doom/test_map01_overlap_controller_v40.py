"""Controller integration regressions for typed unauthored-coast interrupts."""
import io
import json
import queue
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v40 as controller


class _Planner:
    def interrupt(self, _handle):
        return {"requested": True}


class _Process:
    def __init__(self):
        self.stdin = io.StringIO()


def _source_signal():
    return {"status": "observed", "signal_id": "health", "value": 85,
            "sequence": 10, "capture_ns": 1_000_000_000,
            "binding": {"pid": 7, "window": "map01"}}


class Map01V40CoastTests(unittest.TestCase):
    def test_only_unauthored_empty_coast_uses_typed_health_monitor(self):
        admission = {"authored": None, "source_signal": _source_signal()}
        monitor, receipt = controller.select_cover_monitor(
            object(), admission, [], None, 2)
        self.assertIsInstance(monitor, controller.UnauthoredCoastMonitor)
        self.assertEqual(monitor.event_types, frozenset({"typed_observation"}))
        self.assertEqual(receipt["monitor_mode"],
                         "unauthored_coast_typed_health_candidate_v1")

    def test_authored_policy_guard_is_preserved(self):
        existing = object()
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        monitor, receipt = controller.select_cover_monitor(
            existing, {"authored": authored}, [{"action": "forward"}], 0, 2)
        self.assertIs(monitor, existing)
        self.assertEqual(receipt["monitor_mode"], "authored_policy_guard")

    def test_cancel_does_not_return_until_fresh_observation_arrives(self):
        rows = iter([
            {"event": "terminal", "id": "cover-2", "status": "cancelled",
             "release": {"verified": True, "keys_down": [], "buttons_down": []}},
            {"event": "observation", "sequence": 10, "image": "stale"},
            {"event": "observation", "sequence": 11, "image": "paired"},
        ])
        consumed = []

        def wait(predicate):
            while True:
                row = next(rows)
                consumed.append(row)
                if predicate(row):
                    return row

        result = controller.cancel_invalidated_cover(
            _Planner(), object(), _Process(), wait, "cover-2",
            required_observation_sequence=11)
        self.assertEqual(result[1]["status"], "cancelled")
        self.assertEqual(consumed[-1]["image"], "paired")

    def test_completed_future_fallback_replans_from_post_invalidation_frame(self):
        class _Stdout:
            def __init__(self):
                self.rows = queue.Queue()

            def __iter__(self):
                return self

            def __next__(self):
                value = self.rows.get()
                if value is None:
                    raise StopIteration
                return value

            def put(self, row):
                self.rows.put(json.dumps(row) + "\n")

        class _Process:
            def __init__(self):
                self.stdout = _Stdout()
                self.stderr = io.StringIO()
                self.timer = None
                self.finished = False
                self.stdin = self
                self.stdout.put({"event": "ready", "fixture": {"id": "fixture"}})
                self.stdout.put({"event": "observation", "sequence": 9,
                                 "image": "initial.png", "capture_ns": 9,
                                 "capture_to_artifact_ready_ms": 0,
                                 "artifact_ready_ns": 9})

            def write(self, line):
                command = json.loads(line)
                operation = command["op"]
                identifier = command.get("id")
                if operation == "submit":
                    if identifier == "cover-1" and self.timer is not None:
                        self.timer.cancel()
                    self.stdout.put({"event": "accepted", "id": identifier,
                                     "accepted_ns": 100, "steps": [],
                                     "program_sha256": "0" * 64,
                                     "intent_token": "token"})
                elif operation == "cancel" and identifier == "cover-0":
                    self.stdout.put({"event": "typed_observation", "sequence": 11,
                                     "capture_to_typed_ready_ms": 0,
                                     "typed_ready_ns": 11, "emit_ns": 11})
                    self.stdout.put({"event": "terminal", "id": identifier,
                                     "status": "cancelled", "terminal_ns": 101,
                                     "release": {"verified": True, "keys_down": [],
                                                 "buttons_down": []}})
                    def publish_frames():
                        self.stdout.put({"event": "observation", "sequence": 10,
                                         "image": "stale.png", "capture_ns": 10,
                                         "capture_to_artifact_ready_ms": 0,
                                         "artifact_ready_ns": 10})
                        self.stdout.put({"event": "observation", "sequence": 12,
                                         "image": "fresh.png", "capture_ns": 12,
                                         "capture_to_artifact_ready_ms": 0,
                                         "artifact_ready_ns": 12})
                    self.timer = threading.Timer(2.0, publish_frames)
                    self.timer.daemon = True
                    self.timer.start()
                elif operation == "cancel" and identifier == "cover-1":
                    self.stdout.put({"event": "terminal", "id": identifier,
                                     "status": "cancelled", "terminal_ns": 102,
                                     "release": {"verified": True, "keys_down": [],
                                                 "buttons_down": []}})
                elif operation == "finish":
                    self.stdout.put({"event": "post_control_score", "score": 0})
                    self.stdout.rows.put(None)
                    self.finished = True
                return len(line)

            def flush(self):
                pass

            def poll(self):
                return 0 if self.finished else None

            def wait(self, timeout=None):
                return 0

        class _Monitor:
            event_types = frozenset({"typed_observation"})
            soft_event_count = 0
            latest_soft_event = None

            def observe(self, row):
                if row["event"] == "typed_observation":
                    return {"event": "policy_invalidation", "sequence": 11}
                return None

        class _Client:
            thread_id = "thread"

            def __init__(self, *args, **kwargs):
                pass

            def initialize(self):
                pass

            def close(self):
                pass

        class _Planner:
            thread_id = "thread"

            def __init__(self, *args, **kwargs):
                self.calls = 0

            def start_session(self):
                pass

            def await_turn(self, handle, timeout):
                self.calls += 1
                return SimpleNamespace(
                    answer={"state": "terminal"}, usage={}, handle=handle, status="complete",
                    answer_eligible=self.calls == 1,
                    cancellation_requested=False, error=None)

            def interrupt(self, handle):
                return {"requested": True}

        class _Pool:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def submit(self, function, *args):
                result = function(*args)
                return SimpleNamespace(done=lambda: True, result=lambda: result)

        process = _Process()
        observed_sources = []
        source_signal = {"status": "observed", "signal_id": "health", "value": 85,
                         "sequence": 9, "capture_ns": 9,
                         "binding": {"pid": 7, "window": "map01"}}

        class _SignalReader:
            def __init__(self, *args, signal_id, **kwargs):
                self.signal_id = signal_id

            def read(self, observation):
                value = 85 if self.signal_id == "health" else 8
                return {**source_signal, "signal_id": self.signal_id, "value": value,
                        "sequence": observation["sequence"]}

        def record_sheet(sources, target):
            observed_sources.append([str(source) for source in sources])
            Path(target).write_bytes(b"test image")

        def make_handle(planner, *args, **kwargs):
            return SimpleNamespace(turn_id=f"turn-{len(observed_sources)}",
                                   thread_id="thread")

        def monitor_builder(*args, **kwargs):
            return _Monitor(), {"authored": None, "source_signal": source_signal}

        with tempfile.TemporaryDirectory() as temporary, \
                mock.patch.object(sys, "argv", ["controller", "--out", str(Path(temporary) / "out"),
                    "--iterations", "2", "--model", "test", "--effort", "low",
                    "--load-fixture-manifest", "fixture.json"]), \
                mock.patch.object(controller, "app_server_command", return_value=[]), \
                mock.patch.object(controller, "win", side_effect=lambda path: str(path)), \
                mock.patch.object(controller, "session_command", return_value=[]), \
                mock.patch.object(controller, "CodexAppServerClient", _Client), \
                mock.patch.object(controller, "PersistentPlannerAdapter", _Planner), \
                mock.patch.object(controller, "DoomStatusNumberReader", _SignalReader), \
                mock.patch.object(controller.subprocess, "Popen", return_value=process), \
                mock.patch.object(controller, "ThreadPoolExecutor", _Pool), \
                mock.patch.object(controller, "build_cover_monitor", side_effect=monitor_builder), \
                mock.patch.object(controller, "select_cover_monitor",
                                  side_effect=lambda monitor, admission, *a: (monitor, admission)), \
                mock.patch.object(controller, "admitted_cover_commands", side_effect=lambda commands, *_: commands), \
                mock.patch.object(controller, "compile_cover", return_value=[]), \
                mock.patch.object(controller, "temporal_sheet", side_effect=record_sheet), \
                mock.patch.object(controller, "begin_model_turn", side_effect=make_handle), \
                mock.patch.object(controller, "final_admission_from_planner_result",
                                  return_value={"status": "not_admitted"}), \
                mock.patch.object(controller, "latest_soft_event_summary", return_value=None):
            controller.main()

        self.assertEqual(len(observed_sources), 2)
        self.assertEqual(observed_sources[1][-1], "fresh.png")


if __name__ == "__main__":
    unittest.main()

