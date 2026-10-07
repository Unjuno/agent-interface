"""Frozen current-main renewal rejection and failure-cleanup characterization."""
import ast
import json
import os
import queue
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from baseline_doom_controller_failure_cleanup_v1 import ControllerFailureCleanup

SOURCE = ROOT / "baseline_map01_overlap_controller_v39.py"


class EventQueue:
    def __init__(self, rows, events, planner, timeline):
        self.rows = iter(rows)
        self.events = events
        self.planner = planner
        self.timeline = timeline

    def get(self, timeout):
        row = next(self.rows)
        if row["event"] == "terminal":
            if not self.planner.await_started.wait(1):
                raise AssertionError("planner wait did not start before terminal delivery")
        self.events.append(row)
        self.timeline.append({
            "observation": "new_observation_consumed",
            "rejected": "stale_sequence_rejection_consumed",
            "terminal": "prior_cover_terminal_consumed",
        }[row["event"]])
        if row["event"] == "rejected":
            threading.Timer(.05, self.planner.release_await.set).start()
        return row


class ProcessStdin:
    def __init__(self):
        self.writes = []
        self.closed = False

    def write(self, value):
        self.writes.append(value)

    def flush(self):
        pass

    def close(self):
        self.closed = True


class Process:
    def __init__(self):
        self.stdin = ProcessStdin()

    def poll(self):
        return 0


class Reader:
    def join(self, timeout=None):
        pass

    def is_alive(self):
        return False


class Planner:
    def __init__(self, timeline):
        self.timeline = timeline
        self.await_started = threading.Event()
        self.release_await = threading.Event()
        self.interrupted = []
        self.closed = []

    def await_turn(self, handle, timeout):
        self.timeline.append("planner_await_started")
        self.await_started.set()
        self.release_await.wait(2)
        self.timeline.append("planner_await_returned")
        return {"status": "completed"}

    def interrupt(self, handle):
        self.interrupted.append(handle)
        self.timeline.append("planner_interrupted")
        self.release_await.set()
        return {"status": "interrupted"}

    def close(self, timeout=1):
        self.closed.append(timeout)
        self.timeline.append("planner_closed")
        self.release_await.set()


class InvalidationMonitor:
    event_types = frozenset({"observation"})

    def __init__(self):
        self.rows = []

    def observe(self, row):
        self.rows.append(row)
        return None


def extract_current_main_renewal_path():
    tree = ast.parse(SOURCE.read_bytes(), filename=str(SOURCE))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    wait_node = next(node for node in ast.walk(main)
                     if isinstance(node, ast.FunctionDef) and node.name == "wait")
    submit_node = next(node for node in ast.walk(main)
                       if isinstance(node, ast.FunctionDef) and node.name == "submit_cover")
    renewal_block = next(
        node for node in ast.walk(main)
        if isinstance(node, ast.With) and any(
            isinstance(item.context_expr, ast.Call) and
            isinstance(item.context_expr.func, ast.Name) and
            item.context_expr.func.id == "ThreadPoolExecutor"
            for item in node.items))
    factory = ast.parse(
        "def run(state, process, incoming, planner, planner_handle, monitor, "
        "failure_cleanup, reader, runtime, all_events, timeline):\n"
        "    invalidation_monitor = monitor\n"
        "    latest = {'sequence': 7}\n"
        "    clock_ns = 0\n"
        "    cover_steps = []\n"
        "    index = 0\n"
        "    cover = 'cover-0'\n"
        "    cover_ids = ['cover-0']\n"
        "    cover_terminals = []\n"
        "    cover_renewal_gaps_ms = []\n"
        "    current_cover = cover\n"
        "    current_terminal = None\n"
        "    invalidation = None\n"
        "    planner_interrupt = None\n").body[0]
    factory.body.extend([wait_node, submit_node])
    factory.body += ast.parse(
        "failure_cleanup.observe_output(all_events, reader, wait, runtime, [])\n"
        "state['wait'] = wait\n"
        "try:\n"
        "    pass\n"
        "except BaseException as error:\n"
        "    state.update(error=error, latest=latest, cover_ids=list(cover_ids), "
        "cover_terminals=list(cover_terminals), current_cover=current_cover, "
        "current_terminal=current_terminal, planner_interrupt=planner_interrupt)\n"
        "    raise\n").body
    # Replace the placeholder pass with the exact main() renewal loop block.
    try_node = factory.body[-1]
    try_node.body = [renewal_block]
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {
        "queue": queue,
        "time": time,
        "json": json,
        "ThreadPoolExecutor": ThreadPoolExecutor,
    }
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope["run"]


class CurrentMainRenewalBoundaryTests(unittest.TestCase):
    def test_stale_renewal_rejection_raises_then_cleanup_closes_planner_and_verifies_prior_empty_release(self):
        prior_accept = {"event": "accepted", "id": "cover-0"}
        prior_terminal = {
            "event": "terminal", "id": "cover-0", "status": "expired",
            "terminal_ns": 100,
            "release": {"verified": True, "keys_down": [], "buttons_down": []},
        }
        observation = {"event": "observation", "sequence": 8}
        rejection = {
            "event": "rejected", "id": "cover-0-renew-1",
            "reason": "latest observation sequence required before input",
        }
        timeline = []
        events = [prior_accept]
        planner = Planner(timeline)
        process = Process()
        incoming = EventQueue([prior_terminal, observation, rejection],
                              events, planner, timeline)
        monitor = InvalidationMonitor()
        state = {}

        with tempfile.TemporaryDirectory(prefix="v39-renewal-boundary-") as temp:
            out = Path(temp)
            runtime = out / "runtime"
            runtime.mkdir()
            failure_cleanup = ControllerFailureCleanup(planner, out)
            with self.assertRaises(RuntimeError) as raised:
                with failure_cleanup as cleanup:
                    cleanup.track(process)
                    cleanup.set_stage("planner_turn")
                    extract_current_main_renewal_path()(
                        state, process, incoming, planner, object(), monitor,
                        cleanup, Reader(), runtime, events, timeline)

            self.assertEqual(
                str(raised.exception),
                "{'event': 'rejected', 'id': 'cover-0-renew-1', "
                "'reason': 'latest observation sequence required before input'}",
            )
            self.assertEqual(state["latest"]["sequence"], 8)
            self.assertEqual(state["cover_ids"], ["cover-0"])
            self.assertEqual(len(state["cover_terminals"]), 1)
            self.assertIs(state["cover_terminals"][0], prior_terminal)
            self.assertIsNone(state["planner_interrupt"])
            self.assertEqual(process.stdin.writes, [process.stdin.writes[0]])
            command = json.loads(process.stdin.writes[0])
            self.assertEqual(command["op"], "submit")
            self.assertEqual(command["id"], "cover-0-renew-1")
            self.assertEqual(command["expected_sequence"], 7)
            self.assertEqual(monitor.rows, [])
            self.assertEqual(planner.interrupted, [])
            self.assertEqual(len(planner.closed), 1)

            receipt = json.loads((out / "controller-failure.json").read_text())
            self.assertEqual(receipt["primary_error_type"], "RuntimeError")
            self.assertEqual(receipt["failed_stage"], "planner_turn")
            self.assertTrue(receipt["input_terminals_complete"])
            self.assertTrue(receipt["input_releases_verified_empty"])
            self.assertTrue(receipt["input_release_verified_empty"])
            self.assertFalse(receipt["scorer_terminal_observed"])
            self.assertFalse(receipt["score_file_present"])
            self.assertFalse(receipt["owner_events_closed"])
            self.assertFalse(receipt["cleanup_complete"])
            self.assertLess(timeline.index("stale_sequence_rejection_consumed"),
                            timeline.index("planner_await_returned"))
            self.assertLess(timeline.index("planner_await_returned"),
                            timeline.index("planner_closed"))
            self.assertNotIn("planner_interrupted", timeline)
            mode = os.environ.get("V39_RENEWAL_TEST_MODE", "unspecified")
            if mode not in ("normal", "optimized"):
                raise AssertionError("runner must name the interpreter mode")
            (ROOT / f"observed_{mode}.json").write_text(json.dumps({
                "mode": mode,
                "initial_expected_sequence": 7,
                "new_observation_sequence": 8,
                "submitted_renewal_id": command["id"],
                "submission_response": rejection,
                "raised_exception": {
                    "type": type(raised.exception).__name__,
                    "text": str(raised.exception),
                },
                "monitor_observed_rows_during_submit": len(monitor.rows),
                "planner_interrupt_count": len(planner.interrupted),
                "timeline": timeline,
                "failure_cleanup": receipt,
                "live_game_or_native_input": False,
            }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
