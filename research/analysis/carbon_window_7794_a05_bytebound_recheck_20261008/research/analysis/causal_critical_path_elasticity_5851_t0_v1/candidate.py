#!/usr/bin/env python3
"""Frozen T0 candidate: dynamic-programming critical-path elasticity on toy DAGs."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures.json"
OUT = HERE / "candidate_result.json"


def endpoint_ms(case, durations):
    nodes = {n["id"]: n for n in case["nodes"]}
    parents = {node: [] for node in nodes}
    for a, b in case["edges"]:
        if a not in nodes or b not in nodes:
            raise ValueError("edge references unknown node")
        parents[b].append(a)
    memo = {}
    visiting = set()

    def finish(node):
        if node in memo:
            return memo[node]
        if node in visiting:
            raise ValueError("cycle")
        visiting.add(node)
        start = max((finish(parent) for parent in parents[node]), default=0)
        value = start + durations[node]
        visiting.remove(node)
        memo[node] = value
        return value

    return finish(case["endpoint"])


def evaluate(case):
    if case["topology"] == "unknown" or not case["clock_complete"]:
        return {"case_id": case["case_id"], "status": "UNKNOWN", "numeric_elasticity": None}
    durations = {n["id"]: n["duration_ms"] for n in case["nodes"]}
    baseline = endpoint_ms(case, durations)
    regions = {}
    for node in case["nodes"]:
        row = regions.setdefault(node["region"], {"total_ms": 0, "largest_span_ms": 0})
        row["total_ms"] += node["duration_ms"]
        row["largest_span_ms"] = max(row["largest_span_ms"], node["duration_ms"])
    for region, row in regions.items():
        if case["topology"] == "branch_change":
            rule = case["branch_rule"]
            if region == rule["region"]:
                perturbed = durations.copy()
                perturbed["model"] += rule["amount_ms"]
                route_changes = perturbed["model"] > rule["threshold_ms"]
                row.update({"static_bound_ms": None, "paired_endpoint_delta_ms": None,
                            "intervention_status": "NONSTATIONARY_INTERVENTION" if route_changes else "FIXED_TOPOLOGY"})
                continue
        perturbed = durations.copy()
        members = [n for n in case["nodes"] if n["region"] == region]
        for node in members:
            perturbed[node["id"]] = node["duration_ms"] // 2
        changed = endpoint_ms(case, perturbed)
        row.update({"static_bound_ms": baseline - changed,
                    "paired_endpoint_delta_ms": baseline - changed,
                    "intervention_status": "FIXED_TOPOLOGY"})
    time_top = max(regions, key=lambda key: regions[key]["total_ms"])
    span_top = max(regions, key=lambda key: regions[key]["largest_span_ms"])
    elasticity_top = max(regions, key=lambda key: (regions[key].get("paired_endpoint_delta_ms") or 0))
    if case["topology"] == "branch_change":
        elasticity_top = "NONSTATIONARY_INTERVENTION"
    return {"case_id": case["case_id"], "status": "MEASURED", "baseline_endpoint_ms": baseline,
            "regions": regions, "sum_of_spans_top": time_top, "largest_span_top": span_top,
            "paired_elasticity_top": elasticity_top}


def main():
    if OUT.exists():
        raise SystemExit("candidate output already exists; refusing overwrite")
    fixture = json.loads(FIX.read_text(encoding="utf-8"))
    result = {"schema": "causal-critical-path-elasticity-5851-t0-candidate-v1",
              "allocation": "CAUSAL-CRITICAL-PATH-ELASTICITY-5851-T0-20261001-01",
              "fixture_sha256": __import__("hashlib").sha256(FIX.read_bytes()).hexdigest(),
              "rows": [evaluate(case) for case in fixture["cases"]]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(result["rows"]),
                      "output": OUT.name}, sort_keys=True))


if __name__ == "__main__":
    main()
