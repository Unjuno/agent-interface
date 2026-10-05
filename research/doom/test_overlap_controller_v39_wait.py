"""Stdlib regressions for v39's nested wait; no game/backend/client import."""
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import tempfile
import types
import unittest

SOURCE = Path(os.environ.get("V39_WAIT_SOURCE", Path(__file__).with_name("map01_overlap_controller_v39.py")))
EMPTY = object()


class UnreadableStderr:
    def __init__(self, error=None):
        self.calls = 0
        self.error = error or AssertionError("synchronous stderr drain entered")

    def read(self):
        self.calls += 1
        raise self.error


class Process:
    def __init__(self, exit_code, stderr=None):
        self.exit_code = exit_code
        self.stderr = stderr or UnreadableStderr()
        self.poll_calls = 0

    def poll(self):
        self.poll_calls += 1
        return self.exit_code


class ScriptQueue:
    def __init__(self, rows):
        self.rows = iter(rows)

    def get(self, timeout):
        row = next(self.rows, EMPTY)
        if row is EMPTY:
            raise queue.Empty()
        return row


class Clock:
    def __init__(self):
        self.value = 0

    def monotonic(self):
        self.value += .01
        return self.value


def extract_wait(process, rows, handle=None, forward=None):
    tree = ast.parse(SOURCE.read_bytes())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    wait = next(node for node in ast.walk(main) if isinstance(node, ast.FunctionDef) and node.name == "wait")
    factory = ast.parse("def factory(process, incoming, handle, forward):\n latest = None\n active_turn_handle = handle\n active_decision_index = 3\n active_observation_delivery = None\n planner = object()\n").body[0]
    factory.body.append(wait)
    factory.body += ast.parse("wait.active_observation_delivery = lambda: active_observation_delivery\nreturn wait, lambda: latest").body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"queue": queue, "time": Clock(),
             "deliver_active_soft_observation": forward or (lambda *_args: None)}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope["factory"](process, ScriptQueue(rows), handle, forward)


class WaitTests(unittest.TestCase):
    def test_active_observation_helper_binds_frame_sequence_and_no_authority(self):
        tree = ast.parse(SOURCE.read_bytes())
        helpers = [node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and
                   node.name in {"_typed_json_equal", "deliver_active_soft_observation"}]
        if {node.name for node in helpers} != {"_typed_json_equal", "deliver_active_soft_observation"}:
            self.fail("pinned current V39 observation helpers are missing")
        module = ast.fix_missing_locations(ast.Module(body=helpers, type_ignores=[]))
        scope = {"Path": Path, "base64": base64, "hashlib": hashlib, "json": json}
        exec(compile(module, str(SOURCE), "exec"), scope)
        frame = b"\x89PNG\r\n\x1a\nfixture"
        observation = {"event": "observation", "sequence": 10,
                       "capture_ns": 1_000_000_000,
                       "pointer_binding": {"focus": 7}, "image": None}
        event = {"sequence": 10, "signal": {"status": "observed",
                 "signal_id": "health", "value": 80, "sequence": 10,
                 "capture_ns": 1_000_000_000, "binding": {"focus": 7}},
                 "outcome": {"status": "SOFT_CHANGED",
                             "requires_new_decision": False,
                             "grants_input_authority": False}}
        class Planner:
            def __init__(self): self.calls = []
            def send_external_observation(self, handle, sequence, text, image_url):
                self.calls.append((handle, sequence, text, image_url))
                return {"outcome": "attached", "sequence": sequence,
                        "thread_id": "thread-1", "turn_id": "turn-1"}
        planner = Planner()
        handle = object()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "current.png"
            path.write_bytes(frame)
            observation["image"] = str(path)
            receipt = scope["deliver_active_soft_observation"](
                planner, handle, observation, event)
        self.assertEqual(len(planner.calls), 1)
        self.assertIs(planner.calls[0][0], handle)
        self.assertEqual(planner.calls[0][1], 10)
        self.assertIn('"sequence":10', planner.calls[0][2])
        self.assertIn("grants no input authority", planner.calls[0][2])
        self.assertEqual(planner.calls[0][3],
                         "data:image/png;base64," + base64.b64encode(frame).decode("ascii"))
        self.assertEqual(receipt["frame_sha256"], hashlib.sha256(frame).hexdigest())
        self.assertFalse(receipt["input_authority"])
        self.assertIsNone(scope["deliver_active_soft_observation"](
            planner, handle, observation, {**event, "sequence": 11}))
        self.assertEqual(len(planner.calls), 1)

    def test_exited_session_does_not_enter_unbounded_stderr_read(self):
        process = Process(0)
        wait, latest = extract_wait(process, [])
        with self.assertRaisesRegex(RuntimeError, "session exited before expected event"):
            wait(lambda row: False)
        self.assertEqual(process.stderr.calls, 0)

    def test_bad_stderr_decoding_does_not_replace_session_exit(self):
        stderr = UnreadableStderr(UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"))
        wait, latest = extract_wait(Process(1, stderr), [])
        with self.assertRaisesRegex(RuntimeError, "session exited before expected event"):
            wait(lambda row: False)
        self.assertEqual(stderr.calls, 0)

    def test_matching_queued_terminal_wins_before_closed_process_poll(self):
        process = Process(0)
        terminal = {"event": "terminal", "id": "wanted"}
        wait, latest = extract_wait(process, [terminal])
        self.assertIs(wait(lambda row: row.get("id") == "wanted"), terminal)
        self.assertEqual(process.poll_calls, 0)
        self.assertEqual(process.stderr.calls, 0)

    def test_observation_updates_latest_before_matching_terminal(self):
        observation = {"event": "observation", "sequence": 7}
        terminal = {"event": "terminal", "id": "wanted"}
        wait, latest = extract_wait(Process(None), [observation, terminal])
        self.assertIs(wait(lambda row: row.get("id") == "wanted"), terminal)
        self.assertIs(latest(), observation)

    def test_policy_invalidation_precedes_matching_predicate(self):
        observation = {"event": "observation", "sequence": 7}
        invalidation = {"reason": "health_decline"}
        monitor = types.SimpleNamespace(observe=lambda row: invalidation)
        wait, latest = extract_wait(Process(None), [observation])
        result = wait(lambda row: True, observation_monitor=monitor)
        self.assertEqual(result["event"], "policy_invalidation")
        self.assertIs(result["invalidation"], invalidation)
        self.assertIs(latest(), observation)

    def test_running_invalidation_retains_typed_event_and_result(self):
        typed = {"event": "typed_observation", "sequence": 9}
        invalidation = {"event": "running_action_invalidation", "reason": "authority_revoked"}
        seen = []
        def observe(row):
            seen.append(row)
            return invalidation
        monitor = types.SimpleNamespace(event_types={"typed_observation"}, observe=observe)
        wait, latest = extract_wait(Process(None), [typed])
        self.assertIs(wait(lambda row: True, observation_monitor=monitor), invalidation)
        self.assertEqual(seen, [typed])
        self.assertIsNone(latest())

    def test_live_session_empty_queue_reaches_existing_timeout(self):
        process = Process(None)
        wait, latest = extract_wait(process, [])
        with self.assertRaises(TimeoutError):
            wait(lambda row: False, timeout=.025)
        self.assertEqual(process.stderr.calls, 0)
        self.assertIsNone(latest())

    def test_matching_soft_event_frame_is_forwarded_once_to_active_handle(self):
        handle = object()
        calls = []
        def forward(planner, active_handle, observation, event):
            calls.append((active_handle, observation, event))
            return {"outcome": "attached", "sequence": observation["sequence"]}
        typed = {"event": "typed_observation", "sequence": 12}
        full = {"event": "observation", "sequence": 12}
        duplicate = {"event": "observation", "sequence": 12}
        terminal = {"event": "terminal", "id": "wanted"}
        monitor = types.SimpleNamespace(event_types={"typed_observation", "observation"},
                                        latest_soft_event=None)
        def observe(row):
            if row["event"] == "typed_observation":
                monitor.latest_soft_event = {"sequence": 12, "signal": {"value": 75}}
            return None
        monitor.observe = observe
        wait, latest = extract_wait(
            Process(None), [typed, full, duplicate, terminal], handle=handle, forward=forward)
        result = wait(lambda row: row.get("id") == "wanted",
                      observation_monitor=monitor)
        self.assertIs(result, terminal)
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], handle)
        self.assertIs(calls[0][1], full)
        self.assertIs(calls[0][2], monitor.latest_soft_event)
        self.assertEqual(wait.active_observation_delivery(),
                         {"iteration": 3, "outcome": "attached", "sequence": 12})


if __name__ == "__main__":
    unittest.main()
