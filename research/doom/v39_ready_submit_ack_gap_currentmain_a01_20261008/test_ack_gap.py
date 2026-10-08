"""Current-main V39 observation arriving during action-ack wait.

Uses the production nested wait function and statically checks its exact caller.
No executor process, GUI, game, model, or OS input is started.
"""
import ast
import inspect
import json
import queue
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
DOOM = HERE.parent
sys.path.insert(0, str(DOOM))
sys.path.insert(0, str(DOOM.parent / "live_control"))
import map01_overlap_controller_v39 as controller


def production_wait():
    tree = ast.parse(inspect.getsource(controller))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    wait = next(n for n in ast.walk(main) if isinstance(n, ast.FunctionDef) and n.name == "wait")
    factory = ast.parse("def factory(incoming):\n latest = None\n").body[0]
    factory.body.append(wait)
    factory.body += ast.parse("return wait, lambda: latest\n").body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"queue": queue, "time": time}
    exec(compile(module, "<current-main-wait>", "exec"), scope)
    incoming = queue.Queue()
    wait, get_latest = scope["factory"](incoming)
    return wait, get_latest, incoming


def ack_wait_source_shape():
    tree = ast.parse(inspect.getsource(controller))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    execute = next(n for n in ast.walk(main)
                   if isinstance(n, ast.FunctionDef) and n.name == "execute_segment")
    ack_calls = []
    for node in ast.walk(execute):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "wait":
            continue
        if node.args and isinstance(node.args[0], ast.Lambda):
            text = ast.unparse(node.args[0])
            if "accepted" in text and "rejected" in text:
                ack_calls.append(node)
    if len(ack_calls) != 1:
        raise AssertionError(f"expected one action acceptance wait, found {len(ack_calls)}")
    return ack_calls[0]


def rejection_handler_raises():
    tree = ast.parse(inspect.getsource(controller))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    execute = next(n for n in ast.walk(main)
                   if isinstance(n, ast.FunctionDef) and n.name == "execute_segment")
    handlers = [n for n in ast.walk(execute) if isinstance(n, ast.If) and
                "accepted['event'] != 'accepted'" in ast.unparse(n.test)]
    return len(handlers) == 1 and any(isinstance(n, ast.Raise) for n in ast.walk(handlers[0]))


class MonitorSpy:
    event_types = {"typed_observation"}
    def __init__(self): self.rows = []
    def observe(self, row): self.rows.append(row); return None


class AckGapTests(unittest.TestCase):
    def test_ack_wait_consumes_fresh_typed_event_without_policy_monitor(self):
        wait, get_latest, incoming = production_wait()
        monitor = MonitorSpy()
        typed = {"event": "typed_observation", "sequence": 2,
                 "capture_ns": 2_000_000, "signals": {"health": {"value": 70}}}
        full = {"event": "observation", "sequence": 2, "capture_ns": 2_000_000}
        rejected = {"event": "rejected", "id": "plan-0", "reason": "latest observation sequence required before input"}
        for row in (typed, full, rejected): incoming.put(row)
        result = wait(lambda row: row["event"] in ("accepted", "rejected") and
                      (row.get("id") == "plan-0" or row["event"] == "rejected"),
                      observation_monitor=None)
        self.assertEqual(result, rejected)
        self.assertEqual(monitor.rows, [])
        self.assertEqual(get_latest(), full)
        ack = ack_wait_source_shape()
        self.assertFalse(any(keyword.arg == "observation_monitor" for keyword in ack.keywords))
        self.assertTrue(rejection_handler_raises())
        raw = {"source_path": "research/doom/map01_overlap_controller_v39.py",
               "source_sha256": __import__("hashlib").sha256(
                   (DOOM / "map01_overlap_controller_v39.py").read_bytes()).hexdigest(),
               "sequence": [1, 2], "event_order": [typed["event"], full["event"], rejected["event"]],
               "ack_result": result, "monitor_calls": len(monitor.rows),
               "controller_latest_after_ack": get_latest(),
               "executor_stale_rejection_reason": rejected["reason"],
               "executor_worker_start": False,
               "controller_rejection_handler": "raises RuntimeError",
               "controller_replan_after_rejection": False,
               "live_game_model_gui_os_input": False}
        out = HERE / ("raw-optimized.json" if sys.flags.optimize else "raw-normal.json")
        out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def test_production_executor_rejects_stale_sequence_before_worker_creation(self):
        source = inspect.getsource(controller)
        self.assertIn('wait(lambda r:r["event"] in ("accepted","rejected")', source)
        exec_path = DOOM.parent / "live_control" / "executor_v12.py"
        tree = ast.parse(exec_path.read_text(encoding="utf-8"))
        submit = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "submit")
        body = ast.unparse(submit)
        stale_check = body.index("expected_sequence != self.backend.sequence")
        worker = body.index("threading.Thread")
        self.assertLess(stale_check, worker)
        self.assertIn("latest observation sequence required before input", body)


if __name__ == "__main__": unittest.main(verbosity=2)
