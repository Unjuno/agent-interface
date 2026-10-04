#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[2]
OUT = HERE / "results/construction-a01"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    for relative, expected in freeze["source_sha256"].items():
        path = WORKTREE / relative
        if not path.is_file() or sha(path.read_bytes()) != expected:
            errors.append("source_sha256:" + relative)

    raw_path = OUT / "candidate-events.jsonl"
    result_path = OUT / "result.json"
    if not raw_path.is_file() or not result_path.is_file():
        errors.append("candidate_artifact_missing")
        raw = b""
        result = {}
    else:
        raw = raw_path.read_bytes()
        result = json.loads(result_path.read_text(encoding="utf-8"))
    rows = []
    try:
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append("candidate_jsonl:" + type(exc).__name__)

    if sha(raw) != result.get("candidate", {}).get("events_sha256"):
        errors.append("candidate_raw_sha256")
    if result.get("run_id") != freeze.get("run_id"):
        errors.append("run_id")
    if result.get("base_commit") != freeze.get("base_commit"):
        errors.append("base_commit")
    if result.get("status") != "CANDIDATE_EXECUTED":
        errors.append("candidate_status")
    if result.get("environment") != {
            "fake_x_display": True, "os_input": False, "gui_capture": False,
            "vizdoom": False, "model_calls": 0, "docker": False}:
        errors.append("environment_scope")

    if len(rows) != 2:
        errors.append("expected_two_events")
    else:
        down, up = rows
        if [down.get("event"), up.get("event")] != ["input_admission", "input_release_measurement"]:
            errors.append("event_order")
        expected_context = ("cover-7", 2, "intent-v39-a01")
        for row in rows:
            if (row.get("id"), row.get("step"), row.get("intent_token")) != expected_context:
                errors.append("program_step_intent_binding")
        d = down.get("physical_key_measurement", {})
        u = up.get("physical_key_measurement", {})
        if d.get("classification") != "CONFIRMED_PHYSICAL_DOWN":
            errors.append("confirmed_down")
        if u.get("classification") != "CONFIRMED_PHYSICAL_UP":
            errors.append("confirmed_up")
        aid = d.get("actuation_id")
        if not aid or u.get("actuation_id") != aid or u.get("identity_status") != "RETIRED":
            errors.append("actuation_identity_link")
        edge = u.get("adapter_edge", {})
        interval = edge.get("interval")
        if (edge.get("edge") != "up" or edge.get("status") != "CONFIRMED_PHYSICAL_UP"
                or edge.get("intent_token") != "intent-v39-a01" or edge.get("key") != "F8"
                or edge.get("actuation_id") != aid or type(interval) is not list
                or len(interval) != 2 or type(interval[0]) is not int
                or type(interval[1]) is not int or interval[0] > interval[1]):
            errors.append("per_key_up_edge")
        if edge.get("grants_input_authority") is not False:
            errors.append("edge_authority")
        if d.get("grants_input_authority") is not False or u.get("grants_input_authority") is not False:
            errors.append("measurement_authority")
        if u.get("application_consumption_observed") is not False:
            errors.append("application_effect_scope")
        if result.get("candidate", {}).get("fake_physical_keys_after_up") != []:
            errors.append("fake_key_not_released")
        if result.get("candidate", {}).get("backend_held_after_up") != []:
            errors.append("backend_hold_not_cleared")

    audit = {
        "schema": "map01-v39-perkey-bridge-construction-audit-v1",
        "run_id": freeze["run_id"],
        "status": "PASS_CONSTRUCTION" if not errors else "FAIL_AUDIT",
        "candidate_events_sha256": sha(raw),
        "event_count": len(rows),
        "errors": errors,
        "scope": "synthetic adapter and fake-display owner behavior only; no live v39, GUI, task-effect, or benefit evidence",
    }
    (OUT / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps({"status": audit["status"], "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
