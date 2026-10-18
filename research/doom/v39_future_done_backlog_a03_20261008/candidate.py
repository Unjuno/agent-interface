"""One-shot current-main completion-time observation backlog experiment."""
import argparse
import ast
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
    "DoomCoverSignalPairMonitor", "build_cover_monitor",
    "cancel_invalidated_cover", "require_cover_terminal",
    "drain_pending_observation_events", "final_admission_from_planner_result",
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


def _wait_node(node):
    return (isinstance(node, ast.FunctionDef) and node.name == "wait" and
            "observation_monitor" in {arg.arg for arg in node.args.args})


def _completion_drain_node(node):
    return (isinstance(node, ast.If) and
            ast.unparse(node.test) == "future.done() and invalidation is None")


def load_source_slices():
    guard_ns = {}
    exec(compile(pinned_source("guard"),
                 FREEZE["sources"]["guard"]["path"], "exec"), guard_ns)
    admission_ns = {}
    exec(compile(pinned_source("final_admission"),
                 FREEZE["sources"]["final_admission"]["path"], "exec"), admission_ns)
    data = pinned_source("controller")
    tree = ast.parse(data, filename=FREEZE["sources"]["controller"]["path"])
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
        raise ValueError(f"missing controller slice(s): {sorted(NEEDED - found)}")
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    waits = [node for node in ast.walk(main) if _wait_node(node)]
    branches = [node for node in ast.walk(main) if _completion_drain_node(node)]
    if len(waits) != 1 or len(branches) != 1 or branches[0].lineno != 987:
        raise ValueError("completion-drain or nested wait source anchor changed")
    namespace = {
        "json": json, "queue": queue, "time": time,
        "ObservableSignalGuard": guard_ns["ObservableSignalGuard"],
        "ObservableSignalPolicyMonitor": guard_ns["ObservableSignalPolicyMonitor"],
        "decide_final_admission": admission_ns["decide_final_admission"],
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]),
                 FREEZE["sources"]["controller"]["path"], "exec"), namespace)

    factory = ast.parse(
        "def _make_wait(incoming, process):\n"
        "    latest = None\n"
        "    return wait\n").body[0]
    factory.body.insert(1, ast.fix_missing_locations(ast.unparse(waits[0]) and
                                                     ast.parse(ast.unparse(waits[0])).body[0]))
    ast.fix_missing_locations(factory)
    exec(compile(ast.Module(body=[factory], type_ignores=[]), "<wait-factory>", "exec"),
         namespace)

    runner = ast.parse(
        "def _run_branch(future, incoming, invalidation_monitor, current_cover, "
        "planner, planner_handle, process, wait, failure_cleanup):\n"
        "    latest = None\n"
        "    invalidation = None\n"
        "    current_terminal = None\n"
        "    cover_terminals = []\n"
        "    planner_interrupt = None\n"
        "    return None\n").body[0]
    runner.body.insert(-1, copy_node := ast.parse(ast.unparse(branches[0])).body[0])
    tail = ast.parse(
        "def _tail():\n"
        "    planner_result = future.result()\n"
        "    planner_terminal_observed_ns = time.perf_counter_ns()\n"
        "    admission = final_admission_from_planner_result(\n"
        "        planner_result, planner_terminal_observed_ns, invalidation, "
        "time.perf_counter_ns())\n").body[0]
    runner.body[-1:-1] = tail.body
    return_node = ast.parse(
        "def _return_values():\n"
        "    return {'latest': latest, 'invalidation': invalidation, "
        "'current_terminal': current_terminal, 'cover_terminals': cover_terminals, "
        "'planner_interrupt': planner_interrupt, 'admission': admission}\n").body[0].body[0]
    runner.body[-1] = return_node
    ast.fix_missing_locations(runner)
    exec(compile(ast.Module(body=[runner], type_ignores=[]), "<completion-drain>", "exec"),
         namespace)
    return namespace


def typed_observation(sequence, health):
    binding = {"surface_id": "synthetic-v39-backlog"}
    capture_ns = sequence * 1_000_000
    signals = {name: {"status": "observed", "signal_id": name, "value": value,
                      "sequence": sequence, "capture_ns": capture_ns,
                      "binding": binding}
               for name, value in (("health", health), ("ammo", 50))}
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": capture_ns, "pointer_binding": binding,
            "signals": signals, "frame_rgb_sha256": str(sequence) * 64}


class RecordingQueue(queue.Queue):
    def __init__(self, events):
        super().__init__()
        self.events = events

    def get(self, *args, **kwargs):
        row = super().get(*args, **kwargs)
        event = "terminal_dequeued" if row["event"] == "terminal" else "observation_dequeued"
        item = {"event": event, "row_event": row["event"]}
        item.update({key: row[key] for key in ("sequence", "id", "status", "release")
                     if key in row})
        self.events.append(item)
        return row


class FakeFuture:
    def __init__(self, events):
        self.events = events

    def done(self):
        self.events.append({"event": "planner_future_poll", "done": True})
        return True

    def result(self):
        self.events.append({"event": "planner_result_consumed"})
        return type("PlannerResult", (), {
            "handle": type("Handle", (), {"turn_id": "turn-1"})(),
            "status": "completed", "answer_eligible": True,
            "terminal_observed_ns": time.perf_counter_ns()})()


class FakePipe:
    def __init__(self, events, incoming):
        self.events = events
        self.incoming = incoming

    def write(self, value):
        command = json.loads(value)
        self.events.append({"event": "executor_cancel_write", **command})
        self.incoming.put({"event": "terminal", "id": command["id"],
                           "status": "cancelled",
                           "release": {"verified": True, "keys_down": [],
                                       "buttons_down": []}})

    def flush(self):
        self.events.append({"event": "executor_cancel_flush"})


class FakeProcess:
    def __init__(self, events, incoming):
        self.stdin = FakePipe(events, incoming)

    def poll(self):
        return None


class FakePlanner:
    def __init__(self, events):
        self.events = events

    def interrupt(self, handle, before_transport=None):
        self.events.append({"event": "planner_interrupt_called", "handle": handle})
        if before_transport:
            before_transport()
        self.events.append({"event": "planner_interrupt_transport", "handle": handle})
        return {"outcome": "requested", "transport_accepted": True}


class Reader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return observation["signals"][self.signal_id]


class Cleanup:
    def __init__(self, events):
        self.events = events

    def set_stage(self, stage):
        self.events.append({"event": "cleanup_stage", "stage": stage})


def run_case(terminal_already_queued):
    events = []
    namespace = load_source_slices()
    source = typed_observation(1, 100)
    monitor, admission = namespace["build_cover_monitor"](
        Reader("health"), source,
        {"signal_id": "health", "critical_health_minimum": 80,
         "maximum_health_loss": 20, "max_source_age_ms": 30000},
        0, ammo_reader=Reader("ammo"), requires_ammo=True)
    future = FakeFuture(events)
    original = monitor.observe

    def record_observe(row):
        events.append({"event": "monitor_received", "sequence": row["sequence"],
                       "future_done": True})
        invalidation = original(row)
        if invalidation is not None:
            events.append({"event": "monitor_invalidated",
                           "reason": invalidation["reason"],
                           "requires_new_decision": invalidation["requires_new_decision"],
                           "grants_input_authority": invalidation["grants_input_authority"]})
        return invalidation

    monitor.observe = record_observe
    incoming = RecordingQueue(events)
    incoming.put(typed_observation(2, 70))
    if terminal_already_queued:
        incoming.put({"event": "terminal", "id": "cover-0", "status": "completed",
                      "release": {"verified": True, "keys_down": [], "buttons_down": []}})
    process = FakeProcess(events, incoming)
    planner = FakePlanner(events)
    wait = namespace["_make_wait"](incoming, process)
    result = namespace["_run_branch"](
        future, incoming, monitor, "cover-0", planner, "turn-1", process,
        wait, Cleanup(events))
    return {
        "path": "queued_terminal" if terminal_already_queued else "cancel_needed",
        "source_health": source["signals"]["health"]["value"],
        "current_health": 70,
        "hard_minimum": admission["effective"]["hard_minimum"],
        "result": result,
        "events": events,
    }


def run_once():
    return {
        "schema": "issue59-v39-future-done-backlog-result-a03",
        "status": "CONSTRUCTION_OBSERVATION",
        "main_commit": FREEZE["main_commit"],
        "cases": [run_case(True), run_case(False)],
        "scope": "Pinned completion-time drain branch and helpers with synthetic rows and deterministic fakes only.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "RESULT.json")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else HERE / args.output
    if output.exists() or output.with_name("events.jsonl").exists():
        raise FileExistsError("refusing to overwrite retained candidate output")
    result = run_once()
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8",
                      newline="\n")
    flat = [{"case": case["path"], **row}
            for case in result["cases"] for row in case["events"]]
    output.with_name("events.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in flat),
        encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "case_count": len(result["cases"]),
                      "event_count": len(flat), "result": str(output)},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
