"""Independent source, event-order, and typed-claim auditor."""
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RESULT_FIELDS = {
    "schema", "status", "main_commit", "planner_pending_at_observation",
    "source_health", "current_health", "hard_minimum", "terminal",
    "planner_interrupt_outcome", "events", "scope",
}


def _json_equal(actual, expected):
    return json.dumps(actual, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) == json.dumps(
                          expected, sort_keys=True, separators=(",", ":"),
                          allow_nan=False)


def _verify_sources(repo=None):
    repo = Path(repo) if repo is not None else _repo_root()
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"],
            text=True).strip()
        if (blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]):
            raise ValueError(f"frozen source identity mismatch: {name}")


def _repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def validate_result(result, events, freeze=None, repo=None):
    freeze = FREEZE if freeze is None else freeze
    _verify_sources(repo)
    expected_top = {
        "schema": "issue59-v39-observation-pump-event-dispatch-result-a02",
        "status": "CONSTRUCTION_OBSERVATION",
        "main_commit": freeze["main_commit"],
        "planner_pending_at_observation": True,
        "source_health": 100,
        "current_health": 84,
        "hard_minimum": 88,
        "planner_interrupt_outcome": "requested",
        "scope": "Pinned production wait/pending-loop/cancel-helper AST slices with synthetic rows and deterministic fakes only.",
    }
    if not isinstance(result, dict) or set(result) != RESULT_FIELDS:
        raise ValueError("result field set mismatch")
    for key, value in expected_top.items():
        if not _json_equal(result.get(key), value):
            label = ("planner pending" if key == "planner_pending_at_observation" else key)
            raise ValueError(f"{label} claim mismatch")
    if not _json_equal(result.get("terminal"), {
            "event": "terminal", "id": "cover-1", "status": "cancelled",
            "release": {"verified": True, "keys_down": [], "buttons_down": []}}):
        raise ValueError("terminal must verify empty release")
    if not isinstance(events, list) or not _json_equal(result.get("events"), events):
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
    received = events[kinds.index("monitor_received")]
    invalidation = events[kinds.index("monitor_invalidated")]
    future_poll = events[kinds.index("planner_future_poll")]
    observed = events[kinds.index("observation_dequeued")]
    if (future_poll.get("done") is not False or received.get("future_pending") is not True or
            observed.get("row_event") != "typed_observation" or
            received.get("sequence") != observed.get("sequence")):
        raise ValueError("monitor delivery did not occur on typed input while planner pending")
    if (invalidation.get("reason") != "health:below_hard_minimum" or
            invalidation.get("requires_new_decision") is not True or
            invalidation.get("grants_input_authority") is not False):
        raise ValueError("monitor invalidation disposition mismatch")
    cancel = events[kinds.index("executor_cancel_write")]
    if cancel != {"event": "executor_cancel_write", "op": "cancel", "id": "cover-1"}:
        raise ValueError("cancel command identity mismatch")
    interrupt = events[kinds.index("planner_interrupt_transport")]
    if interrupt.get("handle") != "turn-1":
        raise ValueError("planner interrupt handle mismatch")
    terminal_event = events[kinds.index("terminal_dequeued")]
    if not _json_equal(terminal_event.get("release"),
                       {"verified": True, "keys_down": [], "buttons_down": []}):
        raise ValueError("terminal event must verify empty release")
    return True


def main():
    result_path = HERE / "RESULT.json"
    raw_path = HERE / "events.jsonl"
    audit_path = HERE / "AUDIT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    events = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    validate_result(result, events)
    if audit_path.exists():
        raise FileExistsError(f"refusing to overwrite {audit_path}")
    audit = {
        "schema": "issue59-v39-observation-pump-event-dispatch-audit-v1",
        "status": "PASS_CONSTRUCTION_EVENT_PUMP",
        "frozen_main": FREEZE["main_commit"],
        "event_rows": len(events),
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "events_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "checks": {
            "source_blobs_and_sha256_verified": True,
            "typed_observation_delivered_while_future_pending": True,
            "health_hard_crossing_reached_monitor": True,
            "executor_cancel_preceded_planner_interrupt_transport": True,
            "terminal_followed_interrupt_and_verified_empty_release": True,
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
