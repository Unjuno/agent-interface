"""One-shot qsize-snapshot interleaving through current V39 action admission."""
import argparse
import ast
import hashlib
import json
import queue
import subprocess
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
HELPERS = {
    "MAX_AUTHORED_HEALTH_LOSS", "guard_spec", "ammo_guard_spec",
    "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
    "DoomCoverSignalPairMonitor", "build_cover_monitor",
    "require_cover_terminal", "drain_pending_observation_events",
    "prepare_action_admission", "final_admission_from_planner_result",
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


def exec_module(name, source_name):
    module = types.ModuleType(name)
    module.__file__ = FREEZE["sources"][source_name]["path"]
    sys.modules[name] = module
    exec(compile(pinned_source(source_name), module.__file__, "exec"), module.__dict__)
    return module


def load_source():
    av = exec_module("action_validity_admission_v1", "action_validity")
    fa1 = exec_module("final_action_admission_v1", "final_admission_v1")
    fa2 = exec_module("final_action_admission_v2", "final_admission_v2")
    contract = exec_module("doom_action_validity_contract_v1", "action_contract")

    guard_ns = {}
    exec(compile(pinned_source("guard"),
                 FREEZE["sources"]["guard"]["path"], "exec"), guard_ns)
    source = pinned_source("controller")
    tree = ast.parse(source, filename=FREEZE["sources"]["controller"]["path"])
    selected, found = [], set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {target.id for target in node.targets
                     if isinstance(target, ast.Name) and target.id in HELPERS}
            if names:
                selected.append(node)
                found.update(names)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in HELPERS:
            selected.append(node)
            found.add(node.name)
    if found != HELPERS:
        raise ValueError(f"missing controller helpers: {sorted(HELPERS - found)}")
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    drain_blocks = [node for node in ast.walk(main)
                    if isinstance(node, ast.If) and
                    ast.unparse(node.test) == "future.done() and invalidation is None"]
    if len(drain_blocks) != 1 or drain_blocks[0].lineno != 987:
        raise ValueError("pinned completion-drain branch anchor changed")
    ns = {
        "json": json, "hashlib": hashlib, "queue": queue, "time": time,
        "ObservableSignalGuard": guard_ns["ObservableSignalGuard"],
        "ObservableSignalPolicyMonitor": guard_ns["ObservableSignalPolicyMonitor"],
        "build_action_contract": contract.build_contract,
        "bindings_equal_exact": contract.bindings_equal_exact,
        "evaluate_action_validity": av.evaluate_action_validity,
        "SNAPSHOT_FORMAT": av.SNAPSHOT_FORMAT,
        "record_action_validity": fa2.record_action_validity,
        "decide_final_admission": fa2.decide_final_admission,
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]),
                 FREEZE["sources"]["controller"]["path"], "exec"), ns)
    branch_runner = ast.parse(
        "def _run_branch(future, incoming, invalidation_monitor, current_cover, "
        "planner, planner_handle, process, wait, failure_cleanup, latest):\n"
        "    invalidation = None\n"
        "    current_terminal = None\n"
        "    cover_terminals = []\n"
        "    planner_interrupt = None\n"
        "    return None\n").body[0]
    branch = ast.parse(ast.unparse(drain_blocks[0])).body[0]
    branch_runner.body.insert(-1, branch)
    tail = ast.parse(
        "def _tail():\n"
        "    planner_result = future.result()\n"
        "    planner_terminal_observed_ns = time.perf_counter_ns()\n"
        "    receipt = final_admission_from_planner_result(\n"
        "        planner_result, planner_terminal_observed_ns, invalidation, "
        "time.perf_counter_ns())\n"
        "    return {'latest': latest, 'invalidation': invalidation, "
        "'current_terminal': current_terminal, 'cover_terminals': cover_terminals, "
        "'planner_interrupt': planner_interrupt, 'receipt': receipt}\n").body[0]
    branch_runner.body[-1:-1] = tail.body
    ast.fix_missing_locations(branch_runner)
    exec(compile(ast.Module(body=[branch_runner], type_ignores=[]),
                 "<completion-race-branch>", "exec"), ns)
    return ns


def typed_observation(sequence, health, capture_ns, binding):
    signals = {name: {"format": "observable-signal-v1", "status": "observed",
                      "signal_id": name, "value": value, "sequence": sequence,
                      "capture_ns": capture_ns, "binding": binding}
               for name, value in (("health", health), ("ammo", 50))}
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": capture_ns, "pointer_binding": binding,
            "signals": signals, "frame_rgb_sha256": str(sequence) * 64}


class SnapshotRaceQueue(queue.Queue):
    def __init__(self, events, late_row):
        super().__init__()
        self.events = events
        self.late_row = late_row
        self.injected = False

    def qsize(self):
        snapshot = super().qsize()
        self.events.append({"event": "queue_snapshot", "count": snapshot})
        if not self.injected:
            self.injected = True
            self.put(self.late_row)
            self.events.append({"event": "late_observation_enqueued",
                                "sequence": self.late_row["sequence"]})
        return snapshot

    def get(self, *args, **kwargs):
        row = super().get(*args, **kwargs)
        event = "terminal_dequeued" if row["event"] == "terminal" else "late_observation_dequeued"
        self.events.append({"event": event, "row_event": row["event"],
                            "id": row.get("id"), "sequence": row.get("sequence")})
        return row


class Future:
    def __init__(self, events):
        self.events = events

    def done(self):
        self.events.append({"event": "planner_future_poll", "done": True})
        return True

    def result(self):
        self.events.append({"event": "planner_result_consumed"})
        return types.SimpleNamespace(
            handle=types.SimpleNamespace(turn_id="turn-1"),
            status="completed", answer_eligible=True)


class Planner:
    def __init__(self, events):
        self.events = events

    def interrupt(self, *args, **kwargs):
        self.events.append({"event": "planner_interrupt_called"})
        return {"outcome": "requested"}


class Process:
    def __init__(self):
        self.stdin = types.SimpleNamespace(write=lambda value: None, flush=lambda: None)

    def poll(self):
        return None


class Cleanup:
    def set_stage(self, stage):
        pass


class Reader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return observation["signals"][self.signal_id]


def run_once():
    events = []
    ns = load_source()
    binding = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}
    source_ns = time.perf_counter_ns()
    source = typed_observation(1, 100, source_ns, binding)
    late = typed_observation(2, 70, time.perf_counter_ns(), binding)
    health_reader, ammo_reader = Reader("health"), Reader("ammo")
    monitor, _admission = ns["build_cover_monitor"](
        health_reader, source,
        {"signal_id": "health", "critical_health_minimum": 80,
         "maximum_health_loss": 20, "max_source_age_ms": 30000},
        0, ammo_reader=ammo_reader, requires_ammo=True)
    observed = []
    original_observe = monitor.observe

    def observe(row):
        observed.append(row["sequence"])
        events.append({"event": "monitor_received", "sequence": row["sequence"]})
        outcome = original_observe(row)
        if outcome is not None:
            events.append({"event": "monitor_invalidated",
                           "reason": outcome["reason"],
                           "requires_new_decision": outcome["requires_new_decision"],
                           "grants_input_authority": outcome["grants_input_authority"]})
        return outcome

    monitor.observe = observe
    incoming = SnapshotRaceQueue(events, late)
    incoming.put({"event": "terminal", "id": "cover-0", "status": "completed",
                  "terminal_ns": time.perf_counter_ns(),
                  "release": {"verified": True, "keys_down": [], "buttons_down": []}})
    initial_latest = {"event": "observation", "sequence": 1,
                      "capture_ns": source_ns, "pointer_binding": binding,
                      "signals": source["signals"]}
    future = Future(events)
    process = Process()
    result = ns["_run_branch"](future, incoming, monitor, "cover-0",
                              Planner(events), "turn-1", process,
                              lambda *args, **kwargs: None, Cleanup(), initial_latest)
    events.append({"event": "final_planner_policy_receipt",
                   "status": result["receipt"]["status"]})
    fresh_before_plan = dict(result["latest"])
    current_health = health_reader.read(fresh_before_plan)
    current_ammo = ammo_reader.read(fresh_before_plan)
    authored = {"critical_health_minimum": 80, "maximum_health_loss": 20,
                "minimum_ammo": 1, "max_current_age_ms": 1000}
    action = {"commands": [{"action": "retreat_fire", "extent": "short"}]}
    action_receipt = ns["prepare_action_admission"](
        result["receipt"], action, authored,
        health_reader.read(source), ammo_reader.read(source),
        current_health, current_ammo, time.perf_counter_ns())
    events.append({"event": "action_admission_evaluated",
                   "status": action_receipt["status"],
                   "current_health_value": current_health["value"],
                   "current_health_sequence": current_health["sequence"]})
    late_row = incoming.get_nowait()
    later_invalidation = monitor.observe(late_row)
    events.append({"event": "late_observation_processed_after_admission",
                   "sequence": late_row["sequence"],
                   "invalidated": later_invalidation is not None})
    return {
        "schema": "issue59-v39-future-done-late-observation-result-a03",
        "status": "CONSTRUCTION_OBSERVATION",
        "main_commit": FREEZE["main_commit"],
        "source_health": 100, "late_health": 70, "hard_minimum": 80,
        "drain_result": {"latest": None,
                         "terminal_id": result["current_terminal"]["id"],
                         "invalidation": result["invalidation"]},
        "latest_used_for_action_admission": {
            "sequence": result["latest"]["sequence"],
            "health": current_health["value"]},
        "action_admission": action_receipt,
        "late_monitor_invalidated": later_invalidation is not None,
        "monitor_observed_sequences": observed,
        "events": events,
        "scope": "Synthetic qsize interleaving and production source-slice admission helpers only; no executor submission.",
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
    output.with_name("events.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in result["events"]),
        encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "event_count": len(result["events"]),
                      "result": str(output)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
