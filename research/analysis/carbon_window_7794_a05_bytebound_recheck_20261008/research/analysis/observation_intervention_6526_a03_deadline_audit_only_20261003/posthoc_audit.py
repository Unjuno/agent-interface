"""Audit-only timing review of the immutable Issue #6526 A02 raw trace."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def event_time_effect_present(payload: dict | None, expected: dict, persisted_ns: int, deadline_ns: int) -> bool:
    return payload == expected and persisted_ns <= deadline_ns


def timing_disposition(lags_ns: list[int], errors: list[str]) -> str:
    if errors:
        return "STOP_REVIEW_ERRORS"
    return "HOLD_AUDIT_TIMING" if any(lag > 0 for lag in lags_ns) else "EXACT_DEADLINE_SAMPLES"


def review(root: Path) -> dict:
    root = Path(root)
    output_dir = root / "formal-output" if (root / "formal-output").is_dir() else root
    trials_path = root / "formal-trials.json"
    if not trials_path.is_file():
        trials_path = output_dir / "formal-trials.json"
    original_path = root / "original-audit.json"
    if not original_path.is_file():
        original_path = root.parent / "audit.json"
    trials = json.loads(trials_path.read_text())
    events = load_jsonl(output_dir / "app-events.jsonl")
    original = json.loads(original_path.read_text())
    receipt = json.loads((output_dir / "candidate-receipt.json").read_text())
    grouped: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        grouped[event.get("kind", "<missing>")].append(event)
    starts = grouped["trial_start"]
    start_by_id = {event.get("trial_id"): event for event in starts}
    actions_by_id: dict[str, list[dict]] = defaultdict(list)
    for event in grouped["action_effect"]:
        actions_by_id[event.get("trial_id")].append(event)
    deadlines = {event.get("trial_id"): event for event in grouped["deadline_observed"]}
    errors: list[str] = []
    if receipt.get("exit_code") != 0 or receipt.get("trial_count") != 180:
        errors.append("original-candidate-receipt-mismatch")
    ids = [row["trial_id"] for row in trials]
    if len(trials) != 180 or [event.get("trial_id") for event in starts] != ids:
        errors.append("allocation-or-start-order-mismatch")
    if len(start_by_id) != len(starts) or len(deadlines) != len(grouped["deadline_observed"]):
        errors.append("duplicate-start-or-deadline")
    if set(actions_by_id) != {row["trial_id"] for row in trials}:
        errors.append("action-trial-id-set-mismatch")

    lags_ms: list[float] = []
    exact_outcomes: dict[str, bool] = {}
    disagreements: list[dict] = []
    by_cell: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in trials:
        tid = row["trial_id"]
        start = start_by_id.get(tid)
        action_list = actions_by_id.get(tid, [])
        raw_deadline_path = output_dir / f"deadline-{tid}.json"
        effect_path = output_dir / f"effect-{tid}.json"
        try:
            snapshot = json.loads(raw_deadline_path.read_text())
        except (OSError, json.JSONDecodeError):
            errors.append(f"deadline-record-invalid:{tid}")
            continue
        if start is None or len(action_list) != 1:
            errors.append(f"start-or-action-count:{tid}")
            continue
        action = action_list[0]
        deadline_ns = start["start_ns"] + row["deadline_ms"] * 1_000_000
        snapshot_ns = snapshot.get("snapshot_ns", 0)
        lag_ns = snapshot_ns - deadline_ns
        lags_ms.append(lag_ns / 1_000_000)
        if snapshot.get("deadline_ns") != deadline_ns or snapshot.get("trial_id") != tid:
            errors.append(f"nominal-deadline-binding:{tid}")
        if lag_ns < 0:
            errors.append(f"snapshot-before-deadline:{tid}")
        if deadlines.get(tid, {}).get("deadline_ns") != deadline_ns:
            errors.append(f"deadline-event-binding:{tid}")
        if deadlines.get(tid, {}).get("effect_present") != snapshot.get("effect_present"):
            errors.append(f"snapshot-event-disagreement:{tid}")
        persisted_ns = action.get("persisted_ns", 0)
        if action.get("action_ns", 0) > persisted_ns:
            errors.append(f"invalid-action-persistence-order:{tid}")
        expected_payload = {"trial_id": tid, "value": row["expected_value"]}
        try:
            payload = json.loads(effect_path.read_text())
        except (OSError, json.JSONDecodeError):
            payload = None
        if payload != expected_payload:
            errors.append(f"effect-file-payload:{tid}")
        if snapshot.get("effect_payload") not in (None, expected_payload):
            errors.append(f"snapshot-payload:{tid}")
        on_time = event_time_effect_present(payload, expected_payload, persisted_ns, deadline_ns)
        exact_outcomes[tid] = on_time
        cell = (row["schedule"], row["arm"])
        by_cell[cell]["n"] += 1
        by_cell[cell]["misses"] += not on_time
        if bool(snapshot.get("effect_present")) != on_time:
            disagreements.append({
                "trial_id": tid,
                "schedule": row["schedule"],
                "arm": row["arm"],
                "deadline_ns": deadline_ns,
                "snapshot_ns": snapshot_ns,
                "snapshot_lag_ms": lag_ns / 1_000_000,
                "persisted_ns": persisted_ns,
                "persisted_after_deadline_ms": (persisted_ns - deadline_ns) / 1_000_000,
                "snapshot_effect_present": bool(snapshot.get("effect_present")),
                "event_time_effect_present": on_time,
            })

    if set(start_by_id) != set(ids) or set(deadlines) != set(ids):
        errors.append("start-or-deadline-set-mismatch")
    timing_gate = timing_disposition([round(lag * 1_000_000) for lag in lags_ms], errors)
    descriptive = {
        f"{schedule}/{arm}": {
            "n": counts["n"],
            "misses_by_raw_persisted_timestamp": counts["misses"],
            "miss_rate_descriptive": counts["misses"] / counts["n"] if counts["n"] else None,
        }
        for (schedule, arm), counts in sorted(by_cell.items())
    }
    return {
        "schema": "issue6526-a03-audit-only-timing-review-v1",
        "disposition": timing_gate,
        "errors": errors,
        "candidate_invocations": 0,
        "corrective_auditor_invocations": 1,
        "trial_count": len(exact_outcomes),
        "snapshot_lag_ms": {
            "min": min(lags_ms) if lags_ms else None,
            "max": max(lags_ms) if lags_ms else None,
            "after_nominal_deadline_count": sum(lag > 0 for lag in lags_ms),
            "exact_deadline_count": sum(lag == 0 for lag in lags_ms),
        },
        "original_audit_decision": original.get("decision"),
        "original_audit_errors": original.get("errors"),
        "original_candidate_receipt": receipt,
        "event_time_reconstruction_descriptive_only": descriptive,
        "snapshot_vs_event_time_disagreements": disagreements,
        "h_classification": "NOT_EVALUATED_AUDIT_TIMING_GATE_UNRESOLVED",
    }
