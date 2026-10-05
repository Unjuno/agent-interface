"""Stdlib regressions for v39's nested wait; no game/backend/client import."""
import ast
import io
import json
import os
from pathlib import Path
import queue
import time
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


def extract_submit_cover(process, wait, latest, cover_steps, validity_monitor, cover_ids):
    tree = ast.parse(SOURCE.read_bytes())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "main")
    submit_cover = next(node for node in ast.walk(main)
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "submit_cover")
    factory = ast.parse(
        "def factory(process, wait, latest, cover_steps, validity_monitor, cover_ids):\n"
        "    clock_ns = 0\n").body[0]
    factory.body.append(submit_cover)
    factory.body += ast.parse("return submit_cover\n").body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"json": json, "time": time}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope["factory"](process, wait, latest, cover_steps,
                            validity_monitor, cover_ids)


def extract_top_level_function(name):
    tree = ast.parse(SOURCE.read_bytes())
    function = next((node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == name), None)
    if function is None:
        return None
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    scope = {"json": json}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope[name]


def extract_renewal_invalidation_branch():
    tree = ast.parse(SOURCE.read_bytes())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "main")
    branch = next(node for node in ast.walk(main)
                  if isinstance(node, ast.If) and
                  any(isinstance(child, ast.Name) and child.id == "next_accepted"
                      for child in ast.walk(node.test)) and
                  "policy_invalidation" in ast.dump(node.test))
    resolver = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "resolve_invalidated_cover_submission")
    cancel = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "cancel_invalidated_cover")
    factory = ast.parse(
        "def factory(next_accepted, next_cover, planner, planner_handle, process, wait, "
        "cover_terminals, cover_ids, current_cover, current_terminal):\n"
        "    invalidation = None\n    planner_interrupt = None\n"
        "    renewal_admission_resolution = None\n").body[0]
    factory.body = [ast.While(test=ast.Constant(value=True), body=[branch], orelse=[])]
    factory.body += ast.parse(
        "return (invalidation, current_cover, planner_interrupt, current_terminal, "
        "cover_terminals, cover_ids, renewal_admission_resolution)\n").body
    module = ast.fix_missing_locations(ast.Module(body=[resolver, cancel, factory], type_ignores=[]))
    scope = {"json": json}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope["factory"]


def extract_initial_cover_gate():
    tree = ast.parse(SOURCE.read_bytes())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "main")
    loop = next(node for node in ast.walk(main) if isinstance(node, ast.For)
                and any(isinstance(child, ast.FunctionDef)
                        and child.name == "submit_cover" for child in node.body))
    submit_cover = next(child for child in loop.body
                        if isinstance(child, ast.FunctionDef)
                        and child.name == "submit_cover")
    assignment = next(stmt for stmt in loop.body if isinstance(stmt, ast.Assign)
                      and any(isinstance(target, ast.Name)
                              and target.id == "initial_cover_admission"
                              for target in stmt.targets))
    gate = next(stmt for stmt in loop.body if isinstance(stmt, ast.If)
                and any(isinstance(node, ast.Name)
                        and node.id == "initial_cover_admission"
                        for node in ast.walk(stmt.test)))
    cancel = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "cancel_invalidated_cover_before_plan")
    resolve = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == "resolve_invalidated_cover_submission")
    factory = ast.parse(
        "def factory(process, wait, latest, cover_steps, validity_monitor, "
        "validity_admission, cover_semantic, cover_policy_source_iteration, "
        "model_session_id, failure_cleanup):\n"
        "    clock_ns = 0\n"
        "    cover = 'cover-0'\n"
        "    cover_ids = []\n"
        "    cover_terminals = []\n"
        "    cover_renewal_gaps_ms = []\n"
        "    decisions = []\n"
        "    effect_memory = []\n"
        "    prior_soft_event_summary = None\n"
        "    planner_started = False\n").body[0]
    factory.body.extend([submit_cover, cancel, resolve])
    factory.body.append(ast.For(
        target=ast.Name(id="index", ctx=ast.Store()),
        iter=ast.Call(func=ast.Name(id="range", ctx=ast.Load()),
                      args=[ast.Constant(value=1)], keywords=[]),
        body=[assignment, gate,
              ast.parse("planner_started = True").body[0]], orelse=[]))
    factory.body += ast.parse(
        "return planner_started, decisions, cover_ids, cover_terminals\n").body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"json": json, "time": time,
             "latest_soft_event_summary": lambda _decisions: None}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope["factory"]


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

    def test_initial_cover_admission_observes_invalidation_before_acceptance(self):
        observation = {"event": "observation", "sequence": 8, "health": 70}
        accepted = {"event": "accepted", "id": "cover-0", "accepted_ns": 123}
        invalidation = {"reason": "health_below_floor", "sequence": 8}
        monitor = types.SimpleNamespace(
            event_types={"observation"},
            observe=lambda row: invalidation if row is observation else None)
        process = types.SimpleNamespace(stdin=io.StringIO())
        wait, latest = extract_wait(Process(None), [observation, accepted])
        cover_ids = []
        submit_cover = extract_submit_cover(
            process, wait, {"sequence": 7}, [{"op": "wait"}], monitor, cover_ids)

        result = submit_cover("cover-0")

        self.assertEqual(result, {"event": "policy_invalidation",
                                  "invalidation": invalidation})
        self.assertIs(latest(), observation)
        self.assertEqual(cover_ids, [])

    def test_invalidated_initial_cover_waits_for_verified_release_and_terminal(self):
        rows = [
            {"event": "cancel_requested", "id": "cover-0", "matched": True},
            {"event": "input_released", "id": "cover-0",
             "intent_token": "intent-1", "program_terminal_pending": True,
             "grants_input_authority": False,
             "owner_release": {"verified": True, "keys_down": [], "buttons_down": []}},
            {"event": "terminal", "id": "cover-0", "status": "cancelled",
             "release": {"verified": True, "keys_down": [], "buttons_down": []}},
        ]
        seen = []
        def wait(predicate):
            row = rows.pop(0)
            self.assertTrue(predicate(row))
            seen.append(row["event"])
            return row
        process = types.SimpleNamespace(stdin=io.StringIO())
        cancel = extract_top_level_function("cancel_invalidated_cover_before_plan")
        self.assertIsNotNone(cancel, "initial-cover cancellation helper is missing")

        receipt = cancel(process, wait, "cover-0")

        self.assertEqual(seen, ["cancel_requested", "input_released", "terminal"])
        self.assertEqual(json.loads(process.stdin.getvalue()),
                         {"op": "cancel", "id": "cover-0"})
        self.assertTrue(receipt["terminal"]["release"]["verified"])

    def test_invalidated_initial_cover_refuses_unverified_owner_release(self):
        rows = [
            {"event": "cancel_requested", "id": "cover-0", "matched": True},
            {"event": "input_release_unverified", "id": "cover-0",
             "program_terminal_pending": True, "grants_input_authority": False,
             "owner_release": {"verified": False, "keys_down": [32],
                               "buttons_down": []}},
            {"event": "terminal", "id": "cover-0", "status": "cancelled",
             "release": {"verified": True, "keys_down": [], "buttons_down": []}},
        ]
        def wait(predicate):
            row = rows.pop(0)
            self.assertTrue(predicate(row))
            return row
        cancel = extract_top_level_function("cancel_invalidated_cover_before_plan")
        process = types.SimpleNamespace(stdin=io.StringIO())

        with self.assertRaisesRegex(RuntimeError, "did not verify empty release"):
            cancel(process, wait, "cover-0")

    def test_initial_cover_invalidation_cancels_and_skips_planner_turn(self):
        observation = {"event": "observation", "sequence": 8, "health": 70,
                       "image": "fresh.png"}
        invalidation = {"reason": "health_below_floor", "sequence": 8}
        rows = [observation,
                {"event": "accepted", "id": "cover-0", "accepted_ns": 123},
                {"event": "cancel_requested", "id": "cover-0", "matched": True},
                {"event": "input_released", "id": "cover-0",
                 "intent_token": "intent-1", "program_terminal_pending": True,
                 "grants_input_authority": False,
                 "owner_release": {"verified": True, "keys_down": [],
                                   "buttons_down": []}},
                {"event": "terminal", "id": "cover-0", "status": "cancelled",
                 "release": {"verified": True, "keys_down": [], "buttons_down": []}}]
        monitor = types.SimpleNamespace(
            event_types={"observation"}, soft_event_count=0, latest_soft_event=None,
            observe=lambda row: invalidation if row is observation else None)
        process = types.SimpleNamespace(stdin=io.StringIO())
        wait_impl, observed_latest = extract_wait(Process(None), rows)
        latest = {"sequence": 7, "image": "stale.png"}
        def wait(predicate, timeout=40, observation_monitor=None):
            result = wait_impl(predicate, timeout=timeout,
                               observation_monitor=observation_monitor)
            if observed_latest() is not None:
                latest.update(observed_latest())
            return result
        failure_cleanup = types.SimpleNamespace(set_stage=lambda _stage: None)

        planner_started, decisions, cover_ids, cover_terminals = extract_initial_cover_gate()(
            process, wait, latest,
            [{"op": "wait"}], monitor, {"status": "admitted"}, [], None,
            "thread-1", failure_cleanup)

        self.assertFalse(planner_started)
        self.assertEqual(cover_ids, ["cover-0"])
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["planner_turn_status"], "not_started")
        self.assertFalse(decisions[0]["model_action_discarded"])
        self.assertEqual(decisions[0]["initial_cover_submission_id"], "cover-0")
        self.assertEqual(decisions[0]["source_image"], "fresh.png")
        self.assertEqual(decisions[0]["initial_cover_admission_result"]["event"],
                         "policy_invalidation")
        self.assertEqual(cover_terminals[0]["status"], "cancelled")

    def test_rejected_initial_submission_is_not_cancelled_as_an_admitted_program(self):
        observation = {"event": "observation", "sequence": 8, "health": 70,
                       "image": "fresh.png"}
        invalidation = {"reason": "health_below_floor", "sequence": 8}
        rows = [observation,
                {"event": "rejected", "reason": "latest observation sequence required before input"},
                {"event": "cancel_requested", "id": "cover-0", "matched": False}]
        monitor = types.SimpleNamespace(
            event_types={"observation"}, soft_event_count=0, latest_soft_event=None,
            observe=lambda row: invalidation if row is observation else None)
        process = types.SimpleNamespace(stdin=io.StringIO())
        wait_impl, observed_latest = extract_wait(Process(None), rows)
        latest = {"sequence": 7, "image": "stale.png"}
        def wait(predicate, timeout=40, observation_monitor=None):
            result = wait_impl(predicate, timeout=timeout,
                               observation_monitor=observation_monitor)
            if observed_latest() is not None:
                latest.update(observed_latest())
            return result
        failure_cleanup = types.SimpleNamespace(set_stage=lambda _stage: None)

        planner_started, decisions, cover_ids, cover_terminals = extract_initial_cover_gate()(
            process, wait, latest, [{"op": "wait"}], monitor,
            {"status": "admitted"}, [], None, "thread-1", failure_cleanup)

        self.assertFalse(planner_started)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["initial_cover_admission_resolution"]["status"],
                         "rejected")
        self.assertEqual(decisions[0]["initial_cover_admission_resolution"]["response"],
                         {"event": "rejected",
                          "reason": "latest observation sequence required before input"})
        self.assertIsNone(decisions[0]["cover_admission_cancellation"])
        self.assertFalse(decisions[0]["cover_program_admitted"])
        self.assertFalse(decisions[0]["cover_terminal_before_plan"])
        self.assertEqual(cover_ids, [])
        self.assertEqual(cover_terminals, [])
        writes = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
        self.assertEqual([row["op"] for row in writes], ["submit"])

    def test_renewal_invalidation_interrupts_before_accepted_ack_and_reuses_receipt(self):
        trace = []
        accepted = {"event": "accepted", "id": "cover-renew-1", "accepted_ns": 100}
        terminal = {"event": "terminal", "id": "cover-renew-1", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}

        class Planner:
            def interrupt(self, handle):
                trace.append("interrupt")
                return {"status": "interrupted", "sequence": 1}

        class Stdin:
            def write(self, value): trace.append("write_cancel")
            def flush(self): pass

        def wait(predicate):
            row = accepted if "wait_ack" not in trace else terminal
            trace.append("wait_ack" if row is accepted else "wait_terminal")
            self.assertTrue(predicate(row))
            return row

        result = extract_renewal_invalidation_branch()(
            {"event": "policy_invalidation", "invalidation": {"reason": "health"}},
            "cover-renew-1", Planner(), object(), types.SimpleNamespace(stdin=Stdin()), wait,
            [{"event": "terminal", "id": "cover-0", "status": "expired",
              "release": {"verified": True, "keys_down": [], "buttons_down": []}}],
            ["cover-0"], "cover-0", None)

        self.assertEqual(trace[0], "interrupt")
        self.assertEqual(trace.count("interrupt"), 1)
        self.assertLess(trace.index("interrupt"), trace.index("wait_ack"))
        self.assertEqual(result[2], {"status": "interrupted", "sequence": 1})
        self.assertEqual(result[3], terminal)
        self.assertEqual(result[5], ["cover-0", "cover-renew-1"])
        self.assertEqual(result[6], {"status": "accepted", "response": accepted})

    def test_renewal_invalidation_interrupts_before_rejected_ack_without_cancel(self):
        trace = []
        rejected = {"event": "rejected", "reason": "stale_sequence"}

        class Planner:
            def interrupt(self, handle):
                trace.append("interrupt")
                return {"status": "interrupted", "sequence": 2}

        class Stdin:
            def write(self, value): trace.append("unexpected_write")
            def flush(self): pass

        def wait(predicate):
            trace.append("wait_ack")
            self.assertTrue(predicate(rejected))
            return rejected

        prior = {"event": "terminal", "id": "cover-0", "status": "expired",
                 "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        terminals, ids = [prior], ["cover-0"]
        result = extract_renewal_invalidation_branch()(
            {"event": "policy_invalidation", "invalidation": {"reason": "health"}},
            "cover-renew-1", Planner(), object(), types.SimpleNamespace(stdin=Stdin()), wait,
            terminals, ids, "cover-0", prior)

        self.assertEqual(trace, ["interrupt", "wait_ack"])
        self.assertEqual(result[2], {"status": "interrupted", "sequence": 2})
        self.assertIs(result[3], prior)
        self.assertEqual(terminals, [prior])
        self.assertEqual(ids, ["cover-0"])
        self.assertEqual(result[6], {"status": "rejected", "response": rejected})

    def test_soft_observation_stale_submit_is_recorded_without_aborting_controller(self):
        observation = {"event": "observation", "sequence": 8, "health": 99,
                       "image": "soft.png"}
        rejected = {"event": "rejected",
                    "reason": "latest observation sequence required before input"}
        monitor = types.SimpleNamespace(
            event_types={"observation"}, soft_event_count=1,
            latest_soft_event={"sequence": 8},
            observe=lambda row: None)
        process = types.SimpleNamespace(stdin=io.StringIO())
        wait_impl, observed_latest = extract_wait(Process(None), [observation, rejected])
        latest = {"sequence": 7, "image": "old.png"}
        def wait(predicate, timeout=40, observation_monitor=None):
            result = wait_impl(predicate, timeout=timeout,
                               observation_monitor=observation_monitor)
            if observed_latest() is not None:
                latest.update(observed_latest())
            return result
        failure_cleanup = types.SimpleNamespace(set_stage=lambda _stage: None)

        planner_started, decisions, cover_ids, cover_terminals = extract_initial_cover_gate()(
            process, wait, latest, [{"op": "wait"}], monitor,
            {"status": "admitted"}, [], None, "thread-1", failure_cleanup)

        self.assertFalse(planner_started)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["initial_cover_admission_resolution"]["status"],
                         "rejected")
        self.assertIsNone(decisions[0]["policy_invalidation"])
        self.assertEqual(decisions[0]["source_image"], "soft.png")
        self.assertEqual(decisions[0]["initial_cover_admission_resolution"]["response"],
                         rejected)
        self.assertEqual(cover_ids, [])
        self.assertEqual(cover_terminals, [])
        writes = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
        self.assertEqual([row["op"] for row in writes], ["submit"])

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

