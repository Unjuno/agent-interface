#!/usr/bin/env python3
"""Independent raw-only audit for the metric-guided selection experiment."""
import argparse
import hashlib
import json
from pathlib import Path


def expected_attempts(f):
    result = []
    for wn in sorted(f["worlds"]):
        world = f["worlds"][wn]
        for part in ["selection", "sealed"]:
            for pid in f["policies"]:
                if pid not in world["policies"]:
                    continue
                policy = world["policies"][pid]
                for st in f["strata"]:
                    for rep in f["replicates"]:
                        available = st not in policy["missing_strata"]
                        latency = policy["selection_ms"] if part == "selection" else policy["sealed_ms"]
                        result.append({
                            "record_type": "attempt", "world": wn, "split": part,
                            "attempt_id": ":".join([wn, part, pid, st, str(rep)]),
                            "policy": pid, "stratum": st, "replicate": rep,
                            "observation_available": available,
                            "intermediate_ms": latency + (1 if rep else -1) if available else None,
                            "endpoint_utility": policy["utility"] if available else None,
                            "hard_safety_failure": st in policy["safety_strata"],
                        })
    return result


def calculate(rows):
    total = len(rows)
    visible = [r for r in rows if r["observation_available"]]
    return {
        "attempt_count": total,
        "observed_count": len(visible),
        "coverage": len(visible) / total if total else 0.0,
        "mean_intermediate_ms_observed": sum(r["intermediate_ms"] for r in visible) / len(visible) if visible else None,
        "mean_endpoint_utility_all_attempts": sum((r["endpoint_utility"] or 0) for r in rows) / total if total else 0.0,
        "hard_safety_failures": sum(1 for r in rows if r["hard_safety_failure"] is True),
        "incomplete_attempts": total - len(visible),
    }


def independent_summaries(f, attempts):
    output = []
    for wn in sorted(f["worlds"]):
        worlds = [x for x in attempts if x["world"] == wn]
        policies = sorted(f["worlds"][wn]["policies"])
        by_policy = {pid: calculate([x for x in worlds if x["split"] == "selection" and x["policy"] == pid]) for pid in policies}
        metric = sorted(policies, key=lambda p: (by_policy[p]["mean_intermediate_ms_observed"], p))[0]
        admissible = [p for p in policies if by_policy[p]["coverage"] == 1 and by_policy[p]["hard_safety_failures"] == 0]
        endpoint = sorted(admissible, key=lambda p: (-by_policy[p]["mean_endpoint_utility_all_attempts"], p))[0] if admissible else None
        metric_final = calculate([x for x in worlds if x["split"] == "sealed" and x["policy"] == metric])
        endpoint_final = calculate([x for x in worlds if x["split"] == "sealed" and x["policy"] == endpoint]) if endpoint else None
        if metric_final["hard_safety_failures"] > 0:
            verdict = "REJECT_NONCOMPENSABLE_SAFETY_REGRESSION"
        elif metric_final["coverage"] != 1 or (endpoint_final and metric_final["mean_endpoint_utility_all_attempts"] < endpoint_final["mean_endpoint_utility_all_attempts"]):
            verdict = "REJECT_SELECTION_COVERAGE_OR_ENDPOINT_REGRESSION"
        elif metric == endpoint:
            verdict = "SCOPED_SELECTION_CONCORDANCE"
        else:
            verdict = "HOLD_METRIC_SELECTION_EFFECT_NOT_REPLICATED"
        output.append({
            "record_type": "selection_summary", "world": wn,
            "candidate_count": len(policies),
            "selection_attempts_per_policy": len(f["strata"]) * len(f["replicates"]),
            "sealed_attempts_per_policy": len(f["strata"]) * len(f["replicates"]),
            "selection_policy_ids": sorted(x["attempt_id"] for x in worlds if x["split"] == "selection"),
            "sealed_policy_ids": sorted(x["attempt_id"] for x in worlds if x["split"] == "sealed"),
            "selected_by_intermediate": metric,
            "selected_by_endpoint": endpoint,
            "metric_winner_selection_stats": by_policy[metric],
            "metric_winner_sealed_stats": metric_final,
            "endpoint_winner_sealed_stats": endpoint_final,
            "disposition": verdict,
        })
    return output


def audit(fixture, raw_path):
    errors = []
    try:
        observed = [json.loads(line) for line in Path(raw_path).read_text().splitlines() if line.strip()]
    except Exception as exc:
        return {"status": "FAIL_SELECTION_FEEDBACK_AUDIT", "errors": [f"raw_parse:{type(exc).__name__}"]}
    if any(not isinstance(x, dict) for x in observed):
        errors.append("record_not_object")
        observed = [x for x in observed if isinstance(x, dict)]
    if any(x.get("record_type") not in {"attempt", "selection_summary"} for x in observed):
        errors.append("unknown_record_type")
    want_attempts = expected_attempts(fixture)
    actual_attempts = [x for x in observed if x.get("record_type") == "attempt"]
    actual_summaries = [x for x in observed if x.get("record_type") == "selection_summary"]
    expected_ids = [x["attempt_id"] for x in want_attempts]
    actual_ids = [x.get("attempt_id") for x in actual_attempts]
    if sorted(actual_ids) != sorted(expected_ids) or len(actual_ids) != len(expected_ids):
        errors.append("attempt_inventory_mismatch")
    exp_by_id = {x["attempt_id"]: x for x in want_attempts}
    for row in actual_attempts:
        if row.get("attempt_id") in exp_by_id and json.dumps(row, sort_keys=True, separators=(",", ":")) != json.dumps(exp_by_id[row["attempt_id"]], sort_keys=True, separators=(",", ":")):
            errors.append("attempt_payload_mismatch:" + str(row.get("attempt_id")))
    expected_summary = independent_summaries(fixture, want_attempts)
    if sorted(actual_summaries, key=lambda x: x.get("world", "")) != sorted(expected_summary, key=lambda x: x.get("world", "")):
        errors.append("summary_recomputation_mismatch")
    expected_dispositions = {k: v["expected_disposition"] for k, v in fixture["worlds"].items()}
    actual_dispositions = {x.get("world"): x.get("disposition") for x in actual_summaries}
    if actual_dispositions != expected_dispositions:
        errors.append("frozen_disposition_mismatch")
    sha = hashlib.sha256(Path(raw_path).read_bytes()).hexdigest()
    return {
        "status": "PASS_SELECTION_FEEDBACK_GATE_SCOPED" if not errors else "FAIL_SELECTION_FEEDBACK_AUDIT",
        "errors": errors, "attempt_count": len(actual_attempts), "world_count": len(actual_summaries),
        "candidate_raw_sha256": sha,
        "results": {x["world"]: {"disposition": x["disposition"], "selected_by_intermediate": x["selected_by_intermediate"], "selected_by_endpoint": x["selected_by_endpoint"], "coverage": x["metric_winner_sealed_stats"]["coverage"], "endpoint_utility": x["metric_winner_sealed_stats"]["mean_endpoint_utility_all_attempts"], "safety_failures": x["metric_winner_sealed_stats"]["hard_safety_failures"]} for x in actual_summaries},
        "scope": "finite authored selection controls only; no empirical surrogate validated",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(json.loads(Path(args.fixtures).read_text()), args.input)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"], "errors", len(result["errors"]))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
