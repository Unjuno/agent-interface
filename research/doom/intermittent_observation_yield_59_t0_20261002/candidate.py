#!/usr/bin/env python3
"""Finite model of a no-authority continuation guard during planner wait."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOCATION = "MAP01-INTERMITTENT-OBSERVATION-YIELD-59-T0-20261002-01"
OUTPUT = ROOT / "results" / "formal-01" / "candidate.json"


def decide(source_sequence: int, source_health: int, event: dict) -> str:
    if event["clock_domain"] != "runtime-monotonic":
        return "YIELD_CLOCK_DOMAIN"
    interval = event["capture_interval_ns"]
    if interval is None:
        return "YIELD_OBSERVATION_MISSING"
    if len(interval) != 2 or any(type(v) is not int for v in interval) or interval[0] > interval[1]:
        return "YIELD_CAPTURE_INTERVAL_MALFORMED"
    if interval[0] > event["available_at_ns"]:
        return "YIELD_CAPTURE_NOT_AVAILABLE"
    if interval[0] <= event["available_at_ns"] < interval[1]:
        return "YIELD_CAPTURE_ORDER_UNKNOWN"
    sequence = event["observation_sequence"]
    if type(sequence) is not int or sequence <= source_sequence:
        return "YIELD_NON_FRESH"
    health = event["health"]
    if health.get("status") == "missing":
        return "YIELD_OBSERVATION_MISSING"
    if health.get("status") == "unavailable":
        return "YIELD_HEALTH_UNAVAILABLE"
    if health.get("status") != "observed":
        return "YIELD_HEALTH_MALFORMED"
    value = health.get("value")
    if type(value) is not int or value < 0:
        return "YIELD_HEALTH_MALFORMED"
    if value < source_health:
        return "YIELD_HEALTH_LOSS"
    return "CONTINUE"


def main() -> int:
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture_bytes = (ROOT / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    if fixture["allocation"] != ALLOCATION:
        raise SystemExit("STOP_ALLOCATION_MISMATCH")
    source = Path(__file__).read_bytes()
    rows = []
    for event in fixture["events"]:
        result = decide(fixture["source_sequence"], fixture["source_health"], event)
        rows.append({
            "event_id": event["id"],
            "input": event,
            "decision": result,
            "authority_granted": False,
            "cover_terminated": result.startswith("YIELD_"),
            "fresh_admission_required_for_new_plan": result.startswith("YIELD_"),
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=False)
    raw = {
        "schema": "intermittent-observation-yield-raw-v1",
        "allocation": ALLOCATION,
        "source_main": fixture["source_main"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(source).hexdigest(),
        "source_sequence": fixture["source_sequence"],
        "source_health": fixture["source_health"],
        "rows": rows,
        "assertion_scope": "finite synthetic guard-policy model; no runtime or live task",
    }
    OUTPUT.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(rows),
                      "continue": sum(row["decision"] == "CONTINUE" for row in rows),
                      "yield": sum(row["decision"].startswith("YIELD_") for row in rows),
                      "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
