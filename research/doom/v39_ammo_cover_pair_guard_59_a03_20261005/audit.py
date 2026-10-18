#!/usr/bin/env python3
"""Independent per-case audit of paired observation identity and guard outcomes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def reference(case, source, fixture):
    h, a = case["health"], case["ammo"]
    if type(h) is not dict or type(a) is not dict:
        return True, False
    if h.get("status") != "observed" or a.get("status") != "observed":
        return True, False
    if h.get("signal_id") != "health" or a.get("signal_id") != "ammo":
        return True, False
    for item in (h, a):
        if (type(item.get("sequence")) is not int or type(item.get("capture_ns")) is not int or
                type(item.get("binding")) is not dict or not item["binding"]):
            return True, False
    if (h["sequence"] != a["sequence"] or h["capture_ns"] != a["capture_ns"] or
            h["binding"] != a["binding"]):
        return True, False
    if (h["sequence"] <= source["sequence"] or a["sequence"] <= source["sequence"] or
            h["capture_ns"] <= source["capture_ns"] or a["capture_ns"] <= source["capture_ns"]):
        return True, True
    max_age_ns = fixture["max_source_age_ms"] * 1_000_000
    if (h["capture_ns"] - source["capture_ns"] > max_age_ns or
            a["capture_ns"] - source["capture_ns"] > max_age_ns):
        return True, True
    if (type(h.get("value")) is not int or type(a.get("value")) is not int or
            h["value"] < 0 or a["value"] < 0):
        return True, True
    return (h["value"] < fixture["health_hard_minimum"] or
            a["value"] < fixture["ammo_hard_minimum"]), True


def signal_invalid(signal, source, signal_id, floor, max_age_ms):
    if (type(signal) is not dict or signal.get("status") != "observed" or
            signal.get("signal_id") != signal_id):
        return True
    if (type(signal.get("sequence")) is not int or signal["sequence"] <= source["sequence"] or
            type(signal.get("capture_ns")) is not int or
            signal["capture_ns"] <= source["capture_ns"] or
            signal.get("binding") != source["binding"]):
        return True
    if signal["capture_ns"] - source["capture_ns"] > max_age_ms * 1_000_000:
        return True
    if type(signal.get("value")) is not int or signal["value"] < 0:
        return True
    return signal["value"] < floor


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    rows = {row["name"]: row for row in result["rows"]}
    checks = []
    for case in fixture["cases"]:
        invalidated, coherent = reference(case, fixture["source"], fixture)
        row = rows[case["name"]]
        checks.extend([
            row["would_request_new_decision"] is invalidated,
            row["pair_coherent"] is coherent,
        ])
        if not coherent:
            checks.append(row["outcomes"] == {})
        else:
            checks.append(set(row["outcomes"]) == {"health", "ammo"})
            expected_by_signal = {
                "health": signal_invalid(case["health"], fixture["source"]["health"],
                                          "health", fixture["health_hard_minimum"],
                                          fixture["max_source_age_ms"]),
                "ammo": signal_invalid(case["ammo"], fixture["source"]["ammo"],
                                       "ammo", fixture["ammo_hard_minimum"],
                                       fixture["max_source_age_ms"]),
            }
            checks.extend(row["outcomes"][key]["requires_new_decision"] == expected
                          for key, expected in expected_by_signal.items())
            checks.append(invalidated == any(expected_by_signal.values()))
    checks.extend([len(rows) == len(fixture["cases"]),
                   result["live_allocation_invocations"] == 0])
    audit = {"format": "59-v39-paired-ammo-cover-audit-v1",
             "checks_passed": sum(checks), "checks_total": len(checks),
             "disposition": "PASS" if all(checks) else "AUDIT_FAILED"}
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True,
                                      separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
