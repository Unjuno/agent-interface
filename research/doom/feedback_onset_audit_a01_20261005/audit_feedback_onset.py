#!/usr/bin/env python3
"""Raw-only, stdlib audit of useful-feedback onset availability in retained V39."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

TASK_EVENTS = {"task_effect", "scored_task_effect", "kill", "enemy_killed", "map_exit", "objective_complete"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", type=Path, required=True)
    args = ap.parse_args()
    root = args.trace
    manifest = json.loads((root / "retention-manifest.json").read_text(encoding="utf-8"))
    pinned = {f["path"]: f for f in manifest["files"]}
    for name in ("runtime/events.jsonl", "report.json"):
        path = root / name
        if path.stat().st_size != pinned[name]["bytes"] or sha(path) != pinned[name]["sha256"]:
            raise SystemExit("STOP_PROVENANCE_MISMATCH:" + name)
    events = [json.loads(s) for s in (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    counts = collections.Counter(e.get("event", "<missing>") for e in events)
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    receipts = [r for d in report["decisions"] for r in d.get("effect_receipts", [])]
    visible = [r for r in receipts if r.get("result") == "visible_change"]
    scores = [e for e in events if e.get("event") == "post_control_score"]
    task_events = [e for e in events if e.get("event") in TASK_EVENTS]
    if (manifest["allocation_id"] != "map01-v39-coast-liveness-live-01"
            or len(events) != 634 or counts["input_admission"] != 39
            or counts["input_released"] != 1
            or counts["input_release_measurement"] != 0
            or counts["input_release_transition"] != 0
            or len(scores) != 1 or task_events
            or len(visible) != 4
            or {r.get("scope") for r in visible} != {"viewport pixels only"}):
        raise SystemExit("STOP_EVENT_SHAPE_CHANGED")
    other_emits = [e["emit_ns"] for e in events if e.get("event") != "post_control_score" and isinstance(e.get("emit_ns"), int)]
    score = scores[0]
    out = {
        "schema": "issue59-feedback-onset-audit-a01",
        "allocation_id": manifest["allocation_id"],
        "event_sha256": pinned["runtime/events.jsonl"]["sha256"],
        "report_sha256": pinned["report.json"]["sha256"],
        "event_count": len(events),
        "input_admission_count": counts["input_admission"],
        "aggregate_release_count": counts["input_released"],
        "per_key_release_measurement_count": counts["input_release_measurement"],
        "per_key_release_transition_count": counts["input_release_transition"],
        "post_control_score_count": len(scores),
        "post_control_score_emit_ns": score.get("emit_ns"),
        "latest_other_event_emit_ns": max(other_emits),
        "post_control_score": {k: score.get(k) for k in ("map", "kill_count", "death_count", "map_exit", "episode_finished")},
        "in_run_task_effect_event_count": len(task_events),
        "visible_viewport_receipt_count": len(visible),
        "visible_receipt_scopes": ["viewport pixels only"],
        "disposition": "NO_INDEPENDENT_USEFUL_FEEDBACK_ONSET_IN_RETAINED_TRACE",
        "scope": "single retained live episode; read-only; no new allocation",
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
