#!/usr/bin/env python3
"""Independent raw-only coverage/accounting audit for Issue #7709 T0."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text())


def average(values):
    return sum(values) / len(values)


def sample_var(values):
    center = average(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def bounds(values, multiplier):
    center = average(values)
    radius = multiplier * math.sqrt(sample_var(values) / len(values))
    return [center - radius, center + radius]


def structure_ok(rows):
    seen = set()
    for row in rows:
        key = (row["scenario"], row["replicate"], row["session"], row["attempt"])
        if key in seen:
            return False
        seen.add(key)
        if row["block"] != row["attempt"] // F["block_width"]:
            return False
        if not 0 <= row["attempt"] < F["attempts"]:
            return False
        if not math.isclose(row["paired_delta_ns"], row["route_b_ns"] - row["route_a_ns"], abs_tol=1e-9):
            return False
        if row["censored"] and not (row["route_a_ns"] == F["deadline_penalty_ns"] == row["route_b_ns"]):
            return False
    expected = F["replicates"] * F["sessions"] * F["attempts"] * len(F["scenarios"])
    return len(rows) == expected and len(seen) == expected


def reconstruct(rows):
    grouped = defaultdict(list)
    per_run = defaultdict(list)
    for row in rows:
        grouped[row["scenario"], row["replicate"]].append(row["paired_delta_ns"])
        per_run[row["scenario"], row["replicate"], row["session"]].append(row["paired_delta_ns"])
    summaries = {name: [] for name in F["scenarios"]}
    for scenario in F["scenarios"]:
        for rep in range(F["replicates"]):
            pooled = grouped[scenario, rep]
            sessions = [average(per_run[scenario, rep, sid]) for sid in range(F["sessions"])]
            classic = bounds(pooled, 1.96)
            clustered = bounds(sessions, 2.364624251)
            summaries[scenario].append((classic[0] <= 0 <= classic[1],
                                        clustered[0] <= 0 <= clustered[1]))
    output = {}
    for scenario, values in summaries.items():
        pcov = average([x[0] for x in values])
        ccov = average([x[1] for x in values])
        output[scenario] = {"datasets": len(values), "pooled_coverage": pcov,
                            "session_cluster_coverage": ccov,
                            "pooled_false_promotion": 1 - pcov,
                            "session_cluster_false_promotion": 1 - ccov,
                            "coverage_gain": ccov - pcov}
    return output


def main():
    candidate = ROOT / "candidate.py"
    raw_path = ROOT / "raw_trials.jsonl"
    if hashlib.sha256(candidate.read_bytes()).hexdigest() != F["candidate_sha256"]:
        raise SystemExit("STOP_CANDIDATE_HASH")
    raw_bytes = raw_path.read_bytes()
    result = json.loads((ROOT / "RESULT.json").read_text())
    if hashlib.sha256(raw_bytes).hexdigest() != result["raw_sha256"]:
        raise SystemExit("STOP_RAW_HASH")
    rows = [json.loads(line) for line in raw_bytes.splitlines()]
    metrics = reconstruct(rows)
    gates = {
        "cluster_coverage_each_regime_ge_0_90": all(x["session_cluster_coverage"] >= 0.90 for x in metrics.values()),
        "cluster_false_promotion_each_regime_le_0_10": all(x["session_cluster_false_promotion"] <= 0.10 for x in metrics.values()),
        "nonstationary_coverage_gain_ge_0_10": all(metrics[x]["coverage_gain"] >= 0.10 for x in ("abrupt", "gradual")),
    }
    mutation_pass = mutation_controls(rows)
    checks = {
        "exact_all_attempt_denominator_and_pairing": structure_ok(rows) and result["raw_rows"] == len(rows),
        "raw_only_metrics_match_candidate": metrics == result["workloads"],
        "all_censored_attempts_retained_at_penalty": sum(r["censored"] for r in rows) > 0 and result["all_attempts_retained"] is True,
        "null_effect_gates_recomputed": gates == result["gates"] and result["disposition"] == ("METHOD_PASS_SCOPED" if all(gates.values()) else "FAIL_METHOD"),
        "missed_and_extra_boundary_mutations_rejected": mutation_pass,
    }
    audit = {"format": "issue7709-t0-independent-audit-v1", "checks": checks,
             "passed": sum(checks.values()), "total": len(checks),
             "disposition": "PASS" if all(checks.values()) else "AUDIT_FAILED"}
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(audit, sort_keys=True))


def mutation_controls(rows):
    dropped = rows[:-1]
    duplicated = rows + [dict(rows[0])]
    missing_boundary = [dict(r) for r in rows]
    extra_boundary = [dict(r) for r in rows]
    target = next(r for r in missing_boundary if r["scenario"] == "abrupt" and r["replicate"] == 0 and r["session"] == 0 and r["attempt"] == 20)
    target["block"] = 1  # merge adjacent fixed windows: missed boundary
    target = next(r for r in extra_boundary if r["scenario"] == "abrupt" and r["replicate"] == 0 and r["session"] == 0 and r["attempt"] == 21)
    target["block"] = 21  # introduce an unregistered split
    return (not structure_ok(dropped) and not structure_ok(duplicated)
            and not structure_ok(missing_boundary) and not structure_ok(extra_boundary))


if __name__ == "__main__":
    main()
