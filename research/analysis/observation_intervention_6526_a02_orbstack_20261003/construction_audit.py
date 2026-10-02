"""Small construction-only raw audit; never classifies A02 scientific data."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def audit(root: Path, expected: list[dict]) -> dict:
    events = [json.loads(line) for line in (root/"app-events.jsonl").read_text().splitlines()]
    by_kind: dict[str, list[dict]] = {}
    for event in events:
        by_kind.setdefault(event["kind"], []).append(event)
    starts = {event["trial_id"]: event for event in by_kind.get("trial_start", [])}
    schedules = {event["trial_id"]: event for event in by_kind.get("action_schedule", [])}
    actions: dict[str, list[dict]] = {}
    for event in by_kind.get("action_effect", []):
        actions.setdefault(event["trial_id"], []).append(event)
    errors = []
    ids = [row["trial_id"] for row in expected]
    if len(ids) != 6 or set(starts) != set(ids) or len(by_kind.get("trial_start", [])) != 6:
        errors.append("six-start-set-mismatch")
    if set(schedules) != set(ids) or len(by_kind.get("action_schedule", [])) != 6:
        errors.append("six-schedule-set-mismatch")
    if set(actions) != set(ids) or any(len(actions.get(tid, [])) != 1 for tid in ids):
        errors.append("six-action-set-mismatch")
    if len(by_kind.get("deadline_observed", [])) != 6:
        errors.append("six-deadline-set-mismatch")
    for row in expected:
        tid = row["trial_id"]
        if tid not in starts or tid not in schedules or tid not in actions:
            continue
        start, schedule, action = starts[tid], schedules[tid], actions[tid][0]
        arm_offset = schedule["scheduled_ns"]-start["start_ns"]
        callback_delay = action["action_ns"]-schedule["scheduled_ns"]
        if schedule["delay_ms"] != 90 or not 0 <= arm_offset <= 5_000_000:
            errors.append(f"schedule-origin-invalid:{tid}")
        if action["scheduled_ns"] != schedule["scheduled_ns"] or callback_delay < 90_000_000:
            errors.append(f"action-schedule-binding-invalid:{tid}")
        if not (root/f"deadline-{tid}.json").is_file():
            errors.append(f"deadline-file-missing:{tid}")
        if row["arm"] == "SCREENSHOT" and not any(e.get("trial_id") == tid for e in by_kind.get("screenshot", [])):
            errors.append(f"screenshot-missing:{tid}")
        if row["arm"] == "SHAM" and not any(e.get("trial_id") == tid for e in by_kind.get("sham", [])):
            errors.append(f"sham-missing:{tid}")
    if by_kind.get("screenshot_error"):
        errors.append("screenshot-errors-present")
    receipt = json.loads((root/"candidate-receipt.json").read_text())
    if receipt.get("exit_code") != 0 or receipt.get("trial_count") != 6:
        errors.append("candidate-receipt-invalid")
    rates = Counter((row["schedule"], row["arm"]) for row in expected)
    if len(rates) != 6 or any(count != 1 for count in rates.values()):
        errors.append("construction-allocation-unbalanced")
    return {"scope": "construction-only", "decision": "CONSTRUCTION_METHOD_PASS" if not errors else "STOP_CONSTRUCTION_AUDIT",
            "errors": errors, "trial_count": len(expected), "schedule_count": len(schedules),
            "action_count": sum(map(len, actions.values())),
            "deadline_count": len(by_kind.get("deadline_observed", [])),
            "capture_count": len(by_kind.get("screenshot", [])),
            "sham_tick_count": len(by_kind.get("sham", [])),
            "screenshot_error_count": len(by_kind.get("screenshot_error", []))}


if __name__ == "__main__":
    raw, trial_path, result_path = map(Path, sys.argv[1:4])
    result = audit(raw, json.loads(trial_path.read_text()))
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "CONSTRUCTION_METHOD_PASS" else 1)
