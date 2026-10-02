#!/usr/bin/env python3
"""One-shot finite candidate invocation. Writes only the fresh package output."""
import hashlib
import json
from pathlib import Path

from candidate import decide

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results" / "formal-01" / "raw.json"


def main():
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture_bytes = (ROOT / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    candidate_bytes = (ROOT / "candidate.py").read_bytes()
    rows = []
    for event in fixture["events"]:
        decision = decide(fixture["source_sequence"], fixture["source_health"], event)
        rows.append({
            "event_id": event["id"],
            "input": event,
            "decision": decision,
            "authority_granted": False,
            "cover_terminated": decision.startswith("YIELD_"),
            "fresh_admission_required_for_new_plan": decision.startswith("YIELD_"),
        })
    raw = {
        "schema": "yield-capture-endpoint-raw-v1",
        "allocation": fixture["allocation"],
        "source_main": fixture["source_main"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "source_sequence": fixture["source_sequence"],
        "source_health": fixture["source_health"],
        "rows": rows,
        "assertion_scope": "five finite synthetic integer-time boundary cases; no runtime or live task",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=False)
    OUTPUT.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "CANDIDATE_COMPLETE",
        "rows": len(rows),
        "continue": sum(row["decision"] == "CONTINUE" for row in rows),
        "yield": sum(row["decision"].startswith("YIELD_") for row in rows),
        "raw_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
