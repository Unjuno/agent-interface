#!/usr/bin/env python3
"""Independent raw-only audit for the Issue #5694 finite opportunity ledger."""
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures.json"
ALLOCATION = "EXOGENOUS-OPPORTUNITY-5694-T0-20261001-01"


def reference_rows(case, deadline):
    expected = []
    next_free = 0
    case_deadline = case.get("deadline_ticks", deadline)
    for ordinal, tick in enumerate(case["opportunities"]):
        item = {"type": "opportunity", "allocation": ALLOCATION,
                "case_id": case["case_id"],
                "opportunity_id": "%s:%02d" % (case["case_id"], ordinal),
                "onset_tick": tick, "deadline_tick": case_deadline,
                "clock_synchronized": case["clock_synchronized"]}
        if not case["clock_synchronized"]:
            item.update(dispatch=None, completion_tick=None, latency_ticks=None,
                        outcome="UNKNOWN_CLOCK_ALIGNMENT")
        elif any(a <= tick < b for a, b in case["busy_intervals"]):
            item.update(dispatch=False, completion_tick=None, latency_ticks=None,
                        outcome=("SAFE_STOP" if case["safe_stop_on_busy"]
                                 else "MISSED_BUSY"))
        else:
            begin = tick if tick > next_free else next_free
            end = begin + case["service_ticks"]
            next_free = end
            elapsed = end - tick
            item.update(dispatch=True, completion_tick=end, latency_ticks=elapsed,
                        outcome=("USEFUL" if elapsed <= case_deadline else "LATE"))
        expected.append(item)
    return expected


def nearest_rank_p95(values):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def metrics(case_rows, fixture_case):
    n = len(case_rows)
    if not fixture_case["clock_synchronized"]:
        return {"opportunities": n, "useful": None, "coverage": None,
                "completed_cycles": 0, "completed_p95_ticks": None,
                "missed_busy": 0, "safe_stops": 0, "late": 0,
                "timing_disposition": "UNKNOWN_CLOCK_ALIGNMENT"}
    latency = [r["latency_ticks"] for r in case_rows if r["dispatch"] is True]
    useful = sum(r["outcome"] == "USEFUL" for r in case_rows)
    return {"opportunities": n, "useful": useful, "coverage": useful / n if n else None,
            "completed_cycles": len(latency),
            "completed_p95_ticks": nearest_rank_p95(latency),
            "missed_busy": sum(r["outcome"] == "MISSED_BUSY" for r in case_rows),
            "safe_stops": sum(r["outcome"] == "SAFE_STOP" for r in case_rows),
            "late": sum(r["outcome"] == "LATE" for r in case_rows),
            "timing_disposition": "SYNCHRONIZED"}


def matches_reference(expected, observed):
    return observed == expected


def audit(fixture, fixture_bytes, rows):
    errors = []
    expected_header = {"type": "header", "schema": "exogenous-opportunity-5694-raw-v1",
                       "allocation": ALLOCATION,
                       "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
                       "case_count": len(fixture["cases"])}
    if not rows or rows[0] != expected_header:
        errors.append("header_or_fixture_identity")
    expected = [expected_header]
    by_case = {}
    for case in fixture["cases"]:
        case_rows = reference_rows(case, fixture["deadline_ticks"])
        expected.extend(case_rows)
        by_case[case["case_id"]] = metrics(case_rows, case)
    observed = rows if rows and rows[0] == expected_header else rows[1:]
    if not matches_reference(expected, observed):
        errors.append("opportunity_inventory_or_reconstruction")
    controls = {}
    for name, mutate in (
        ("omitted_opportunity", lambda x: x[:-1]),
        ("fabricated_opportunity", lambda x: x + [dict(x[-1], opportunity_id="invented:99")]),
        ("false_latency", lambda x: x[:3] + [dict(x[3], latency_ticks=999)] + x[4:]),
        ("safe_stop_relabel", lambda x: x[:24] + [dict(x[24], outcome="USEFUL")] + x[25:]),
    ):
        damaged = mutate(expected)
        controls[name] = not matches_reference(expected, damaged)
    if not all(controls.values()):
        errors.append("corruption_control_not_rejected")
    base = by_case["no_stall"]
    stalled = by_case["busy_silent"]
    if not (base["completed_p95_ticks"] == stalled["completed_p95_ticks"]
            and stalled["coverage"] < base["coverage"]):
        errors.append("coordinated_omission_witness_absent")
    if by_case["busy_safe_stop"]["safe_stops"] != 4:
        errors.append("safe_stop_not_distinguished")
    if by_case["cue_expiry"]["late"] != 4 or by_case["overlap_serial"]["late"] != 3:
        errors.append("deadline_or_overlap_control")
    if by_case["clock_unknown"]["completed_p95_ticks"] is not None:
        errors.append("unsynchronized_timing_fabricated")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_OR_AUDIT",
            "errors": sorted(set(errors)), "rows": len(rows),
            "opportunities_reconstructed": sum(len(c["opportunities"]) for c in fixture["cases"]),
            "corruption_controls_rejected": sum(controls.values()),
            "corruption_controls": controls, "metrics": by_case}


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: audit.py RAW.jsonl [AUDIT.json]")
    output = Path(sys.argv[2]) if len(sys.argv) == 3 else HERE / "audit.json"
    if output.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    raw = Path(sys.argv[1]).read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    result = audit(fixture, fixture_bytes, rows)
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    serialized = json.dumps(result, sort_keys=True, indent=2) + "\n"
    output.write_text(serialized, encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": len(result["errors"]),
                      "corruption_controls_rejected": result["corruption_controls_rejected"],
                      "raw_sha256": result["raw_sha256"]}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
