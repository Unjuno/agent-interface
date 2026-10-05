"""Stdlib regressions for v39's nested wait; no game/backend/client import."""
import ast
import os
from pathlib import Path
import queue
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


def extract_wait(process, rows):
    tree = ast.parse(SOURCE.read_bytes())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    wait = next(node for node in ast.walk(main) if isinstance(node, ast.FunctionDef) and node.name == "wait")
    factory = ast.parse("def factory(process, incoming):\n latest = None\n").body[0]
    factory.body.append(wait)
    factory.body += ast.parse("return wait, lambda: latest").body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"queue": queue, "time": Clock()}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope["factory"](process, ScriptQueue(rows))


class WaitTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
