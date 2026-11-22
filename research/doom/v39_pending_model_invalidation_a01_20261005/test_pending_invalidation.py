"""Compose current-main V39 invalidation with a pending planner future.

No game, model client, GUI, OS input, or live allocation is used.
"""
import ast
import hashlib
import inspect
import json
import queue
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
DOOM = HERE.parent
sys.path.insert(0, str(DOOM))
sys.path.insert(0, str(DOOM.parent / "live_control"))
import map01_overlap_controller_v39 as controller


class Reader:
    def __init__(self, rows):
        self.rows = rows

    def read(self, row):
        return self.rows[row["sequence"]]


class Process:
    def __init__(self):
        self.stdin = self
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def flush(self):
        pass

    def poll(self):
        return None


def extract_production_wait(incoming, process):
    tree = ast.parse(inspect.getsource(controller))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    wait = next(node for node in ast.walk(main)
                if isinstance(node, ast.FunctionDef) and node.name == "wait")
    factory = ast.parse("def factory(incoming, process):\n latest = None\n").body[0]
    factory.body.append(wait)
    factory.body += ast.parse("return wait\n").body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"queue": queue, "time": time}
    exec(compile(module, "<current-main-v39-wait>", "exec"), scope)
    return scope["factory"](incoming, process)


def extract_pending_planner_loop():
    tree = ast.parse(inspect.getsource(controller))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    loops = [node for node in ast.walk(main) if isinstance(node, ast.While)
             and isinstance(node.test, ast.UnaryOp)
             and isinstance(node.test.op, ast.Not)
             and isinstance(node.test.operand, ast.Call)
             and isinstance(node.test.operand.func, ast.Attribute)
             and isinstance(node.test.operand.func.value, ast.Name)
             and node.test.operand.func.value.id == "future"
             and node.test.operand.func.attr == "done"]
    if len(loops) != 1:
        raise RuntimeError(f"expected one pending-future loop, found {len(loops)}")
    result_statement = ast.parse("planner_result = future.result()\n").body[0]
    return loops[0], result_statement


def paired_health_ammo_monitor():
    binding = {"focus": 7, "surface": 9, "geometry": [0, 0, 640, 480]}

    def signal(name, value, seq, captured):
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": name, "value": value, "sequence": seq,
                "capture_ns": captured, "binding": binding}

    source = {"event": "observation", "sequence": 10,
              "capture_ns": 1_000_000_000, "pointer_binding": binding}
    fresh = {"event": "typed_observation", "sequence": 11,
             "capture_ns": 1_100_000_000, "pointer_binding": binding,
             "signals": {"health": signal("health", 80, 11, 1_100_000_000),
                         "ammo": signal("ammo", 4, 11, 1_100_000_000)}}
    health = Reader({10: signal("health", 100, 10, 1_000_000_000),
                     11: fresh["signals"]["health"]})
    ammo = Reader({10: signal("ammo", 4, 10, 1_000_000_000),
                   11: fresh["signals"]["ammo"]})
    monitor, admission = controller.build_cover_monitor(
        health, source,
        {"signal_id": "health", "critical_health_minimum": 35,
         "maximum_health_loss": 12, "max_source_age_ms": 30000},
        0, ammo_reader=ammo, requires_ammo=True)
    if admission["status"] != "admitted":
        raise RuntimeError("fixture fire cover did not admit")
    return monitor, fresh


class PendingInvalidationTests(unittest.TestCase):
    def test_paired_invalidation_wins_pending_model_race_and_gates_answer(self):
        monitor, fresh = paired_health_ammo_monitor()
        # Observe only during the real production wait path, as the main loop does.
        incoming = queue.Queue()
        process = Process()
        wait = extract_production_wait(incoming, process)

        class Planner:
            def __init__(self):
                self.interrupted = []
                self.release = threading.Event()
                self.started = threading.Event()
                self.answer_return_ns = None

            def await_turn(self, handle, timeout):
                self.started.set()
                if not self.release.wait(timeout):
                    raise TimeoutError("test planner was not interrupted")
                self.answer_return_ns = time.perf_counter_ns()
                return SimpleNamespace(
                    handle=handle, status="completed", answer_eligible=True,
                    answer={"state": "active", "commands": [{"action": "forward"}]})

            def interrupt(self, handle):
                self.interrupted.append(handle.turn_id)
                self.release.set()
                return {"status": "interrupt_requested"}

        planner = Planner()
        handle = SimpleNamespace(turn_id="planner-0")
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(planner.await_turn, handle, 5)
        current_cover = "cover-0"
        current_terminal = None
        invalidation_result = None
        planner_interrupt = None
        cover_terminals = []
        env = {
            "future": future, "wait": wait, "invalidation_monitor": monitor,
            "planner": planner, "planner_handle": handle, "process": process,
            "current_cover": current_cover, "current_terminal": current_terminal,
            "invalidation": invalidation_result, "planner_interrupt": planner_interrupt,
            "cover_terminals": cover_terminals,
            "cancel_invalidated_cover": controller.cancel_invalidated_cover,
            "TimeoutError": TimeoutError,
        }
        loop, result_statement = extract_pending_planner_loop()
        tree = ast.fix_missing_locations(ast.Module(
            body=[loop, result_statement], type_ignores=[]))
        self.assertTrue(planner.started.wait(1), "planner never entered pending await")
        incoming.put(fresh)
        incoming.put({"event": "terminal", "id": "cover-0", "status": "cancelled",
                      "release": {"verified": True, "keys_down": [],
                                  "buttons_down": []}})
        try:
            exec(compile(tree, "<current-main-pending-model-loop>", "exec"), env)
        finally:
            pool.shutdown(wait=True)

        result = env["planner_result"]
        self.assertTrue(result.answer_eligible)
        self.assertEqual(env["invalidation"]["reason"], "health:below_hard_minimum")
        self.assertEqual(planner.interrupted, ["planner-0"])
        self.assertEqual(env["planner_interrupt"]["status"], "interrupt_requested")
        self.assertEqual(env["current_terminal"]["status"], "cancelled")
        self.assertEqual(env["current_terminal"]["release"], {
            "verified": True, "keys_down": [], "buttons_down": []})
        self.assertEqual(len(env["cover_terminals"]), 1)
        cancel = json.loads(process.writes[0])
        self.assertEqual(cancel, {"op": "cancel", "id": "cover-0"})

        admission = controller.final_admission_from_planner_result(
            result, env["invalidation"]["outcome_evaluated_ns"],
            env["invalidation"], time.perf_counter_ns() + 1_000)
        self.assertEqual(admission["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertFalse(admission["input_authority_admitted"])
        self.assertIsNone(admission["executor_admission"])
        self.assertGreaterEqual(planner.answer_return_ns,
                                env["invalidation"]["outcome_evaluated_ns"])

        raw = {
            "source_path": "research/doom/map01_overlap_controller_v39.py",
            "source_sha256": hashlib.sha256(
                (DOOM / "map01_overlap_controller_v39.py").read_bytes()).hexdigest(),
            "fresh_sequence": fresh["sequence"],
            "invalidation_reason": env["invalidation"]["reason"],
            "planner_started_before_invalidation": planner.started.is_set(),
            "planner_answer_eligible_after_interrupt": result.answer_eligible,
            "answer_return_ns": planner.answer_return_ns,
            "invalidation_evaluated_ns": env["invalidation"]["outcome_evaluated_ns"],
            "planner_interrupt": env["planner_interrupt"],
            "cancel_request": cancel,
            "terminal": env["current_terminal"],
            "final_admission": admission,
            "formal_allocation_invocations": 0,
            "game_model_gui_os_input": False,
        }
        out = HERE / ("raw-optimized.json" if sys.flags.optimize else "raw-normal.json")
        out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n",
                       encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
