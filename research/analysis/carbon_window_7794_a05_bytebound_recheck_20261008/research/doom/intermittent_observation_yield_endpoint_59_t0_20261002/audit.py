#!/usr/bin/env python3
"""Separate raw-only oracle and mutation audit; does not import candidate.py."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def independently_expected(source_sequence, source_health, event):
    interval = event["capture_interval_ns"]
    if event["clock_domain"] != "runtime-monotonic":
        return "YIELD_CLOCK_DOMAIN"
    if interval is None:
        return "YIELD_OBSERVATION_MISSING"
    if not isinstance(interval, list) or len(interval) != 2 or any(type(v) is not int for v in interval) or interval[0] > interval[1]:
        return "YIELD_CAPTURE_INTERVAL_MALFORMED"
    if event["available_at_ns"] < interval[0]:
        return "YIELD_CAPTURE_NOT_AVAILABLE"
    if interval[0] <= event["available_at_ns"] <= interval[1]:
        return "YIELD_CAPTURE_ORDER_UNKNOWN"
    if type(event["observation_sequence"]) is not int or event["observation_sequence"] <= source_sequence:
        return "YIELD_NON_FRESH"
    health = event["health"]
    if health.get("status") == "missing":
        return "YIELD_OBSERVATION_MISSING"
    if health.get("status") == "unavailable":
        return "YIELD_HEALTH_UNAVAILABLE"
    if health.get("status") != "observed" or type(health.get("value")) is not int or health["value"] < 0:
        return "YIELD_HEALTH_MALFORMED"
    if health["value"] < source_health:
        return "YIELD_HEALTH_LOSS"
    return "CONTINUE"


def audit(raw, fixture, candidate_bytes, fixture_bytes):
    errors = []
    if raw.get("schema") != "yield-capture-endpoint-raw-v1":
        errors.append("schema")
    if raw.get("allocation") != fixture.get("allocation"):
        errors.append("allocation")
    if raw.get("source_main") != fixture.get("source_main"):
        errors.append("source_main")
    if raw.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest():
        errors.append("fixture_hash")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest():
        errors.append("candidate_hash")
    if raw.get("source_sequence") != fixture.get("source_sequence"):
        errors.append("source_sequence")
    if raw.get("source_health") != fixture.get("source_health"):
        errors.append("source_health")
    rows = raw.get("rows")
    events = fixture.get("events")
    if not isinstance(rows, list) or len(rows) != len(events):
        return errors + ["row_count"]
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("event_id") in by_id:
            errors.append("duplicate_or_malformed_id")
        else:
            by_id[row["event_id"]] = row
    if set(by_id) != {event["id"] for event in events}:
        errors.append("row_identity_set")
    for event in events:
        row = by_id.get(event["id"])
        if row is None:
            continue
        if row.get("input") != event:
            errors.append("input:" + event["id"])
        expected = independently_expected(raw.get("source_sequence"), raw.get("source_health"), {"input": event}["input"])
        if row.get("decision") != expected or row.get("decision") != event["expected"]:
            errors.append("decision:" + event["id"])
        yielded = expected.startswith("YIELD_")
        if row.get("authority_granted") is not False:
            errors.append("authority:" + event["id"])
        if row.get("cover_terminated") is not yielded:
            errors.append("cover:" + event["id"])
        if row.get("fresh_admission_required_for_new_plan") is not yielded:
            errors.append("fresh_admission:" + event["id"])
    return errors


def main():
    fixture_bytes = (ROOT / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    raw = json.loads((ROOT / "results" / "formal-01" / "raw.json").read_bytes())
    candidate_bytes = (ROOT / "candidate.py").read_bytes()
    errors = audit(raw, fixture, candidate_bytes, fixture_bytes)
    mutations = {}
    mutated = copy.deepcopy(raw)
    next(row for row in mutated["rows"] if row["event_id"] == "at_end")["decision"] = "CONTINUE"
    mutations["decision"] = bool(audit(mutated, fixture, candidate_bytes, fixture_bytes))
    mutated = copy.deepcopy(raw)
    mutated["rows"][0]["authority_granted"] = True
    mutations["authority"] = bool(audit(mutated, fixture, candidate_bytes, fixture_bytes))
    mutated = copy.deepcopy(raw)
    mutated["rows"].pop()
    mutations["row_omission"] = bool(audit(mutated, fixture, candidate_bytes, fixture_bytes))
    mutations["candidate_hash"] = bool(audit(raw, fixture, candidate_bytes + b"mutation", fixture_bytes))
    result = {
        "status": "PASS_SYNTHETIC_ENDPOINT_CONTRACT_SCOPED" if not errors and all(mutations.values()) else "FAIL",
        "rows": len(raw.get("rows", [])),
        "errors": errors,
        "mutations_rejected": mutations,
        "independent_oracle": "separate function in audit.py; candidate module not imported",
        "scope": "synthetic endpoint predicate only; no runtime or live task",
    }
    path = ROOT / "results" / "formal-01" / "audit.json"
    if path.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_SYNTHETIC_ENDPOINT_CONTRACT_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
