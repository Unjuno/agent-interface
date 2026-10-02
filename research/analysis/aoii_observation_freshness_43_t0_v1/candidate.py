#!/usr/bin/env python3
"""Emit the frozen finite source/receiver trace and declared age metrics."""
import hashlib
import json

TRACE = [
    {"case": "old_unchanged", "tick": 0, "op": "truth", "generation": 1, "value": "OPEN"},
    {"case": "old_unchanged", "tick": 0, "op": "capture", "capture": "c0", "generation": 1, "value": "OPEN"},
    {"case": "old_unchanged", "tick": 5, "op": "deliver", "policy": "LATEST_BY_CAPTURE_TIME", "capture": "c0", "belief": "OPEN"},
    {"case": "old_unchanged", "tick": 5, "op": "deliver", "policy": "COVERAGE_THEN_LATEST", "capture": "c0", "belief": "OPEN"},
    {"case": "recent_superseded", "tick": 0, "op": "truth", "generation": 1, "value": "OPEN"},
    {"case": "recent_superseded", "tick": 4, "op": "truth", "generation": 1, "value": "CLOSED"},
    {"case": "recent_superseded", "tick": 4, "op": "capture", "capture": "c1", "generation": 1, "value": "OPEN"},
    {"case": "recent_superseded", "tick": 5, "op": "deliver", "policy": "LATEST_BY_CAPTURE_TIME", "capture": "c1", "belief": "OPEN"},
    {"case": "recent_superseded", "tick": 5, "op": "deliver", "policy": "COVERAGE_THEN_LATEST", "capture": "c1", "belief": "OPEN"},
    {"case": "short_critical", "tick": 0, "op": "truth", "generation": 1, "value": "SAFE"},
    {"case": "short_critical", "tick": 2, "op": "truth", "generation": 1, "value": "DANGER"},
    {"case": "short_critical", "tick": 3, "op": "truth", "generation": 1, "value": "SAFE"},
    {"case": "short_critical", "tick": 4, "op": "capture", "capture": "c2", "generation": 1, "value": "SAFE"},
    {"case": "short_critical", "tick": 4, "op": "deliver", "policy": "LATEST_BY_CAPTURE_TIME", "capture": "c2", "belief": "SAFE"},
    {"case": "short_critical", "tick": 4, "op": "deliver", "policy": "COVERAGE_THEN_LATEST", "capture": "c2", "belief": "SAFE"},
    {"case": "rapid_reversal", "tick": 0, "op": "truth", "generation": 1, "value": "A"},
    {"case": "rapid_reversal", "tick": 1, "op": "capture", "capture": "c3", "generation": 1, "value": "A"},
    {"case": "rapid_reversal", "tick": 2, "op": "truth", "generation": 1, "value": "B"},
    {"case": "rapid_reversal", "tick": 3, "op": "truth", "generation": 1, "value": "A"},
    {"case": "rapid_reversal", "tick": 4, "op": "belief", "value": "B"},
    {"case": "rapid_reversal", "tick": 4, "op": "deliver", "policy": "LATEST_BY_CAPTURE_TIME", "capture": "c3", "belief": "B"},
    {"case": "rapid_reversal", "tick": 4, "op": "deliver", "policy": "COVERAGE_THEN_LATEST", "capture": "c3", "belief": "A"},
    {"case": "missing_truth", "tick": 0, "op": "capture", "capture": "c4", "generation": 1, "value": "X"},
    {"case": "missing_truth", "tick": 1, "op": "deliver", "policy": "LATEST_BY_CAPTURE_TIME", "capture": "c4", "belief": "X"},
    {"case": "missing_truth", "tick": 1, "op": "deliver", "policy": "COVERAGE_THEN_LATEST", "capture": "c4", "belief": "X"},
    {"case": "generation_change", "tick": 0, "op": "truth", "generation": 1, "value": "FORM"},
    {"case": "generation_change", "tick": 0, "op": "capture", "capture": "c5", "generation": 1, "value": "FORM"},
    {"case": "generation_change", "tick": 2, "op": "truth", "generation": 2, "value": "SHEET"},
    {"case": "generation_change", "tick": 3, "op": "deliver", "policy": "LATEST_BY_CAPTURE_TIME", "capture": "c5", "belief": "FORM"},
    {"case": "generation_change", "tick": 3, "op": "deliver", "policy": "COVERAGE_THEN_LATEST", "capture": "c5", "belief": "FORM"},
]

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def main():
    print(json.dumps({"type": "freeze", "trace": TRACE, "trace_sha256": digest(TRACE), "delivery_budget_per_policy": 6, "authority": False}, sort_keys=True))
    for case in sorted({r["case"] for r in TRACE}):
        events = [r for r in TRACE if r["case"] == case]
        truths = [r for r in events if r["op"] == "truth"]
        captures = {r["capture"]: r for r in events if r["op"] == "capture"}
        for d in (r for r in events if r["op"] == "deliver"):
            c = captures[d["capture"]]
            current = next((t for t in reversed(truths) if t["tick"] <= d["tick"]), None)
            complete = current is not None
            generation_match = complete and c["generation"] == current["generation"]
            age = d["tick"] - c["tick"]
            error = None if not complete else (d["belief"] != current["value"])
            print(json.dumps({"type": "delivery", "case": case, "tick": d["tick"], "policy": d["policy"], "capture": d["capture"], "capture_tick": c["tick"], "capture_generation": c["generation"], "truth_generation": None if current is None else current["generation"], "age": age, "belief": d["belief"], "truth": None if current is None else current["value"], "known": complete, "generation_match": generation_match, "incorrect": error, "authority": False}, sort_keys=True))
    print(json.dumps({"type": "source", "trace_sha256": digest(TRACE), "deliveries_per_policy": 6}, sort_keys=True))

if __name__ == "__main__":
    main()
