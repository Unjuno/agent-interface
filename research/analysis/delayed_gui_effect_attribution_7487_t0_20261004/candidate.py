#!/usr/bin/env python3
"""Render the frozen Issue #7487 synthetic source ledger into T0 stimuli."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DELAYS = (300, 1500)
FORMATS = ("CHRONOLOGICAL_SUMMARY", "SOURCE_BOUND_RECEIPT")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(case, delay, presentation):
    effect = case["effect"]
    events = []
    for action in case["actions"]:
        events.append({"kind": "action", **action})
    event = {"kind": "effect", "effect_id": effect["effect_id"],
             "target": effect["target"], "time_ms": effect["observed_at_ms"]}
    if presentation == "SOURCE_BOUND_RECEIPT":
        event["causal_link_status"] = effect["causal_link_status"]
        event["source_action_id"] = effect["source_action_id"]
        event["source_actor"] = effect["source_actor"]
        event["evidence_id"] = effect["evidence_id"]
    events.append(event)
    events.sort(key=lambda row: (row["time_ms"], row["kind"], row.get("action_id", row.get("effect_id", ""))))
    return {
        "case_id": case["case_id"],
        "display_delay_ms": delay,
        "effect_display_at_ms": effect["observed_at_ms"] + delay,
        "presentation": presentation,
        "events": events,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    ledger_path = HERE / "frozen_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    records = [render(case, delay, fmt) for case in ledger["cases"]
               for delay in DELAYS for fmt in FORMATS]
    args.out.mkdir(parents=True, exist_ok=False)
    raw = args.out / "presentations.jsonl"
    raw.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    manifest = {
        "schema": "unjuno.issue7487.t0.presentations.v1",
        "ledger_sha256": digest(ledger_path),
        "candidate_sha256": digest(Path(__file__)),
        "record_count": len(records),
        "records_sha256": digest(raw),
    }
    (args.out / "candidate_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
