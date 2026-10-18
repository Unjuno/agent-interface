"""One-shot test of the pinned V39 observation pump and invalidation branch."""
import argparse
import ast
import copy
import hashlib
import json
import queue
import subprocess
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
NEEDED = {
    "MAX_AUTHORED_HEALTH_LOSS", "guard_spec", "ammo_guard_spec",
    "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
    "DoomCoverSignalPairMonitor", "build_cover_monitor", "cancel_invalidated_cover",
    "require_cover_terminal",
}


def repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def pinned_source(name):
    spec = FREEZE["sources"][name]
    root = repo_root()
    data = subprocess.check_output(
        ["git", "-C", str(root), "show", f"{FREEZE['main_commit']}:{spec['path']}"])
    blob = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"],
        text=True).strip()
    if hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
        raise ValueError(f"pinned source identity mismatch: {name}")
    return data


def _pending_loop(node):
    test = node.test
    return (isinstance(node, ast.While) and isinstance(test, ast.UnaryOp) and
            isinstance(test.op, ast.Not) and isinstance(test.operand, ast.Call) and
            isinstance(test.operand.func, ast.Attribute) and
            isinstance(test.operand.func.value, ast.Name) and
            test.operand.func.value.id == "future" and test.operand.func.attr == "done")


def load_production_slices():
    guard_bytes = pinned_source("guard")
    guard_namespace = {}
    exec(compile(guard_bytes, FREEZE["sources"]["guard"]["path"], "exec"),
         guard_namespace)
    controller_bytes = pinned_source("controller")
    tree = ast.parse(controller_bytes, filename=FREEZE["sources"]["controller"]["path"])
    selected = []
    found = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {target.id for target in node.targets
                     if isinstance(target, ast.Name) and target.id in NEEDED}
            if names:
                selected.append(node)
                found.update(names)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in NEEDED:
            selected.append(node)
            found.add(node.name)
    if found != NEEDED:
        raise ValueError(f"missing production helper(s): {sorted(NEEDED - found)}")

    wait_nodes = [node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == "wait" and
                  "observation_monitor" in {arg.arg for arg in node.args.args}]
    loops = [node for node in ast.walk(tree) if _pending_loop(node)]
    if len(wait_nodes) != 1 or len(loops) != 1 or len(loops[0].body) < 2:
        raise ValueError("expected one production wait function and one pending-future loop")
    if wait_nodes[0].lineno != 799 or loops[0].lineno != 914:
        raise ValueError("frozen event-pump AST positions changed")

    namespace = {"json": json, "time": time, "queue": queue,
                 "ObservableSignalGuard": guard_namespace["ObservableSignalGuard"]}
    exec(compile(ast.Module(body=selected, type_ignores=[]),
                 FREEZE["sources"]["controller"]["path"], "exec"), namespace)

    wait_factory = ast.parse(
        "def _make_wait(incoming, process):\n    latest = None\n    return wait\n").body[0]
    wait_factory.body.insert(1, copy.deepcopy(wait_nodes[0]))
    ast.fix_missing_locations(wait_factory)
    exec(compile(ast.Module(body=[wait_factory], type_ignores=[]), "<wait-factory>", "exec"),
         namespace)

    loop = copy.deepcopy(loops[0])
    loop.body = loop.body[:2]
    pump = ast.parse(
        "def _run_pending_pump(future, wait, invalidation_monitor, current_cover, "
        "planner, planner_handle, process, cover_terminals):\n"
        "    planner_interrupt = None\n"
        "    current_terminal = None\n"
        "    return planner_interrupt, current_terminal, cover_terminals\n").body[0]
    pump.body.insert(2, loop)
    ast.fix_missing_locations(pump)
    exec(compile(ast.Module(body=[pump], type_ignores=[]), "<pending-pump>", "exec"),
         namespace)
    return namespace


def typed_observation(sequence, health):
    binding = {"surface_id": "synthetic-v39-event-pump"}
    captured = sequence * 1_000_000
    signals = {name: {"status": "observed", "signal_id": name, "value": value,
                      "sequence": sequence, "capture_ns": captured,
                      "binding": binding}
               for name, value in (("health", health), ("ammo", 50))}
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": captured, "pointer_binding": binding, "signals": signals,
            "frame_rgb_sha256": str(sequence) * 64}


class RecordingQueue(queue.Queue):
    def __init__(self, events):
        super().__init__()
        self.events = events

    def get(self, *args, **kwargs):
        row = super().get(*args, **kwargs)
        name = "terminal_dequeued" if row["event"] == "terminal" else "observation_dequeued"
        logged = {"event": name, "row_event": row["event"]}
        if row["event"] == "terminal":
            logged.update(id=row.get("id"), status=row.get("status"),
                          release=row.get("release"))
        else:
            logged["sequence"] = row.get("sequence")
        self.events.append(logged)
        return row


class PendingFuture:
    def __init__(self, events):
        self.events = events
        self.pending = True

    def done(self):
        self.events.append({"event": "planner_future_poll", "done": False})
        return False


class FakePipe:
    def __init__(self, events):
        self.events = events

    def write(self, value):
        command = json.loads(value)
        self.events.append({"event": "executor_cancel_write", **command})

    def flush(self):
        self.events.append({"event": "executor_cancel_flush"})


class FakeProcess:
    def __init__(self, events):
        self.stdin = FakePipe(events)

    def poll(self):
        return None


class FakePlanner:
    def __init__(self, events):
        self.events = events

    def interrupt(self, handle, before_transport=None):
        self.events.append({"event": "planner_interrupt_called", "handle": handle})
        if before_transport is not None:
            before_transport()
        self.events.append({"event": "planner_interrupt_transport", "handle": handle})
        return {"outcome": "requested", "transport_accepted": True}


class Reader:
    def __init__(self, name):
        self.name = name

    def read(self, observation):
        return observation["signals"][self.name]


def run_once():
    events = []
    namespace = load_production_slices()
    source = typed_observation(1, 100)
    current = typed_observation(2, 84)
    monitor, admission = namespace["build_cover_monitor"](
        Reader("health"), source,
        {"signal_id": "health", "critical_health_minimum": 80,
         "maximum_health_loss": 12, "max_source_age_ms": 30000},
        1, ammo_reader=Reader("ammo"), requires_ammo=True)
    future = PendingFuture(events)
    original_observe = monitor.observe

    def observe_while_pending(row):
        events.append({"event": "monitor_received", "sequence": row["sequence"],
                       "future_pending": future.pending})
        invalidation = original_observe(row)
        if invalidation is not None:
            events.append({"event": "monitor_invalidated",
                           "reason": invalidation["reason"],
                           "requires_new_decision": invalidation["requires_new_decision"],
                           "grants_input_authority": invalidation["grants_input_authority"]})
        return invalidation

    monitor.observe = observe_while_pending
    events.append({"event": "observation_enqueued", "sequence": current["sequence"]})
    incoming = RecordingQueue(events)
    incoming.put(current)
    incoming.put({"event": "terminal", "id": "cover-1", "status": "cancelled",
                  "release": {"verified": True, "keys_down": [], "buttons_down": []}})
    process = FakeProcess(events)
    planner = FakePlanner(events)
    cover_terminals = []
    wait = namespace["_make_wait"](incoming, process)
    planner_interrupt, terminal, _ = namespace["_run_pending_pump"](
        future, wait, monitor, "cover-1", planner, "turn-1", process, cover_terminals)
    helper_events = []
    helper_events.append({"event": "planner_interrupt_outcome",
                          "outcome": planner_interrupt.get("outcome")})
    helper_events.append({"event": "verified_terminal_returned",
                          "id": terminal["id"], "status": terminal["status"],
                          "release": terminal["release"]})
    events.extend(helper_events)
    return {
        "schema": "issue59-v39-observation-pump-event-dispatch-result-v1",
        "status": "CONSTRUCTION_OBSERVATION",
        "main_commit": FREEZE["main_commit"],
        "planner_pending_at_observation": future.pending,
        "source_health": source["signals"]["health"]["value"],
        "current_health": current["signals"]["health"]["value"],
        "hard_minimum": admission["effective"]["hard_minimum"],
        "terminal": terminal,
        "planner_interrupt_outcome": planner_interrupt["outcome"],
        "events": events,
        "scope": "Pinned production wait/pending-loop/cancel-helper AST slices with synthetic rows and deterministic fakes only.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "RESULT.json")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else HERE / args.output
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    result = run_once()
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    events_path = output.with_name("events.jsonl")
    if events_path.exists():
        raise FileExistsError(f"refusing to overwrite {events_path}")
    events_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n"
                                      for row in result["events"]),
                           encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "event_count": len(result["events"]),
                      "result": str(output)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
