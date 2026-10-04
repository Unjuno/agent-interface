#!/usr/bin/env python3
"""Independent reference audit for the frozen dual-signal fixture."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def expected(signal, signal_id, floor, source_seq, source_time, source_binding):
    if signal.get("status") != "observed":
        return True, "UNKNOWN"
    if signal.get("signal_id") != signal_id:
        return True, "UNKNOWN"
    if (type(signal.get("sequence")) is not int or signal["sequence"] <= source_seq or
            type(signal.get("capture_ns")) is not int or signal["capture_ns"] <= source_time or
            signal.get("binding") != source_binding):
        return True, "UNKNOWN"
    if type(signal.get("value")) is not int or signal["value"] < 0:
        return True, "UNKNOWN"
    if signal["value"] < floor:
        return True, "HARD_INVALIDATED"
    return False, "UNCHANGED" if signal["value"] == 4 or signal_id == "health" else "SOFT_CHANGED"


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    source = fixture["source"]
    floors = {"health": fixture["health_hard_minimum"], "ammo": fixture["ammo_hard_minimum"]}
    by_name = {row["name"]: row for row in result["rows"]}
    checks = []
    expected_map = {}
    for sample in fixture["samples"]:
        expected_events = {key: expected(signal, key, floors[key], source[key]["sequence"],
                                        source[key]["capture_ns"], source[key]["binding"])
                           for key, signal in sample.items() if key in floors}
        should_invalidate = any(item[0] for item in expected_events.values())
        expected_map[sample["name"]] = should_invalidate
        actual = by_name[sample["name"]]
        checks.append(actual["would_request_new_decision"] == should_invalidate)
        checks.extend(actual["outcomes"][key]["status"] == status
                      for key, (_, status) in expected_events.items())
    checks.extend([
        len(result["rows"]) == len(fixture["samples"]),
        result["live_allocation_invocations"] == 0,
        result["all_expected_invalidations"] == (all(
            by_name[name]["would_request_new_decision"] == value
            for name, value in expected_map.items())),
    ])
    audit = {"format": "59-v39-dual-signal-audit-v1", "passed": sum(checks),
             "total": len(checks), "disposition": "PASS" if all(checks) else "AUDIT_FAILED",
             "checks": checks}
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True,
                                      separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": audit["disposition"], "passed": audit["passed"],
                      "total": audit["total"]}, sort_keys=True))


if __name__ == "__main__":
    main()
