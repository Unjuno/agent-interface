"""Compose pending-planner invalidation with neutral cover terminal races.

Construction-only: no game, model client, GUI, OS input, or live allocation.
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

    def run_reader(self):
        pass


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
    scope = {"queue": queue, "time": time, "failure_cleanup": SimpleNamespace(
        observe_output=lambda *args: None, set_stage=lambda *args: None)}
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
    loop = loops[0]
    # The production branch depends on iteration-level locals initialized before
    # the wait. Seed the wait at a fresh boundary to isolate the pending race.
    statement = ast.parse("""while not future.done():
    boundary = wait(lambda r: r[\"event\"] == \"terminal\" and r.get(\"id\") == current_cover,
                    timeout=.1, observation_monitor=invalidation_monitor)
    if boundary[\"event\"] == \"policy_invalidation\":
        invalidation = boundary[\"invalidation\"]
        planner_interrupt, current_terminal = cancel_invalidated_cover(
            planner, planner_handle, process, wait, current_cover)
        cover_terminals.append(current_terminal)
        break
    current_terminal = boundary
    cover_terminals.append(current_terminal)
    if future.done():
        break
    next_cover = f\"cover-{index}-renew-{len(cover_ids)}\"
    next_accepted = submit_cover(next_cover)
    cover_renewal_gaps_ms.append((next_accepted[\"accepted_ns\"] -
                                  current_terminal[\"terminal_ns\"]) / 1e6)
    current_cover = next_cover
    current_terminal = None
planner_result = future.result()
""").body
    return None, statement


def health_monitor():
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
    readers = {name: Reader({10: signal(name, value, 10, 1_000_000_000),
                             11: fresh["signals"][name]})
               for name, value in (("health", 100), ("ammo", 4))}
    monitor, admission = controller.build_cover_monitor(
        readers["health"], source,
        {"signal_id": "health", "critical_health_minimum": 35,
         "maximum_health_loss": 12, "max_source_age_ms": 30000}, 0,
        ammo_reader=readers["ammo"], requires_ammo=True)
    if admission["status"] != "admitted":
        raise RuntimeError("fixture cover did not admit")
    return monitor, fresh


class PendingNeutralTerminalTests(unittest.TestCase):
    def test_pending_answer_discarded_for_cancel_completed_and_expired(self):
        source_sha = hashlib.sha256((DOOM / "map01_overlap_controller_v39.py").read_bytes()).hexdigest()
        evidence = []
        for terminal_status in ("cancelled", "completed", "expired"):
            with self.subTest(terminal_status=terminal_status):
                monitor, fresh = health_monitor()
                incoming, process = queue.Queue(), Process()
                wait = extract_production_wait(incoming, process)

                class Planner:
                    def __init__(self):
                        self.release = threading.Event()
                        self.started = threading.Event()
                        self.interrupted = []
                        self.answer_return_ns = None

                    def await_turn(self, handle, timeout):
                        self.started.set()
                        if not self.release.wait(timeout):
                            raise TimeoutError("planner was not interrupted")
                        self.answer_return_ns = time.perf_counter_ns()
                        return SimpleNamespace(handle=handle, status="completed",
                            answer_eligible=True,
                            answer={"state": "active", "commands": [{"action": "forward"}]})

                    def interrupt(self, handle):
                        self.interrupted.append(handle.turn_id)
                        self.release.set()
                        return {"status": "interrupt_requested"}

                planner, handle = Planner(), SimpleNamespace(turn_id="planner-0")
                pool = ThreadPoolExecutor(max_workers=1)
                future = pool.submit(planner.await_turn, handle, 5)
                terminal = {"event": "terminal", "id": "cover-0", "status": terminal_status,
                            "release": {"verified": True, "keys_down": [], "buttons_down": []}}
                env = {"future": future, "wait": wait, "invalidation_monitor": monitor,
                    "planner": planner, "planner_handle": handle, "process": process,
                    "current_cover": "cover-0", "current_terminal": None,
                    "index": 0, "cover_ids": ["cover-0"], "cover_renewal_gaps_ms": [],
                    "boundary": {"event": "terminal", "id": "cover-0",
                                 "status": terminal_status,
                                 "release": {"verified": True, "keys_down": [],
                                             "buttons_down": []}},
                    "timeout": 0.1,
                    "invalidation": None, "planner_interrupt": None, "cover_terminals": [],
                    "cancel_invalidated_cover": controller.cancel_invalidated_cover,
                    "TimeoutError": TimeoutError}
                _, result_statement = extract_pending_planner_loop()
                tree = ast.fix_missing_locations(ast.Module(body=result_statement, type_ignores=[]))
                self.assertTrue(planner.started.wait(1), "planner did not enter pending await")
                incoming.put(fresh)
                incoming.put(terminal)
                try:
                    exec(compile(tree, "<current-main-pending-model-loop>", "exec"), env)
                finally:
                    pool.shutdown(wait=True)

                result = env["planner_result"]
                self.assertEqual(env["invalidation"]["reason"], "health:below_hard_minimum")
                self.assertEqual(planner.interrupted, ["planner-0"])
                self.assertIs(env["current_terminal"], terminal)
                self.assertEqual(len(env["cover_terminals"]), 1)
                self.assertEqual(json.loads(process.writes[0]), {"op": "cancel", "id": "cover-0"})
                admission = controller.final_admission_from_planner_result(
                    result, env["invalidation"]["outcome_evaluated_ns"],
                    env["invalidation"], time.perf_counter_ns() + 1000)
                self.assertEqual(admission["status"], "REJECTED_POLICY_INVALIDATED")
                self.assertFalse(admission["input_authority_admitted"])
                self.assertIsNone(admission["executor_admission"])
                self.assertGreaterEqual(planner.answer_return_ns,
                                        env["invalidation"]["outcome_evaluated_ns"])
                evidence.append({"terminal_status": terminal_status,
                    "invalidation_reason": env["invalidation"]["reason"],
                    "answer_eligible_after_interrupt": result.answer_eligible,
                    "planner_interrupt": "interrupt_requested",
                    "cancel_request": json.loads(process.writes[0]),
                    "release": terminal["release"], "final_admission": admission["status"],
                    "input_authority_admitted": admission["input_authority_admitted"]})

        out = HERE / ("raw-optimized.json" if sys.flags.optimize else "raw-normal.json")
        out.write_text(json.dumps({"source_path": "research/doom/map01_overlap_controller_v39.py",
            "source_sha256": source_sha, "cases": evidence,
            "formal_allocation_invocations": 0, "game_model_gui_os_input": False},
            sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
