"""One-shot test of full pinned V39 pending-future loop paths."""
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
    if not isinstance(node, ast.While):
        return False
    test = node.test
    return (isinstance(test, ast.UnaryOp) and
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
    found.update({"ObservableSignalPolicyMonitor"} if "ObservableSignalPolicyMonitor" in guard_namespace else set())
    controller_needed = NEEDED - {"ObservableSignalPolicyMonitor"}
    controller_found = found - {"ObservableSignalPolicyMonitor"}
    if controller_found != controller_needed:
        raise ValueError(f"missing production helper(s): {sorted(NEEDED - found)}")

    wait_nodes = [node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == "wait" and
                  "observation_monitor" in {arg.arg for arg in node.args.args}]
    loops = [node for node in ast.walk(tree) if _pending_loop(node)]
    if len(wait_nodes) != 1 or len(loops) != 1 or len(loops[0].body) < 2:
        raise ValueError("expected one production wait function and one pending-future loop")
    if not any(isinstance(node, ast.While) and _pending_loop(node)
               for node in ast.walk(tree)):
        raise ValueError("frozen pending-future loop is absent")

    namespace = {"json": json, "time": time, "queue": queue,
                 "ObservableSignalPolicyMonitor": guard_namespace["ObservableSignalPolicyMonitor"],
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
    pump = ast.parse(
        "def _run_pending_pump(future, wait, invalidation_monitor, current_cover, "
        "planner, planner_handle, process, cover_terminals, submit_cover, "
        "failure_cleanup, index, cover_ids, cover_renewal_gaps_ms):\n"
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


class ScriptedFuture:
    def __init__(self, events, done_after):
        self.events = events
        self.done_after = done_after
        self.polls = 0
        self.pending = True

    def done(self):
        self.polls += 1
        done = self.done_after is not None and self.polls >= self.done_after
        self.pending = not done
        self.events.append({"event": "planner_future_poll", "done": done})
        return done


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


def run_case(case_name, observations, terminal_ids, done_after):
    events = []
    namespace = load_production_slices()
    source = typed_observation(1, 100)
    monitor, admission = namespace["build_cover_monitor"](
        Reader("health"), source,
        {"signal_id": "health", "critical_health_minimum": 80,
         "maximum_health_loss": 20, "max_source_age_ms": 30000},
        1, ammo_reader=Reader("ammo"), requires_ammo=True)
    future = ScriptedFuture(events, done_after)
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
    incoming = RecordingQueue(events)
    for sequence, health in observations:
        row = typed_observation(sequence, health)
        events.append({"event": "observation_enqueued", "sequence": sequence})
        incoming.put(row)
    if case_name != "invalidation":
        for identifier in terminal_ids:
            incoming.put({"event": "terminal", "id": identifier, "status": "completed",
                          "terminal_ns": 1_000_000_000 + len(events),
                          "release": {"verified": True, "keys_down": [], "buttons_down": []}})
    if case_name == "invalidation":
        incoming.put({"event": "terminal", "id": terminal_ids[-1],
                      "status": "cancelled", "terminal_ns": 2_000_000_000,
                      "release": {"verified": True, "keys_down": [], "buttons_down": []}})
    process = FakeProcess(events)
    planner = FakePlanner(events)
    cover_terminals = []
    wait = namespace["_make_wait"](incoming, process)
    submitted = []
    def submit_cover(identifier):
        submitted.append(identifier)
        cover_ids.append(identifier)
        events.append({"event": "cover_renewed", "id": identifier})
        return {"accepted_ns": 1_000_000_000 + len(events)}
    class Cleanup:
        def set_stage(self, stage):
            events.append({"event": "cleanup_stage", "stage": stage})
    cover_ids = []
    renewal_gaps = []
    result = namespace["_run_pending_pump"](
        future, wait, monitor, "cover-0", planner, "turn-1", process,
        cover_terminals, submit_cover, Cleanup(), 0, cover_ids, renewal_gaps)
    planner_interrupt, terminal, _ = result
    return {"case": case_name, "events": events, "submitted": submitted,
            "cover_terminals": cover_terminals, "planner_interrupt": planner_interrupt,
            "terminal": terminal, "future_polls": future.polls,
            "hard_minimum": admission["effective"]["hard_minimum"]}


def run_once():
    healthy = run_case("healthy_completion", [(2, 99), (3, 98), (4, 97)],
                       ["cover-0", "cover-0-renew-0", "cover-0-renew-1"],
                       done_after=6)
    invalidation = run_case("invalidation", [(2, 99), (3, 70)],
                            ["cover-0"], done_after=None)
    return {"schema": "issue59-v39-observation-pump-full-loop-result-a04",
            "status": "CONSTRUCTION_OBSERVATION",
            "main_commit": FREEZE["main_commit"],
            "cases": [healthy, invalidation],
            "scope": "Full frozen pending-loop AST with synthetic queues, patched cover-submit boundary, and deterministic fakes only."}


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
    flat_events = [{"case": case["case"], **row}
                   for case in result["cases"] for row in case["events"]]
    events_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n"
                                      for row in flat_events),
                           encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"],
                      "event_count": sum(len(case["events"]) for case in result["cases"]),
                      "result": str(output)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
