#!/usr/bin/env python3
"""Versioned raw-only audit repair; does not rerun or alter the candidate/raw."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text())
V2 = json.loads((ROOT / "FREEZE_AUDIT_V2.json").read_text())


def avg(xs):
    return sum(xs) / len(xs)


def variance(xs):
    center = avg(xs)
    return sum((x - center) ** 2 for x in xs) / (len(xs) - 1)


def ci(xs, critical):
    center = avg(xs)
    half = critical * math.sqrt(variance(xs) / len(xs))
    return center - half, center + half


def valid(rows):
    keys = set()
    for row in rows:
        identity = (row["scenario"], row["replicate"], row["session"], row["attempt"])
        if identity in keys or row["block"] != row["attempt"] // F["block_width"]:
            return False
        keys.add(identity)
        if not math.isclose(row["paired_delta_ns"], row["route_b_ns"] - row["route_a_ns"], abs_tol=1e-9):
            return False
        if row["censored"] and (row["route_a_ns"] != F["deadline_penalty_ns"] or
                                row["route_b_ns"] != F["deadline_penalty_ns"]):
            return False
    expected = F["replicates"] * F["sessions"] * F["attempts"] * len(F["scenarios"])
    return len(rows) == expected == len(keys)


def mutation_suite(rows):
    dropped = rows[:-1]
    duplicated = rows + [dict(rows[0])]
    merged = [dict(x) for x in rows]
    split = [dict(x) for x in rows]
    next(x for x in merged if x["scenario"] == "abrupt" and x["replicate"] == 0 and x["session"] == 0 and x["attempt"] == 20)["block"] = 1
    next(x for x in split if x["scenario"] == "abrupt" and x["replicate"] == 0 and x["session"] == 0 and x["attempt"] == 21)["block"] = 21
    return {"dropped_row_rejected": not valid(dropped),
            "duplicate_row_rejected": not valid(duplicated),
            "missed_boundary_rejected": not valid(merged),
            "extra_boundary_rejected": not valid(split)}


def main():
    candidate = ROOT / "candidate.py"
    raw_file = ROOT / "raw_trials.jsonl"
    result_file = ROOT / "RESULT.json"
    raw_bytes = raw_file.read_bytes()
    result_bytes = result_file.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    result_sha = hashlib.sha256(result_bytes).hexdigest()
    if hashlib.sha256(candidate.read_bytes()).hexdigest() != V2["candidate_sha256"]:
        raise SystemExit("STOP_CANDIDATE_HASH")
    if raw_sha != V2["candidate_raw_sha256"] or result_sha != V2["candidate_result_sha256"]:
        raise SystemExit("STOP_V2_FROZEN_INPUT_HASH")
    result = json.loads(result_bytes)
    rows = [json.loads(line) for line in raw_bytes.splitlines()]
    paired = defaultdict(list)
    by_session = defaultdict(list)
    for row in rows:
        paired[row["scenario"], row["replicate"]].append(row["paired_delta_ns"])
        by_session[row["scenario"], row["replicate"], row["session"]].append(row["paired_delta_ns"])
    aggregate = {name: [] for name in F["scenarios"]}
    for name in F["scenarios"]:
        for rep in range(F["replicates"]):
            values = paired[name, rep]
            runs = [avg(by_session[name, rep, sid]) for sid in range(F["sessions"])]
            pooled = ci(values, 1.96)
            clustered = ci(runs, 2.364624251)
            aggregate[name].append((pooled[0] <= 0 <= pooled[1], clustered[0] <= 0 <= clustered[1]))
    metrics = {}
    for name, values in aggregate.items():
        pc = avg([x[0] for x in values])
        cc = avg([x[1] for x in values])
        pfp = avg([not x[0] for x in values])
        cfp = avg([not x[1] for x in values])
        metrics[name] = {"datasets": len(values), "pooled_coverage": pc,
                         "session_cluster_coverage": cc, "pooled_false_promotion": pfp,
                         "session_cluster_false_promotion": cfp, "coverage_gain": cc - pc}
    gates = {
        "cluster_coverage_each_regime_ge_0_90": all(x["session_cluster_coverage"] >= .90 for x in metrics.values()),
        "cluster_false_promotion_each_regime_le_0_10": all(x["session_cluster_false_promotion"] <= .10 for x in metrics.values()),
        "nonstationary_coverage_gain_ge_0_10": all(metrics[x]["coverage_gain"] >= .10 for x in ("abrupt", "gradual")),
    }
    mutations = mutation_suite(rows)
    checks = {
        "exact_denominator_and_pairing": valid(rows) and result["raw_rows"] == len(rows),
        "result_raw_hash_matches": result["raw_sha256"] == raw_sha,
        "independent_metrics_reproduce_candidate": metrics == result["workloads"],
        "all_attempts_and_censored_penalties_retained": result["all_attempts_retained"] is True and any(x["censored"] for x in rows),
        "null_effect_gates_recomputed": gates == result["gates"],
        "dropped_and_duplicate_controls_rejected": mutations["dropped_row_rejected"] and mutations["duplicate_row_rejected"],
        "missed_and_extra_boundary_controls_rejected": mutations["missed_boundary_rejected"] and mutations["extra_boundary_rejected"],
        "audit_v1_failure_preserved": json.loads((ROOT / "AUDIT.json").read_text())["disposition"] == "AUDIT_FAILED",
    }
    audit = {"format": "issue7709-t0-independent-audit-v2", "checks": checks,
             "mutation_controls": mutations, "passed": sum(checks.values()), "total": len(checks),
             "disposition": "PASS" if all(checks.values()) else "AUDIT_FAILED"}
    (ROOT / "AUDIT_V2.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
