#!/usr/bin/env python3
"""Recompute one retained v39 health-feedback timing trace from frozen Git blobs."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
FREEZE_PATH = HERE / "FREEZE.json"


class AuditError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json(data: bytes, label: str) -> Any:
    try:
        return json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"{label}: invalid JSON: {exc}") from exc


def ms(delta_ns: int) -> float:
    return round(delta_ns / 1_000_000, 6)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def source_blob(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=HERE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AuditError(f"cannot read frozen source {path}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def analyze(freeze: dict[str, Any], blobs: dict[str, bytes]) -> dict[str, Any]:
    report = parse_json(blobs["report.json"], "report.json")
    score = parse_json(blobs["runtime/score.json"], "runtime/score.json")
    owners = parse_json(blobs["runtime/owner-events.json"], "owner-events.json")
    retention = parse_json(blobs["retention-manifest.json"], "retention-manifest.json")
    prompts = blobs["decision-2/prompt.txt"].decode("utf-8")
    events = [parse_json(line, f"events.jsonl line {i}") for i, line in enumerate(blobs["runtime/events.jsonl"].splitlines(), 1) if line]

    require(retention.get("schema") == "map01-v39-first-outcome-retention-v1", "unexpected retention manifest")
    indexed = {item["path"]: item for item in retention["files"]}
    for path, expected in freeze["members"].items():
        require(digest(blobs[path]) == expected, f"frozen SHA256 mismatch for {path}")
        require(path in indexed, f"retention manifest omits {path}")
        require(indexed[path]["sha256"] == expected, f"retention manifest SHA256 mismatch for {path}")
        require(indexed[path]["bytes"] == len(blobs[path]), f"retention manifest size mismatch for {path}")
    require(digest(blobs["retention-manifest.json"]) == freeze["retention_manifest_sha256"], "retention manifest changed")
    require(retention.get("allocation_id") == "map01-v39-coast-liveness-live-01", "wrong retained allocation")
    require(len(report.get("decisions", [])) >= 3, "report lacks the decision sequence under audit")

    d1, d2 = report["decisions"][1], report["decisions"][2]
    event = d1["cover_validity_latest_soft_event"]
    signal, outcome = event["signal"], event["outcome"]
    capture_ns = signal["capture_ns"]
    outcome_ns = event["outcome_evaluated_ns"]
    require(signal["sequence"] == 62 and signal["signal_id"] == "health" and signal["value"] == 85, "sequence-62 health signal mismatch")
    require(outcome["source_value"] == 97 and outcome["current_value"] == 85 and outcome["hard_minimum"] == 85, "health transition mismatch")
    require(outcome["status"] == "SOFT_CHANGED" and outcome["keep_existing_policy"] is True, "sequence-62 guard disposition mismatch")
    require(outcome["grants_input_authority"] is False and outcome["task_success_verified"] is False, "unexpected authority/success claim")
    require(d1["controller_model_started_ns"] < capture_ns < d1["controller_model_ended_ns"], "health signal was not during model wait")

    matching = [e for e in events if e.get("id") == "cover-1" and e.get("step") == 5]
    hold_start = next((e for e in matching if e.get("event") == "step_started"), None)
    held = next((e for e in matching if e.get("event") == "keys_held"), None)
    hold_done = next((e for e in matching if e.get("event") == "step_completed"), None)
    require(hold_start and held and hold_done, "step-5 hold trace incomplete")
    require(held.get("keys") == ["a"], "step-5 admitted key mismatch")
    require(hold_start["issued_ns"] < held["input_ack_ns"] < capture_ns < hold_done["completed_ns"], "capture/hold event ordering mismatch")

    later_keys = [e for e in events if e.get("id") == "cover-1" and e.get("event") == "keys_held" and e.get("step") == 6]
    require(len(later_keys) == 1 and later_keys[0].get("keys") == ["Down", "space"], "step-6 input trace mismatch")
    next_key_ack_ns = later_keys[0]["input_ack_ns"]
    require(capture_ns < next_key_ack_ns < d1["controller_model_ended_ns"], "next key acknowledgement ordering mismatch")

    terminals = [e for e in events if e.get("id") == "cover-1" and e.get("event") == "terminal"]
    require(len(terminals) == 1, "cover-1 terminal count mismatch")
    release = terminals[0].get("interruption", {}).get("record", {})
    require(release.get("event") == "owner_release" and release.get("verified") is True, "missing verified empty owner release")
    require(release.get("keys_down") == [] and release.get("buttons_down") == [], "release was not verified empty")
    release_ns = release["verified_ns"]
    require(release_ns > next_key_ack_ns, "release precedes later input")

    prompt_evidence = all(piece in prompts for piece in ('"current_value":85', '"effect":"prior_cover_preserved"', '"sequence":62', '"grants_input_authority":false'))
    require(prompt_evidence, "decision-2 prompt does not expose the expected health feedback")
    current = d2["final_action_admission"]
    require(current["status"] == "REJECTED_ACTION_NOT_CURRENT", "decision-2 action was not rejected stale")
    validity = current["action_validity"]
    require(validity["reason"] == "health_max_decrease_from_source_failed", "decision-2 rejection reason mismatch")
    require(validity["contract"]["source"]["signals"]["health"]["value"] == 85, "decision-2 source health mismatch")
    require(validity["snapshot"]["signals"]["health"]["value"] == 73, "decision-2 current health mismatch")

    own_releases = [e for e in owners if e.get("event") == "owner_release" and e.get("verified") is True and e.get("keys_down") == []]
    require(any(e.get("verified_ns") == release_ns for e in own_releases), "owner ledger does not confirm terminal release")
    normal_up_events = [e for e in events if e.get("id") == "cover-1" and (e.get("event") in ("key_up", "input_released") or e.get("operation") == "key_up")]
    require(not normal_up_events, "unexpected per-key up event; update the audit to review it")

    feedback_to_outcome = outcome_ns - capture_ns
    capture_to_hold_completion = hold_done["completed_ns"] - capture_ns
    capture_to_next_input_ack = next_key_ack_ns - capture_ns
    capture_to_empty_release = release_ns - capture_ns
    return {
        "schema": "v39-health-feedback-timing-result-v1",
        "source_commit": freeze["source_commit"],
        "allocation": retention["allocation_id"],
        "evidence_class": "posthoc retained single-allocation trace audit",
        "measurements": {
            "health_capture_ns": capture_ns,
            "health_monitor_outcome_ns": outcome_ns,
            "feedback_to_outcome_ms": ms(feedback_to_outcome),
            "model_wait_start_ns": d1["controller_model_started_ns"],
            "model_wait_end_ns": d1["controller_model_ended_ns"],
            "feedback_to_model_terminal_ms": ms(d1["controller_model_ended_ns"] - capture_ns),
            "hold_key_ack_ns": held["input_ack_ns"],
            "hold_step_completion_ns": hold_done["completed_ns"],
            "feedback_to_hold_step_completion_ms": ms(capture_to_hold_completion),
            "next_step_keys_ack_ns": next_key_ack_ns,
            "feedback_to_next_step_keys_ack_ms": ms(capture_to_next_input_ack),
            "verified_empty_owner_release_ns": release_ns,
            "feedback_to_verified_empty_owner_release_ms": ms(capture_to_empty_release),
            "normal_per_key_up_receipt_present": False
        },
        "state": {
            "health_source": outcome["source_value"],
            "health_at_capture": outcome["current_value"],
            "guard_status": outcome["status"],
            "cover_preserved": outcome["keep_existing_policy"],
            "feedback_granted_authority": outcome["grants_input_authority"],
            "first_pending_action_admission": d1["final_action_admission"]["status"],
            "next_pending_action_admission": current["status"],
            "next_action_health_source": validity["contract"]["source"]["signals"]["health"]["value"],
            "next_action_health_current": validity["snapshot"]["signals"]["health"]["value"],
            "map_exit": score["map_exit"],
            "episode_finished": score["episode_finished"],
            "kill_count": score["kill_count"],
            "death_count": score["death_count"],
            "reward": score["reward"]
        },
        "interpretation_limits": [
            "The measured signal is an adverse health change, not positive task-effect onset.",
            "The verified empty owner release is a program-level release after later inputs; it is not a per-key up timestamp or key dwell measurement.",
            "The subsequent model action was rejected because current health decreased beyond its authored predicate.",
            "The post-control score records no MAP01 exit and an unfinished episode; this is not a task success or recovery-benefit result.",
            "One retained run cannot establish matched-condition performance or a general timing distribution."
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", type=Path, help="write RESULT.json (default: print to stdout)")
    args = parser.parse_args()
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    paths = set(freeze["members"]) | {"retention-manifest.json"}
    blobs = {path: source_blob(freeze["source_commit"], f"{freeze['allocation']}/{path}") for path in paths}
    result = analyze(freeze, blobs)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.write.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditError as exc:
        print(f"AUDIT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
