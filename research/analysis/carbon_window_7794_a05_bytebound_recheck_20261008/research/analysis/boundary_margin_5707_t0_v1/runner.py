#!/usr/bin/env python3
"""Deterministic synthetic T0 for Issue #5707 / successor #5709."""
import json
import sys

BASE = ["opp-01", "opp-02", "opp-03", "opp-04"]
CASES = ["comfortable", "thin", "crossing", "safe_stop", "missing_time", "altered_opportunities"]

def row(case):
    if case in ("comfortable", "thin"):
        margins = [100, 90, 80, 70] if case == "comfortable" else [12, 11, 10, 9]
        return {"case": case, "opportunity_ids": BASE, "policy_a": {"margins_ms": margins, "forbidden_effects": 0}, "policy_b": {"margins_ms": margins, "forbidden_effects": 0}, "crossings": 0, "stops": 0, "unknown": 0, "disposition": "OBSERVED"}
    if case == "crossing":
        return {"case": case, "opportunity_ids": BASE, "policy_a": {"margins_ms": [40, 30, -3, 20], "forbidden_effects": 1}, "policy_b": {"margins_ms": [40, 30, -3, 20], "forbidden_effects": 1}, "crossings": 1, "stops": 0, "unknown": 0, "disposition": "BOUNDARY_CROSSED"}
    if case == "safe_stop":
        return {"case": case, "opportunity_ids": BASE, "policy_a": {"margins_ms": [30, 30, 30, 30], "forbidden_effects": 0}, "policy_b": {"margins_ms": [30, 30, 30, 30], "forbidden_effects": 0}, "crossings": 0, "stops": 1, "unknown": 0, "disposition": "STOP_RECORDED_OUTCOME_UNKNOWN"}
    if case == "missing_time":
        return {"case": case, "opportunity_ids": BASE, "policy_a": {"margins_ms": [40, None, 30, 20], "forbidden_effects": 0}, "policy_b": {"margins_ms": [40, None, 30, 20], "forbidden_effects": 0}, "crossings": 0, "stops": 0, "unknown": 1, "disposition": "UNKNOWN"}
    if case == "altered_opportunities":
        return {"case": case, "opportunity_ids": BASE, "policy_a": {"opportunity_ids": BASE, "margins_ms": [40, 30, 20, 10], "forbidden_effects": 0}, "policy_b": {"opportunity_ids": BASE[:-1], "margins_ms": [40, 30, 20], "forbidden_effects": 0}, "crossings": 0, "stops": 0, "unknown": 0, "disposition": "HOLD_NO_STABLE_DENOMINATOR"}
    raise ValueError(case)

def main():
    with open(sys.argv[1], "w", encoding="utf-8") as out:
        for case in CASES:
            out.write(json.dumps(row(case), sort_keys=True, separators=(",", ":")) + "\n")

if __name__ == "__main__":
    main()
