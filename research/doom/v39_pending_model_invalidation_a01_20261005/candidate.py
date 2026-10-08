"""Exercise the frozen V39 pending-model invalidation branch with fake IO."""
import ast
import json
import sys
import time
from pathlib import Path

import map01_overlap_controller_v39 as controller
from observable_signal_guard_v2 import ObservableSignalGuard

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "research/doom/map01_overlap_controller_v39.py"
FREEZE = Path(__file__).with_name("FREEZE.json")


def source_nodes():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        index = next((i for i, row in enumerate(node.body)
                      if isinstance(row, ast.While) and
                      ast.unparse(row.test) == "not future.done()"), None)
        if index is None:
            continue
        result = next((row for row in node.body[index + 1:]
                       if isinstance(row, ast.Assign) and any(
                           isinstance(t, ast.Name) and t.id == "planner_result"
                           for t in row.targets)), None)
        if result is None:
            raise AssertionError("planner_result assignment absent")
        return node.body[index], result
    raise AssertionError("V39 pending-model loop absent")


def signal(name, value, sequence, capture_ns, binding):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": binding}


def monitor_for_case(case):
    binding = {"surface": 17, "geometry": [0, 0, 640, 480]}
    health = signal("health", 100, 10, 1_000_000_000, binding)
    ammo = signal("ammo", 30, 10, 1_000_000_000, binding)
    validity = {"signal_id": "health", "critical_health_minimum": 50,
                "maximum_health_loss": 10, "max_source_age_ms": 30000}
    hg = ObservableSignalGuard(controller.guard_spec(validity, health, 1), health, binding)
    ag = ObservableSignalGuard(controller.ammo_guard_spec(ammo, 1, 30000), ammo, binding)
    monitor = controller.DoomCoverSignalPairMonitor({"health": hg, "ammo": ag}, None, None)
    if case == "hard_health":
        hv, av, ab = 89, 29, binding
    elif case == "unknown_pair_binding":
        hv, av, ab = 95, 29, {"surface": 18, "geometry": [0, 0, 640, 480]}
    else:
        hv, av, ab = 95, 29, binding
    captured = 1_100_000_000
    row = {"event": "typed_observation", "sequence": 11, "capture_ns": captured,
           "pointer_binding": binding, "frame_rgb_sha256": "a" * 64,
           "signals": {"health": signal("health", hv, 11, captured, binding),
                       "ammo": signal("ammo", av, 11, captured, ab)}}
    return monitor, row


class Handle:
    turn_id = "turn-synthetic-pending-a01"


class Result:
    handle = Handle()
    status = "completed"
    answer_eligible = True
    cancellation_requested = True


class Future:
    def __init__(self, events, require_release):
        self.complete = False
        self.events = events
        self.require_release = require_release

    def done(self):
        return self.complete

    def result(self):
        if not self.complete:
            raise AssertionError("result requested while pending")
        if self.require_release and "verified_empty_release" not in self.events:
            raise AssertionError("answer returned before verified empty release")
        self.events.append("late_model_answer_returned")
        return Result()


class Planner:
    def __init__(self, events):
        self.events = events

    def interrupt(self, handle):
        if self.events[-1] != "hud_invalidation_observed_while_pending":
            raise AssertionError("interrupt did not follow a pending invalidation")
        self.events.append("planner_interrupt_requested")
        return {"status": "interrupted", "turn_id": handle.turn_id}


class Process:
    def __init__(self, events):
        self.events = events
        self.stdin = self
        self.writes = []

    def write(self, value):
        command = json.loads(value)
        if command != {"op": "cancel", "id": "cover-a01"}:
            raise AssertionError(f"unexpected command: {command!r}")
        self.writes.append(command)
        self.events.append("cover_cancel_emitted")
        return len(value)

    def flush(self):
        return None


def run_case(case, nodes):
    events = ["model_pending"]
    monitor, observation = monitor_for_case(case)
    future = Future(events, case != "soft_change")
    planner, process = Planner(events), Process(events)
    terminal_rows = []
    state = {"future": future, "current_cover": "cover-a01",
             "invalidation_monitor": monitor, "planner_handle": Handle(),
             "planner": planner, "process": process, "cover_terminals": terminal_rows,
             "cover_ids": ["cover-a01"], "cover_renewal_gaps_ms": [], "index": 1,
             "TimeoutError": TimeoutError, "cancel_invalidated_cover": controller.cancel_invalidated_cover,
             "submit_cover": lambda _id: (_ for _ in ()).throw(AssertionError("unexpected renewal"))}

    def wait(predicate, timeout=40, observation_monitor=None):
        if observation_monitor is not None:
            if future.done():
                raise AssertionError("signal observed after answer completion")
            event = observation_monitor.observe(observation)
            if event is None:
                events.append("soft_change_preserved_while_pending")
                future.complete = True
                raise TimeoutError()
            events.append("hud_invalidation_observed_while_pending")
            return {"event": "policy_invalidation", "invalidation": event}
        terminal = {"event": "terminal", "id": "cover-a01", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        if not predicate(terminal) or process.writes != [{"op": "cancel", "id": "cover-a01"}]:
            raise AssertionError("invalid terminal/cancel sequence")
        events.append("verified_empty_release")
        future.complete = True
        return terminal

    state["wait"] = wait
    loop, assignment = nodes
    executable = ast.Module(body=[loop, assignment], type_ignores=[])
    exec(compile(ast.fix_missing_locations(executable), str(SOURCE), "exec"), state, state)
    invalidation = state.get("invalidation")
    terminal_ns = time.perf_counter_ns()
    invalidation_ns = invalidation["outcome_evaluated_ns"] if invalidation else 0
    decision_ns = max(terminal_ns, invalidation_ns) + 1
    admission = controller.final_admission_from_planner_result(
        state["planner_result"], terminal_ns, invalidation, decision_ns)
    if case == "soft_change":
        assert invalidation is None
        assert admission["status"] == "READY_FOR_ACTION_VALIDITY"
        assert events == ["model_pending", "soft_change_preserved_while_pending",
                          "late_model_answer_returned"]
    else:
        assert admission["status"] == "REJECTED_POLICY_INVALIDATED"
        assert admission["input_authority_admitted"] is False
        assert events == ["model_pending", "hud_invalidation_observed_while_pending",
                          "planner_interrupt_requested", "cover_cancel_emitted",
                          "verified_empty_release", "late_model_answer_returned"]
        assert len(terminal_rows) == 1 and terminal_rows[0]["release"]["verified"] is True
        assert terminal_rows[0]["release"]["buttons_down"] == []
        assert terminal_rows[0]["release"]["keys_down"] == []
        if case == "hard_health":
            assert invalidation["outcomes"]["health"]["status"] == "HARD_INVALIDATED"
        else:
            assert invalidation["outcome"]["status"] == "UNKNOWN"
    assert admission["grants_input_authority"] is False
    return {"case": case, "events": events, "invalidation": invalidation,
            "final_admission": admission, "soft_event_count": monitor.soft_event_count,
            "cancel_commands": process.writes, "terminal_receipts": terminal_rows,
            "planner_interrupt_calls": events.count("planner_interrupt_requested")}


def main():
    import hashlib
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in freeze["implementation_files"]}
    if hashes != freeze["implementation_file_sha256"]:
        raise AssertionError("source changed after freeze")
    result = {"schema": "v39-pending-model-invalidation-construction-a03",
              "status": "PASS_CONSTRUCTION_SCOPED",
              "repository_commit": freeze["repository_commit"],
              "implementation_file_sha256": hashes,
              "python": sys.version.split()[0],
              "cases": [run_case(case, source_nodes()) for case in
                        ("hard_health", "unknown_pair_binding", "soft_change")],
              "limitations": ["deterministic fake observations and provider scheduling",
                              "no live game, GUI, model call, native input, or timing",
                              "does not test whether real threat-linked HUD changes cross the authored guard"]}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()



