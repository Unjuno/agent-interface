#!/usr/bin/env python3
"""Independent raw-only oracle; deliberately does not import candidate.py."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "fresh_same_state": "CONTINUE",
    "fresh_health_loss": "YIELD_HEALTH_LOSS",
    "fresh_health_gain": "CONTINUE",
    "stale_sequence": "YIELD_NON_FRESH",
    "missing_observation": "YIELD_OBSERVATION_MISSING",
    "unavailable_health": "YIELD_HEALTH_UNAVAILABLE",
    "malformed_health": "YIELD_HEALTH_MALFORMED",
    "wrong_clock_domain": "YIELD_CLOCK_DOMAIN",
    "future_capture_interval": "YIELD_CAPTURE_NOT_AVAILABLE",
    "capture_straddles_decision": "YIELD_CAPTURE_ORDER_UNKNOWN",
}


def independently_expected(source_sequence: int, source_health: int, row: dict) -> str:
    value = row["input"]
    health = value["health"]
    interval = value["capture_interval_ns"]
    if value["clock_domain"] != "runtime-monotonic":
        return "YIELD_CLOCK_DOMAIN"
    if interval is None:
        return "YIELD_OBSERVATION_MISSING"
    if not isinstance(interval, list) or len(interval) != 2 or not all(type(x) is int for x in interval) or interval[0] > interval[1]:
        return "YIELD_CAPTURE_INTERVAL_MALFORMED"
    if interval[0] > value["available_at_ns"]:
        return "YIELD_CAPTURE_NOT_AVAILABLE"
    if interval[0] <= value["available_at_ns"] <= interval[1]:
        return "YIELD_CAPTURE_ORDER_UNKNOWN"
    seq = value["observation_sequence"]
    if type(seq) is not int or seq <= source_sequence:
        return "YIELD_NON_FRESH"
    if health.get("status") == "missing":
        return "YIELD_OBSERVATION_MISSING"
    if health.get("status") == "unavailable":
        return "YIELD_HEALTH_UNAVAILABLE"
    if health.get("status") != "observed" or type(health.get("value")) is not int or health["value"] < 0:
        return "YIELD_HEALTH_MALFORMED"
    if health["value"] < source_health:
        return "YIELD_HEALTH_LOSS"
    return "CONTINUE"


def audit(raw: dict, fixture: dict, candidate_bytes: bytes) -> list[str]:
    errors = []
    if raw.get("schema") != "intermittent-observation-yield-raw-v1": errors.append("schema")
    if raw.get("allocation") != fixture.get("allocation"): errors.append("allocation")
    if raw.get("source_main") != fixture.get("source_main"): errors.append("source_main")
    if raw.get("fixture_sha256") != hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(): errors.append("fixture_hash")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest(): errors.append("candidate_hash")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED): return errors + ["row_count"]
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("event_id") in by_id:
            errors.append("duplicate_or_malformed_id")
        else:
            by_id[row["event_id"]] = row
    if set(by_id) != set(EXPECTED): errors.append("row_identity_set")
    for event in fixture["events"]:
        row = by_id.get(event["id"])
        if row is None: continue
        if row.get("input") != event: errors.append("input:" + event["id"])
        decision = independently_expected(fixture["source_sequence"], fixture["source_health"], row)
        if decision != EXPECTED[event["id"]] or row.get("decision") != decision:
            errors.append("decision:" + event["id"])
        yielding = decision.startswith("YIELD_")
        if row.get("authority_granted") is not False: errors.append("authority:" + event["id"])
        if row.get("cover_terminated") is not yielding: errors.append("cover_state:" + event["id"])
        if row.get("fresh_admission_required_for_new_plan") is not yielding: errors.append("new_plan_gate:" + event["id"])
    return sorted(set(errors))


def main() -> int:
    root = ROOT / "results" / "formal-01"
    raw_path = root / "candidate.json"
    output = root / "audit.json"
    if output.exists(): raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    candidate_bytes = (ROOT / "candidate.py").read_bytes()
    errors = audit(raw, fixture, candidate_bytes)
    mutations = []
    mutations.append(("decision_flip", lambda x: x["rows"][0].update(decision="YIELD_HEALTH_LOSS")))
    mutations.append(("input_sequence", lambda x: x["rows"][0]["input"].update(observation_sequence=70)))
    mutations.append(("drop_loss_row", lambda x: x["rows"].pop(1)))
    mutations.append(("duplicate_identity", lambda x: x["rows"][1].update(event_id=x["rows"][0]["event_id"])))
    mutations.append(("grant_authority", lambda x: x["rows"][1].update(authority_granted=True)))
    mutations.append(("hide_yield", lambda x: x["rows"][1].update(cover_terminated=False)))
    controls = []
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        controls.append({"name": name, "rejected": bool(audit(changed, fixture, candidate_bytes))})
    passed = not errors and all(item["rejected"] for item in controls)
    result = {
        "schema": "intermittent-observation-yield-audit-v1",
        "disposition": "PASS_SYNTHETIC_GUARD_CONTRACT_SCOPED" if passed else "FAIL_AUDIT",
        "errors": errors,
        "rows": len(raw.get("rows", [])),
        "yield_rows": sum(str(row.get("decision", "")).startswith("YIELD_") for row in raw.get("rows", [])),
        "mutation_controls": controls,
        "mutation_rejections": sum(item["rejected"] for item in controls),
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "errors": errors,
                      "mutation_rejections": result["mutation_rejections"], "rows": result["rows"]}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
