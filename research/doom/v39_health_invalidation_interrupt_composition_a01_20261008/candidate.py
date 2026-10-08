"""One-shot composition of V39 health invalidation, cover cancel and planner adapter."""
import ast
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / "research" / "live_control"))
from persistent_planner_adapter_v2 import PersistentPlannerAdapter


def frozen_source(spec):
    data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
    blob = subprocess.check_output(["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
    if hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
        raise ValueError(f"frozen source mismatch: {spec['path']}")
    return data


namespace = {"json": json, "time": time}
guard_spec = FREEZE["sources"]["guard"]
exec(compile(frozen_source(guard_spec), guard_spec["path"], "exec"), namespace)
controller_spec = FREEZE["sources"]["controller"]
tree = ast.parse(frozen_source(controller_spec), filename=controller_spec["path"])
needed = {"MAX_AUTHORED_HEALTH_LOSS", "guard_spec", "ammo_guard_spec",
          "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
          "DoomCoverSignalPairMonitor", "build_cover_monitor",
          "cancel_invalidated_cover", "require_cover_terminal"}
selected = [node for node in tree.body
            if ((isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in needed for target in node.targets)) or
                (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in needed))]
found = {next((target.id for target in node.targets if isinstance(target, ast.Name)), "")
         if isinstance(node, ast.Assign) else node.name for node in selected}
if found != needed:
    raise ValueError(f"missing frozen controller helper(s): {sorted(needed - found)}")
exec(compile(ast.Module(body=selected, type_ignores=[]), controller_spec["path"], "exec"), namespace)

SCHEMA = {"type": "object", "properties": {"action": {"type": "string"}},
          "required": ["action"], "additionalProperties": False}


class Reader:
    def __init__(self, name):
        self.name = name

    def read(self, observation):
        return observation["signals"][self.name]


def observation(sequence, health):
    captured = sequence * 1_000_000
    binding = {"surface_id": "synthetic-v39-composition"}
    signals = {name: {"status": "observed", "signal_id": name, "value": value,
                      "sequence": sequence, "capture_ns": captured, "binding": binding}
               for name, value in (("health", health), ("ammo", 50))}
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": captured, "pointer_binding": binding, "signals": signals,
            "frame_rgb_sha256": "b" * 64}


class FakeClient:
    def __init__(self, events, *, cancel_answer="stale", interrupt_error=False):
        self.events = events
        self.cancel_answer = cancel_answer
        self.interrupt_error = interrupt_error

    def start_thread(self, **kwargs):
        self.events.append({"event": "thread_started", "thread_id": "thread-1"})
        return {"thread": {"id": "thread-1"}}

    def start_turn(self, thread_id, inputs, **kwargs):
        self.events.append({"event": "turn_started", "thread_id": thread_id,
                            "turn_id": "turn-1", "input": inputs[0]["text"]})
        return {"turn": {"id": "turn-1"}}

    def interrupt_turn(self, thread_id, turn_id):
        self.events.append({"event": "planner_interrupt_transport", "thread_id": thread_id,
                            "turn_id": turn_id})
        if self.interrupt_error:
            raise OSError("synthetic planner transport error")
        return {"accepted": True}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        self.events.append({"event": "answer_arrived", "thread_id": thread_id,
                            "turn_id": turn_id})
        text = json.dumps({"action": self.cancel_answer})
        return {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed",
                "items": [{"type": "agentMessage", "text": text}]}}

    def latest_turn_usage(self, thread_id, turn_id):
        return None


class FakePipe:
    def __init__(self, events, *, fail=False):
        self.events = events
        self.fail = fail

    def write(self, value):
        self.events.append({"event": "executor_cancel_write", **json.loads(value)})
        if self.fail:
            raise OSError("synthetic executor cancel failure")

    def flush(self):
        self.events.append({"event": "executor_cancel_flush"})


class FakeProcess:
    def __init__(self, events, *, fail=False):
        self.stdin = FakePipe(events, fail=fail)


def run_case(name, loss, health, *, cancel_fails=False):
    events = []
    client = FakeClient(events)
    planner = PersistentPlannerAdapter(client, model="fixed-test-model", effort="low",
                                       cwd="/repo", base_instructions="Return JSON only.")
    planner.start_session()
    handle = planner.begin_turn("pending old observation", output_schema=SCHEMA)
    monitor, admission = namespace["build_cover_monitor"](
        Reader("health"), observation(1, 100),
        {"signal_id": "health", "critical_health_minimum": 80,
         "maximum_health_loss": loss, "max_source_age_ms": 30000},
        1, ammo_reader=Reader("ammo"), requires_ammo=True)
    invalidation = monitor.observe(observation(2, health))
    events.append({"event": "monitor_disposition",
                   "outcome": None if invalidation is None else invalidation["reason"],
                   "hard_minimum": admission["effective"]["hard_minimum"]})
    helper_error = None
    terminal = None
    if invalidation is not None:
        def wait(_predicate):
            nonlocal terminal
            terminal = {"event": "terminal", "id": "cover-1", "status": "cancelled",
                        "release": {"verified": True, "keys_down": [], "buttons_down": []}}
            events.append({"event": "cover_terminal", "status": terminal["status"],
                           "release": terminal["release"]})
            return terminal
        try:
            interrupt, terminal = namespace["cancel_invalidated_cover"](
                planner, handle, FakeProcess(events, fail=cancel_fails), wait, "cover-1")
            events.append({"event": "helper_returned", "interrupt_outcome": interrupt["outcome"]})
        except RuntimeError as error:
            helper_error = str(error)
            events.append({"event": "helper_error", "message": helper_error})
    result = planner.await_turn(handle)
    events.append({"event": "answer_classified", "answer_eligible": result.answer_eligible,
                   "answer": result.answer, "cancellation_requested": result.cancellation_requested})
    return {"case": name, "maximum_health_loss": loss, "health": health,
            "hard_minimum": admission["effective"]["hard_minimum"],
            "invalidation": None if invalidation is None else invalidation["reason"],
            "cancel_fails": cancel_fails, "terminal": terminal,
            "helper_error": helper_error, "answer_eligible": result.answer_eligible,
            "answer": result.answer, "events": events}


def run():
    return {"schema": "issue59-health-invalidation-interrupt-composition-result-v1",
            "status": "CONSTRUCTION_OBSERVATION", "main_commit": FREEZE["main_commit"],
            "pending_model": True,
            "cases": [run_case("hard-crossing-cancel-first", 12, 84),
                      run_case("soft-change-preserves-cover", 16, 84),
                      run_case("hard-crossing-cancel-write-failure", 12, 84, cancel_fails=True)],
            "scope": "Synthetic typed HUD and fake transport composition only; no live timing, key state, task effect, or recovery efficacy."}


if __name__ == "__main__":
    output = HERE / "RESULT.json"
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    result = run()
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, separators=(",", ":")))
