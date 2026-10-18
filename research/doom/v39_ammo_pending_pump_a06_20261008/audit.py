"""Independent source and event-order auditor for the ammo pending-pump result."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RESULT_FIELDS = {
    "schema", "status", "main_commit", "planner_pending_at_observation",
    "source_health", "current_health", "source_ammo", "current_ammo",
    "ammo_hard_minimum", "terminal", "planner_interrupt_outcome", "events", "scope",
}


def _repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def validate_result(result, events):
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(
            ["git", "-C", str(_repo_root()), "show", f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(
            ["git", "-C", str(_repo_root()), "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"],
            text=True).strip()
        if blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
            raise ValueError(f"frozen source identity mismatch: {name}")
    expected = {
        "schema": "issue59-v39-ammo-pending-pump-result-a06",
        "status": "CONSTRUCTION_OBSERVATION",
        "main_commit": FREEZE["main_commit"],
        "planner_pending_at_observation": True,
        "source_health": 100,
        "current_health": 100,
        "source_ammo": 50,
        "current_ammo": 0,
        "ammo_hard_minimum": 1,
        "planner_interrupt_outcome": "requested",
        "scope": "Pinned production wait/pending-loop/cancel-helper AST slices with synthetic paired ammo rows and deterministic fakes only.",
    }
    if not isinstance(result, dict) or set(result) != RESULT_FIELDS:
        raise ValueError("result field set mismatch")
    for key, value in expected.items():
        if result.get(key) != value:
            raise ValueError(f"result claim mismatch: {key}")
    terminal_expected = {"event": "terminal", "id": "cover-1", "status": "cancelled",
                         "release": {"verified": True, "keys_down": [], "buttons_down": []}}
    if result.get("terminal") != terminal_expected:
        raise ValueError("terminal must prove cancelled empty release")
    if not isinstance(events, list) or result.get("events") != events:
        raise ValueError("raw event stream differs from result")
    kinds = [row.get("event") if isinstance(row, dict) else None for row in events]
    required = ["observation_enqueued", "planner_future_poll", "observation_dequeued",
                "monitor_received", "monitor_invalidated", "planner_interrupt_called",
                "executor_cancel_write", "executor_cancel_flush",
                "planner_interrupt_transport", "terminal_dequeued",
                "planner_interrupt_outcome", "verified_terminal_returned"]
    positions = []
    for event in required:
        if kinds.count(event) != 1:
            raise ValueError(f"event order requires exactly one {event}")
        positions.append(kinds.index(event))
    if positions != sorted(positions):
        raise ValueError("event order mismatch")
    poll = events[kinds.index("planner_future_poll")]
    observation = events[kinds.index("observation_dequeued")]
    received = events[kinds.index("monitor_received")]
    invalidation = events[kinds.index("monitor_invalidated")]
    if (poll.get("done") is not False or received.get("future_pending") is not True or
            observation.get("row_event") != "typed_observation" or
            observation.get("sequence") != received.get("sequence")):
        raise ValueError("paired observation was not delivered while planner remained pending")
    if (invalidation.get("reason") != "ammo:below_hard_minimum" or
            invalidation.get("requires_new_decision") is not True or
            invalidation.get("grants_input_authority") is not False):
        raise ValueError("ammo hard-invalidation disposition mismatch")
    if events[kinds.index("executor_cancel_write")] != {
            "event": "executor_cancel_write", "op": "cancel", "id": "cover-1"}:
        raise ValueError("executor cancel identity mismatch")
    if events[kinds.index("planner_interrupt_transport")].get("handle") != "turn-1":
        raise ValueError("planner interrupt handle mismatch")
    dequeued = events[kinds.index("terminal_dequeued")]
    if dequeued.get("release") != terminal_expected["release"]:
        raise ValueError("dequeued terminal does not verify empty release")
    return True


def main():
    result_path = HERE / "RESULT.json"
    events_path = HERE / "events.jsonl"
    audit_path = HERE / "AUDIT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    validate_result(result, events)
    if audit_path.exists():
        raise FileExistsError(f"refusing to overwrite {audit_path}")
    audit = {
        "schema": "issue59-v39-ammo-pending-pump-audit-a06-v1",
        "status": "PASS_CONSTRUCTION_EVENT_PUMP",
        "frozen_main": FREEZE["main_commit"],
        "event_rows": len(events),
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
        "checks": {
            "source_blobs_and_sha256_verified": True,
            "paired_ammo_zero_delivered_while_future_pending": True,
            "ammo_hard_crossing_reached_monitor": True,
            "executor_cancel_preceded_interrupt_transport": True,
            "terminal_verified_empty_after_interrupt": True,
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
