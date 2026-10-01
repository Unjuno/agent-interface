"""Independent raw-only audit for Issue #5694 finite event simulation."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def p95(values):
    if not values:
        return None
    x = sorted(values)
    return x[math.ceil(.95 * len(x)) - 1]


def audit(raw):
    assert raw["schema"] == "issue5694-opportunity-clock-raw-v1"
    assert raw["clock_domain"] == "simulated_monotonic_ms-v1"
    errors = []
    for name, scenario in raw["scenarios"].items():
        rows = scenario["opportunities"]
        ids = [r["opportunity_id"] for r in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"{name}:duplicate-id")
        for r in rows:
            if r["expiry_ms"] <= r["onset_ms"]:
                errors.append(f"{name}:invalid-window:{r['opportunity_id']}")
            aligned = r["clock_aligned"]
            outcome = r["outcome"]
            start, end = r["decision_start_ms"], r["effect_end_ms"]
            if not aligned and (outcome != "unknown_clock" or start is not None or end is not None):
                errors.append(f"{name}:invented-unsynchronized-timing")
            if outcome == "useful_effect" and (start is None or end is None or end > r["expiry_ms"] or end < start):
                errors.append(f"{name}:invalid-useful-endpoint:{r['opportunity_id']}")
            if outcome in {"miss_expired", "unknown_clock"} and outcome == "unknown_clock" and (start is not None or end is not None):
                errors.append(f"{name}:unknown-has-timing")
        useful = sum(r["outcome"] == "useful_effect" for r in rows)
        safe = sum(r["outcome"] == "safe_stop" for r in rows)
        missed = sum(r["outcome"] == "miss_expired" for r in rows)
        unknown = sum(r["outcome"] == "unknown_clock" for r in rows)
        latencies = [r["effect_end_ms"] - r["decision_start_ms"] for r in rows
                     if r["outcome"] in {"useful_effect", "safe_stop"}]
        s = scenario["summary"]
        expected = {"opportunity_count": len(rows), "useful_effect_count": useful,
                    "safe_stop_count": safe, "miss_expired_count": missed,
                    "unknown_clock_count": unknown, "completed_cycle_p95_ms": p95(latencies),
                    "useful_opportunity_coverage": useful / len(rows) if rows else None,
                    "handled_opportunity_fraction": (useful + safe) / len(rows) if rows else None}
        for k, v in expected.items():
            if s.get(k) != v:
                errors.append(f"{name}:summary-mismatch:{k}")
        if len(rows) != len([r for r in raw["schedule"] if r["opportunity_id"] in set(ids)]) and name not in {"overlap_control", "expiry_control"}:
            errors.append(f"{name}:denominator-loss")
    a = raw["scenarios"]["true_useful_fast"]["summary"]
    b = raw["scenarios"]["sparse_fast_with_busy_periods"]["summary"]
    if not (b["completed_cycle_p95_ms"] < a["completed_cycle_p95_ms"] and
            b["useful_opportunity_coverage"] < a["useful_opportunity_coverage"]):
        errors.append("constructed-ranking-inversion-not-detected")
    if raw["scenarios"]["no_stall_fast"]["summary"]["useful_opportunity_coverage"] != 1.0:
        errors.append("no-stall-control-failed")
    if raw["scenarios"]["safe_stop_control"]["summary"]["safe_stop_count"] != 1:
        errors.append("safe-stop-control-failed")
    if raw["scenarios"]["overlap_control"]["summary"]["opportunity_count"] != 2:
        errors.append("overlap-denominator-control-failed")
    if raw["scenarios"]["unsynchronized_clock_control"]["summary"]["unknown_clock_count"] != 2:
        errors.append("clock-unknown-control-failed")
    return {"result": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
            "errors": errors, "scenario_count": len(raw["scenarios"]),
            "schedule_opportunity_count": len(raw["schedule"]),
            "ranking_inversion": {"true_useful_fast_p95_ms": a["completed_cycle_p95_ms"],
                                  "sparse_busy_p95_ms": b["completed_cycle_p95_ms"],
                                  "true_useful_fast_coverage": a["useful_opportunity_coverage"],
                                  "sparse_busy_coverage": b["useful_opportunity_coverage"],
                                  "lower_p95_but_lower_coverage": b["completed_cycle_p95_ms"] < a["completed_cycle_p95_ms"] and b["useful_opportunity_coverage"] < a["useful_opportunity_coverage"]}}


def main():
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = audit(raw)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["result"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()

