#!/usr/bin/env python3
"""Enumerate frozen metric-guided policy-selection controls."""
import argparse
import json
from pathlib import Path


def rows_from_fixture(fixture):
    for world_name, world in fixture["worlds"].items():
        for split in ("selection", "sealed"):
            for policy in fixture["policies"]:
                spec = world["policies"].get(policy)
                if spec is None:
                    continue
                for stratum in fixture["strata"]:
                    for replicate in fixture["replicates"]:
                        observed = stratum not in spec["missing_strata"]
                        yield {
                            "record_type": "attempt",
                            "world": world_name,
                            "split": split,
                            "attempt_id": f"{world_name}:{split}:{policy}:{stratum}:{replicate}",
                            "policy": policy,
                            "stratum": stratum,
                            "replicate": replicate,
                            "observation_available": observed,
                            "intermediate_ms": (spec["selection_ms"] if split == "selection" else spec["sealed_ms"]) + (replicate * 2 - 1) if observed else None,
                            "endpoint_utility": spec["utility"] if observed else None,
                            "hard_safety_failure": stratum in spec["safety_strata"],
                        }


def stats(rows):
    n = len(rows)
    observed = [r for r in rows if r["observation_available"]]
    return {
        "attempt_count": n,
        "observed_count": len(observed),
        "coverage": len(observed) / n if n else 0.0,
        "mean_intermediate_ms_observed": sum(r["intermediate_ms"] for r in observed) / len(observed) if observed else None,
        "mean_endpoint_utility_all_attempts": sum((r["endpoint_utility"] or 0) for r in rows) / n if n else 0.0,
        "hard_safety_failures": sum(bool(r["hard_safety_failure"]) for r in rows),
        "incomplete_attempts": n - len(observed),
    }


def summarize(fixture, rows):
    summaries = []
    for world_name, world in fixture["worlds"].items():
        world_rows = [r for r in rows if r["world"] == world_name]
        policies = sorted(world["policies"])
        selection_stats = {p: stats([r for r in world_rows if r["split"] == "selection" and r["policy"] == p]) for p in policies}
        eligible = [p for p in policies if selection_stats[p]["coverage"] == 1.0 and selection_stats[p]["hard_safety_failures"] == 0]
        selected_metric = min(policies, key=lambda p: (selection_stats[p]["mean_intermediate_ms_observed"], p))
        selected_endpoint = min(eligible, key=lambda p: (-selection_stats[p]["mean_endpoint_utility_all_attempts"], p)) if eligible else None
        sealed_metric = stats([r for r in world_rows if r["split"] == "sealed" and r["policy"] == selected_metric])
        sealed_endpoint = stats([r for r in world_rows if r["split"] == "sealed" and r["policy"] == selected_endpoint]) if selected_endpoint else None
        if sealed_metric["hard_safety_failures"]:
            disposition = "REJECT_NONCOMPENSABLE_SAFETY_REGRESSION"
        elif sealed_metric["coverage"] < 1.0 or (sealed_endpoint and sealed_metric["mean_endpoint_utility_all_attempts"] < sealed_endpoint["mean_endpoint_utility_all_attempts"]):
            disposition = "REJECT_SELECTION_COVERAGE_OR_ENDPOINT_REGRESSION"
        elif selected_metric == selected_endpoint:
            disposition = "SCOPED_SELECTION_CONCORDANCE"
        else:
            disposition = "HOLD_METRIC_SELECTION_EFFECT_NOT_REPLICATED"
        summaries.append({
            "record_type": "selection_summary",
            "world": world_name,
            "candidate_count": len(policies),
            "selection_attempts_per_policy": len(fixture["strata"]) * len(fixture["replicates"]),
            "sealed_attempts_per_policy": len(fixture["strata"]) * len(fixture["replicates"]),
            "selection_policy_ids": sorted({r["attempt_id"] for r in world_rows if r["split"] == "selection"}),
            "sealed_policy_ids": sorted({r["attempt_id"] for r in world_rows if r["split"] == "sealed"}),
            "selected_by_intermediate": selected_metric,
            "selected_by_endpoint": selected_endpoint,
            "metric_winner_selection_stats": selection_stats[selected_metric],
            "metric_winner_sealed_stats": sealed_metric,
            "endpoint_winner_sealed_stats": sealed_endpoint,
            "disposition": disposition,
        })
    return summaries


def run(fixture):
    attempts = list(rows_from_fixture(fixture))
    return attempts + summarize(fixture, attempts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as stream:
        for record in run(fixture):
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    print("candidate records", len(run(fixture)))


if __name__ == "__main__":
    main()
