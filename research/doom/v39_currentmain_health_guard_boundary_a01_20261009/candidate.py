"""Current-main V39 health-guard boundary under a pending planner."""
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


BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 640, 480]}
SOURCE_CAPTURE_NS = 1_000_000_000


def signal(name, value, sequence, capture_ns):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": BINDING}


class Reader:
    def __init__(self, rows):
        self.rows = rows

    def read(self, row):
        return self.rows[row["sequence"]]


class Process:
    def __init__(self):
        self.stdin = self
        self.writes = []
        self.events = []

    def write(self, data):
        self.writes.append(data)
        self.events.append("executor_cancel")

    def flush(self):
        pass

    def poll(self):
        return None


class Planner:
    def __init__(self, process):
        self.process = process
        self.interrupted = []
        self.release = threading.Event()
        self.started = threading.Event()
        self.answer_return_ns = None

    def await_turn(self, handle, timeout):
        self.started.set()
        if not self.release.wait(timeout):
            raise TimeoutError("planner was not interrupted by the guard")
        self.answer_return_ns = time.perf_counter_ns()
        return SimpleNamespace(
            handle=handle, status="completed", answer_eligible=True,
            answer={"state": "active", "commands": [{"action": "forward"}]})

    def interrupt(self, handle, *, before_transport=None):
        self.interrupted.append(handle.turn_id)
        if before_transport is not None:
            before_transport()
        self.process.events.append("planner_interrupt")
        self.release.set()
        return {"status": "interrupt_requested"}


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


def make_observation(sequence, health):
    capture_ns = SOURCE_CAPTURE_NS + (sequence - 10) * 100_000_000
    return {
        "event": "typed_observation", "sequence": sequence,
        "capture_ns": capture_ns, "pointer_binding": BINDING,
        "frame_rgb_sha256": f"{sequence:064x}",
        "signals": {
            "health": signal("health", health, sequence, capture_ns),
            "ammo": signal("ammo", 4, sequence, capture_ns),
        },
    }


def run_case():
    source = {"event": "observation", "sequence": 10,
              "capture_ns": SOURCE_CAPTURE_NS, "pointer_binding": BINDING}
    observations = [make_observation(11, 89), make_observation(12, 88),
                    make_observation(13, 87)]
    health = Reader({10: signal("health", 100, 10, SOURCE_CAPTURE_NS),
                     **{row["sequence"]: row["signals"]["health"]
                        for row in observations}})
    ammo = Reader({10: signal("ammo", 4, 10, SOURCE_CAPTURE_NS),
                   **{row["sequence"]: row["signals"]["ammo"]
                      for row in observations}})
    monitor, admission_receipt = controller.build_cover_monitor(
        health, source,
        {"signal_id": "health", "critical_health_minimum": 35,
         "maximum_health_loss": 12, "max_source_age_ms": 30000},
        0, ammo_reader=ammo, requires_ammo=True)
    if admission_receipt["status"] != "admitted":
        raise AssertionError("authored source policy did not admit")
    if admission_receipt["effective"]["hard_minimum"] != 88:
        raise AssertionError("effective threshold is not the expected 88")

    incoming = queue.Queue()
    process = Process()
    wait = extract_production_wait(incoming, process)
    planner = Planner(process)
    handle = SimpleNamespace(turn_id="planner-0")
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(planner.await_turn, handle, 5)
    cover_terminals = []
    env = {
        "future": future, "wait": wait, "invalidation_monitor": monitor,
        "planner": planner, "planner_handle": handle, "process": process,
        "current_cover": "cover-0", "current_terminal": None,
        "invalidation": None, "planner_interrupt": None,
        "cover_terminals": cover_terminals,
        "cancel_invalidated_cover": controller.cancel_invalidated_cover,
        "TimeoutError": TimeoutError,
    }
    loop, result_statement = extract_pending_planner_loop()
    program = ast.fix_missing_locations(ast.Module(
        body=[loop, result_statement], type_ignores=[]))
    if not planner.started.wait(1):
        pool.shutdown(wait=True)
        raise AssertionError("planner did not enter pending wait")

    for row in observations:
        incoming.put(row)
    incoming.put({"event": "terminal", "id": "cover-0", "status": "cancelled",
                  "release": {"verified": True, "keys_down": [],
                              "buttons_down": []}})
    try:
        exec(compile(program, "<current-main-pending-model-loop>", "exec"), env)
    finally:
        pool.shutdown(wait=True)

    planner_result = env["planner_result"]
    invalidation = env["invalidation"]
    admission = controller.final_admission_from_planner_result(
        planner_result, invalidation["outcome_evaluated_ns"], invalidation,
        time.perf_counter_ns() + 1_000)
    if monitor.soft_event_count != 2:
        raise AssertionError("89 and exact-floor 88 were not retained as soft changes")
    if invalidation["reason"] != "health:below_hard_minimum":
        raise AssertionError("the 88 sample did not invalidate the active policy")
    if process.events != ["executor_cancel", "planner_interrupt"]:
        raise AssertionError("cover cancel did not precede planner interruption")
    if env["current_terminal"]["release"] != {
            "verified": True, "keys_down": [], "buttons_down": []}:
        raise AssertionError("matching terminal did not verify empty release")
    if (admission["status"] != "REJECTED_POLICY_INVALIDATED" or
            admission["input_authority_admitted"] or
            admission["executor_admission"] is not None):
        raise AssertionError("invalidated answer passed final admission")
    if planner_result.answer_eligible is not True:
        raise AssertionError("adversarial planner result did not exercise final gate")

    source_bytes = (DOOM / "map01_overlap_controller_v39.py").read_bytes()
    return {
        "schema": "v39-currentmain-health-guard-boundary-a01",
        "source_path": "research/doom/map01_overlap_controller_v39.py",
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_health": 100,
        "hard_minimum": admission_receipt["effective"]["hard_minimum"],
        "threat_present": True,
        "threat_present_is_synthetic_metadata": True,
        "observations": [
            {"sequence": row["sequence"],
             "health": row["signals"]["health"]["value"],
             "expected": "HARD_INVALIDATED" if row["sequence"] == 13 else
                        "SOFT_CHANGED"}
            for row in observations],
        "soft_event_count": monitor.soft_event_count,
        "invalidation_reason": invalidation["reason"],
        "planner_started_before_observations": True,
        "planner_answer_eligible_after_interrupt": planner_result.answer_eligible,
        "answer_return_ns": planner.answer_return_ns,
        "invalidation_evaluated_ns": invalidation["outcome_evaluated_ns"],
        "event_order": process.events,
        "cancel_request": json.loads(process.writes[0]),
        "planner_interrupt": env["planner_interrupt"],
        "cover_terminal": env["current_terminal"],
        "final_admission": admission,
        "formal_allocation_invocations": 0,
        "game_model_gui_os_input": False,
    }


if __name__ == "__main__":
    result = run_case()
    output = HERE / "results" / "candidate_raw.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({"result_path": str(output), "candidate": "PASS_BOUNDARY_SCOPED"},
                     sort_keys=True))
