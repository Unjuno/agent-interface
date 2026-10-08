"""Regression for a soft observation making a pending cover renewal stale."""
import ast
import json
import os
import queue
import time
import unittest
from pathlib import Path

SOURCE = Path(os.environ.get(
    "V39_CONTROLLER_SOURCE", Path(__file__).with_name("map01_overlap_controller_v39.py")))


def load_controller_function(name):
    tree = ast.parse(SOURCE.read_text())
    node = next((item for item in tree.body
                 if isinstance(item, ast.FunctionDef) and item.name == name), None)
    if node is None:
        raise AssertionError(f"V39 lacks tested function {name}")
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    scope = {"queue": queue, "time": time,
             "STALE_SEQUENCE_REJECTION_REASON":
                 "latest observation sequence required before input"}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope[name]


def load_current_wait_and_submit(rows, process, monitor):
    tree = ast.parse(SOURCE.read_text())
    main = next(item for item in tree.body
                if isinstance(item, ast.FunctionDef) and item.name == "main")
    nested = {item.name: item for item in ast.walk(main)
              if isinstance(item, ast.FunctionDef) and
              item.name in {"wait", "submit_cover"}}
    if set(nested) != {"wait", "submit_cover"}:
        raise AssertionError("V39 main lacks wait or submit_cover")
    factory = ast.parse(
        "def factory(process, incoming, observation_monitor):\n"
        "    latest = {'sequence': 7}\n"
        "    clock_ns = 0\n"
        "    cover_steps = [{'op': 'observe'}]\n"
        "    cover_ids = []\n"
        "    all_events = []\n"
        "    reader_errors = []\n"
        "    validity_monitor = observation_monitor\n"
    ).body[0]
    factory.body.extend([nested["wait"], nested["submit_cover"]])
    factory.body.extend(ast.parse(
        "return submit_cover, lambda: latest, lambda: cover_ids, lambda: process.stdin.writes"
    ).body)
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"queue": queue, "time": time, "json": json}
    exec(compile(module, str(SOURCE), "exec"), scope)
    incoming = queue.Queue()
    for row in rows:
        incoming.put(row)
    return scope["factory"](process, incoming, monitor)


class Stdin:
    def __init__(self):
        self.writes = []

    def write(self, value):
        self.writes.append(value)

    def flush(self):
        pass


class Process:
    def __init__(self):
        self.stdin = Stdin()

    def poll(self):
        return None


class Monitor:
    event_types = {"observation"}

    def __init__(self, invalidation=None):
        self.invalidation = invalidation
        self.seen = []

    def observe(self, row):
        self.seen.append(row)
        return self.invalidation


class Planner:
    def __init__(self):
        self.interrupts = []

    def interrupt(self, handle):
        receipt = {"outcome": "requested", "turn_id": handle}
        self.interrupts.append(receipt)
        return receipt


class SoftStaleRenewalTests(unittest.TestCase):
    def test_accepted_renewal_is_still_classified_as_admitted(self):
        classify = load_controller_function("classify_cover_renewal_response")
        self.assertEqual(classify({"event": "accepted"}), {"status": "accepted"})

    def test_soft_observation_then_stale_sequence_rejection_is_no_cover_not_session_failure(self):
        process = Process()
        monitor = Monitor()
        rejection = {"event": "rejected",
                     "reason": "latest observation sequence required before input"}
        submit, latest, cover_ids, writes = load_current_wait_and_submit([
            {"event": "observation", "sequence": 8}, rejection], process, monitor)

        response = submit("cover-renew-1", allow_rejection=True)
        outcome = load_controller_function("classify_cover_renewal_response")(response)

        self.assertEqual(latest(), {"event": "observation", "sequence": 8})
        self.assertEqual(response, rejection)
        self.assertEqual(outcome, {"status": "stale_sequence_no_cover",
                                   "reason": rejection["reason"]})
        self.assertEqual(cover_ids(), [])
        self.assertEqual(json.loads(writes()[0])["expected_sequence"], 7)

    def test_unexpected_renewal_rejection_still_fails_closed(self):
        response = {"event": "rejected", "reason": "invalid program"}
        classify = load_controller_function("classify_cover_renewal_response")
        with self.assertRaises(RuntimeError) as caught:
            classify(response)
        self.assertEqual(caught.exception.args, (response,))

    def test_coverless_wait_keeps_planner_alive_on_soft_event_and_interrupts_on_hard_change(self):
        planner = Planner()
        soft_monitor = Monitor()
        soft_process = Process()
        soft_rows = [{"event": "observation", "sequence": 9}]
        # Extract the exact current V39 wait closure without importing GUI/model dependencies.
        tree = ast.parse(SOURCE.read_text())
        main = next(item for item in tree.body
                    if isinstance(item, ast.FunctionDef) and item.name == "main")
        nested = {item.name: item for item in ast.walk(main)
                  if isinstance(item, ast.FunctionDef) and item.name in {"wait", "submit_cover"}}
        incoming = queue.Queue()
        incoming.put(soft_rows[0])
        factory = ast.parse(
            "def factory(process, incoming, observation_monitor):\n"
            "    latest = None\n    all_events = []\n    reader_errors = []\n"
        ).body[0]
        factory.body.append(nested["wait"])
        factory.body.extend(ast.parse("return wait").body)
        module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
        scope = {"queue": queue, "time": time}
        exec(compile(module, str(SOURCE), "exec"), scope)
        wait = scope["factory"](soft_process, incoming, soft_monitor)
        coverless = load_controller_function("wait_without_active_cover")

        self.assertIsNone(coverless(wait, soft_monitor, planner, "turn-2"))
        self.assertEqual(planner.interrupts, [])
        self.assertEqual(soft_monitor.seen, [soft_rows[0]])

        invalidation = {"reason": "health_below_floor"}
        hard_monitor = Monitor(invalidation)
        hard_process = Process()
        hard_incoming = queue.Queue()
        hard_incoming.put({"event": "observation", "sequence": 10})
        hard_factory = ast.parse(
            "def factory(process, incoming, observation_monitor):\n"
            "    latest = None\n    all_events = []\n    reader_errors = []\n"
        ).body[0]
        hard_factory.body.append(nested["wait"])
        hard_factory.body.extend(ast.parse("return wait").body)
        hard_module = ast.fix_missing_locations(ast.Module(body=[hard_factory], type_ignores=[]))
        hard_scope = {"queue": queue, "time": time}
        exec(compile(hard_module, str(SOURCE), "exec"), hard_scope)
        hard_wait = hard_scope["factory"](hard_process, hard_incoming, hard_monitor)
        boundary = coverless(hard_wait, hard_monitor, planner, "turn-2")
        self.assertEqual(boundary["invalidation"], invalidation)
        self.assertEqual(boundary["planner_interrupt"], {
            "outcome": "requested", "turn_id": "turn-2"})
        self.assertEqual(len(planner.interrupts), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
