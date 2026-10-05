#!/usr/bin/env python3
"""Candidate retrieval-label contract. Deliberately does not open oracle.json."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture.json"
OUT = ROOT / "results" / "candidate.json"


def choose(case):
    if not case["history_required"]:
        return "NONE"
    if not case["identity_unique"] or not case["source_hash"] or not case["lineage_linear"]:
        return "ABSTAIN"
    source_bytes = json.dumps(case["source"], sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(source_bytes).hexdigest() != case["source_hash"]:
        return "ABSTAIN"
    events = case["source"].get("event_ids")
    if not isinstance(events, list) or len(events) != 2 or len(set(events)) != 2:
        return "ABSTAIN"
    return "EVENT_CHAIN"


def main():
    fixture = json.loads(FIXTURE.read_text())
    rows = []
    for case in fixture["cases"]:
        label = choose(case)
        rows.append({
            "case_id": case["case_id"], "label": label,
            "source_hash": case["source_hash"],
            "event_ids": case["source"]["event_ids"] if label == "EVENT_CHAIN" else [],
            "authority_granted": False, "authority_scope": None,
        })
    OUT.parent.mkdir(parents=True, exist_ok=False)
    OUT.write_text(json.dumps({"schema": "task-memory-t0-candidate-v1", "rows": rows}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"case_count": len(rows), "output": str(OUT), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
