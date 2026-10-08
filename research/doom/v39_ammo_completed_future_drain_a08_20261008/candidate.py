"""One-shot current-main ammo invalidation through the completed-future drain."""
import ast
from concurrent.futures import Future
import copy
from dataclasses import dataclass
import hashlib
import json
import math
import queue
from pathlib import Path
import subprocess
import threading
import time

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def frozen_source(name):
    spec = FREEZE["sources"][name]
    data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
    blob = subprocess.check_output(["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
    if blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
        raise ValueError(f"frozen source mismatch: {name}")
    return data


guard_namespace = {"json": json, "time": time}
guard_spec = FREEZE["sources"]["guard"]
exec(compile(frozen_source("guard"), guard_spec["path"], "exec"), guard_namespace)

planner_namespace = {"dataclass": dataclass, "json": json, "math": math,
                     "Path": Path, "threading": threading}
planner_spec = FREEZE["sources"]["planner_adapter"]
exec(compile(frozen_source("planner_adapter"), planner_spec["path"], "exec"), planner_namespace)
PersistentPlannerAdapter = planner_namespace["PersistentPlannerAdapter"]

v1_namespace = {"deepcopy": copy.deepcopy}
v1_source = frozen_source("final_admission_v1")
exec(compile(v1_source, FREEZE["sources"]["final_admission_v1"]["path"], "exec"), v1_namespace)
v2_tree = ast.parse(frozen_source("final_admission_v2"),
                     filename=FREEZE["sources"]["final_admission_v2"]["path"])
v2_nodes = [node for node in v2_tree.body
            if ((isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in {"SCHEMA", "ACTION_VALIDITY_FORMAT"}
                    for target in node.targets)) or
                (isinstance(node, ast.FunctionDef) and node.name == "decide_final_admission"))]
v2_namespace = {"deepcopy": copy.deepcopy,
                "decide_v1": v1_namespace["decide_final_admission"]}
exec(compile(ast.Module(body=v2_nodes, type_ignores=[]),
             FREEZE["sources"]["final_admission_v2"]["path"], "exec"), v2_namespace)

controller_spec = FREEZE["sources"]["controller"]
controller_tree = ast.parse(frozen_source("controller"), filename=controller_spec["path"])
needed = {"MAX_AUTHORED_HEALTH_LOSS", "guard_spec", "ammo_guard_spec",
          "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
          "DoomCoverSignalPairMonitor", "build_cover_monitor",
          "drain_pending_observation_events", "require_cover_terminal",
          "final_admission_from_planner_result"}
selected = []
found = set()
for node in controller_tree.body:
    if isinstance(node, ast.Assign):
        names = {target.id for target in node.targets
                 if isinstance(target, ast.Name) and target.id in needed}
        if names:
            selected.append(node)
            found.update(names)
    elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in needed:
        selected.append(node)
        found.add(node.name)
if found != needed:
    raise ValueError(f"missing current-main controller helpers: {sorted(needed - found)}")

controller_namespace = {
    "json": json, "time": time, "queue": queue,
    "ObservableSignalGuard": guard_namespace["ObservableSignalGuard"],
    "ObservableSignalPolicyMonitor": guard_namespace["ObservableSignalPolicyMonitor"],
    "decide_final_admission": v2_namespace["decide_final_admission"],
}
exec(compile(ast.Module(body=selected, type_ignores=[]), controller_spec["path"], "exec"),
     controller_namespace)


def verify_main_order():
    main = next(node for node in controller_tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    drain_ifs = []
    planner_result_assignments = []
    final_admission_assignments = []
    for node in ast.walk(main):
        if isinstance(node, ast.If) and any(
                isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and
                child.func.id == "drain_pending_observation_events"
                for child in ast.walk(node)):
            drain_ifs.append(node)
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "planner_result"
                for target in node.targets):
            planner_result_assignments.append(node)
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "final_action_admission"
                for target in node.targets):
            final_admission_assignments.append(node)
    if len(drain_ifs) != 1 or len(planner_result_assignments) != 1:
        raise ValueError("expected one main drain and planner-result site")
    result_line = planner_result_assignments[0].lineno
    later_admissions = [node for node in final_admission_assignments
                        if node.lineno > result_line]
    if not later_admissions:
        raise ValueError("no final-admission site follows planner-result site")
    final_admission = min(later_admissions, key=lambda node: node.lineno)
    positions = [drain_ifs[0].lineno, result_line, final_admission.lineno]
    if positions != sorted(positions):
        raise ValueError(f"main ordering changed: {positions}")
    drain_text = ast.get_source_segment(
        frozen_source("controller").decode("utf-8"), drain_ifs[0])
    if "future.done()" not in drain_text or "invalidation is None" not in drain_text:
        raise ValueError("drain is not guarded by completed future and empty invalidation")
    return positions


class Reader:
    def __init__(self, name):
        self.name = name

    def read(self, observation):
        return observation["signals"][self.name]


def typed_observation(sequence, health, ammo):
    captured = sequence * 1_000_000
    binding = {"surface_id": "synthetic-v39-ammo-completion-drain"}
    signals = {name: {"status": "observed", "signal_id": name, "value": value,
                      "sequence": sequence, "capture_ns": captured,
                      "binding": binding}
               for name, value in (("health", health), ("ammo", ammo))}
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": captured, "pointer_binding": binding,
            "signals": signals, "frame_rgb_sha256": "e" * 64}


class RecordingQueue(queue.Queue):
    def __init__(self, events):
        super().__init__()
        self.events = events

    def get_nowait(self):
        row = super().get_nowait()
        self.events.append({"event": "queue_dequeued", "row_event": row.get("event"),
                            "sequence": row.get("sequence"), "id": row.get("id"),
                            "status": row.get("status"), "release": row.get("release")})
        return row


class FakeClient:
    def __init__(self, events):
        self.events = events

    def start_thread(self, **kwargs):
        self.events.append({"event": "planner_thread_started"})
        return {"thread": {"id": "thread-a08"}}

    def start_turn(self, thread_id, inputs, **kwargs):
        self.events.append({"event": "planner_turn_started", "thread_id": thread_id})
        return {"turn": {"id": "turn-a08"}}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        self.events.append({"event": "planner_turn_completed", "turn_id": turn_id})
        return {"threadId": thread_id, "turn": {
            "id": turn_id, "status": "completed",
            "items": [{"type": "agentMessage", "text": json.dumps({"action": "stale"})}],
        }}

    def latest_turn_usage(self, thread_id, turn_id):
        return None


def run_case(name, ammo):
    events = []
    planner = PersistentPlannerAdapter(
        FakeClient(events), model="fixed-test-model", effort="low", cwd="/repo",
        base_instructions="Return JSON only.")
    planner.start_session()
    handle = planner.begin_turn("pending decision from the previous paired observation",
                                output_schema={"type": "object"})
    monitor, _admission = controller_namespace["build_cover_monitor"](
        Reader("health"), typed_observation(1, 100, 50),
        {"signal_id": "health", "critical_health_minimum": 80,
         "maximum_health_loss": 12, "max_source_age_ms": 30000},
        1, ammo_reader=Reader("ammo"), requires_ammo=True)
    observation = typed_observation(2, 100, ammo)
    incoming = RecordingQueue(events)
    incoming.put(observation)
    terminal_row = {"event": "terminal", "id": "cover-a08", "status": "completed",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
    incoming.put(terminal_row)
    events.append({"event": "typed_observation_enqueued", "sequence": 2, "ammo": ammo})
    events.append({"event": "matching_terminal_enqueued", "status": "completed"})

    # The adapter completes first, making this a real completed Future before drain.
    planner_result = planner.await_turn(handle)
    future = Future()
    future.set_result(planner_result)
    events.append({"event": "planner_future_completed",
                   "answer_eligible": planner_result.answer_eligible})
    future_done = future.done()
    events.append({"event": "future_done_checked", "done": future_done})
    if not future_done:
        raise RuntimeError("construction failed to create completed-future boundary")

    original_observe = monitor.observe
    observed = []

    def observe_and_record(row):
        events.append({"event": "actual_monitor_received", "sequence": row["sequence"],
                       "future_done": future.done()})
        outcome = original_observe(row)
        observed.append(outcome)
        events.append({"event": "actual_monitor_disposition",
                       "reason": None if outcome is None else outcome["reason"],
                       "requires_new_decision": False if outcome is None else
                           outcome["requires_new_decision"],
                       "grants_input_authority": False if outcome is None else
                           outcome["grants_input_authority"]})
        return outcome

    monitor.observe = observe_and_record
    drained = controller_namespace["drain_pending_observation_events"](
        incoming, monitor, "cover-a08")
    invalidation = drained["invalidation"]
    terminal = drained["terminal"]
    if terminal is not None:
        controller_namespace["require_cover_terminal"](terminal)
    events.append({"event": "completed_terminal_validated",
                   "status": None if terminal is None else terminal["status"],
                   "verified_empty": bool(terminal and terminal["release"] == {
                       "verified": True, "keys_down": [], "buttons_down": []})})

    completed_result = future.result()
    events.append({"event": "completed_answer_read",
                   "answer_eligible": completed_result.answer_eligible,
                   "answer": completed_result.answer})
    terminal_observed_ns = time.perf_counter_ns()
    decided_ns = time.perf_counter_ns()
    admission = controller_namespace["final_admission_from_planner_result"](
        completed_result, terminal_observed_ns, invalidation, decided_ns)
    events.append({"event": "final_admission", "status": admission["status"],
                   "reason": admission["reason"],
                   "input_authority_admitted": admission["input_authority_admitted"]})
    disposition = "hard_invalidation" if invalidation is not None else (
        "soft_change" if monitor.latest_soft_event is not None and
        monitor.latest_soft_event["signal"]["value"] == ammo else "unchanged")
    return {"case": name, "source_health": 100, "current_health": 100,
            "source_ammo": 50, "current_ammo": ammo, "ammo_hard_minimum": 1,
            "planner_future_done_before_drain": future_done,
            "planner_status": completed_result.status,
            "planner_answer_eligible": completed_result.answer_eligible,
            "answer": completed_result.answer,
            "monitor_disposition": disposition,
            "invalidation_reason": None if invalidation is None else invalidation["reason"],
            "terminal": terminal, "final_admission": admission,
            "incoming_empty_after_drain": incoming.empty(), "events": events}


def run():
    main_positions = verify_main_order()
    return {"schema": "issue59-v39-ammo-completed-future-drain-result-a08-v1",
            "status": "CONSTRUCTION_OBSERVATION",
            "main_commit": FREEZE["main_commit"],
            "main_order_lines": {"drain": main_positions[0],
                                 "planner_result": main_positions[1],
                                 "final_admission": main_positions[2]},
            "cases": [run_case("positive-floor-soft-control", 1),
                      run_case("zero-ammo-completed-future", 0)],
            "scope": "Frozen current-main queue-drain, paired monitor, planner adapter, and final-admission composition with synthetic observations and deterministic fakes only."}


if __name__ == "__main__":
    result_path = HERE / "RESULT.json"
    events_path = HERE / "events.jsonl"
    if result_path.exists() or events_path.exists():
        raise SystemExit("refusing to overwrite a one-shot output")
    result = run()
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    raw = [{"case": case["case"], **event}
           for case in result["cases"] for event in case["events"]]
    events_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in raw),
                           encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "case_count": len(result["cases"]),
                      "event_count": len(raw)}, separators=(",", ":")))



