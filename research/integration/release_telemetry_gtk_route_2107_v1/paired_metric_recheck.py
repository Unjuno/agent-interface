"""Post-hoc pairwise metric recheck for the frozen Issue #2107 formal rows.

This does not rerun or alter the frozen formal auditor or allocation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import statistics

NONTERMINAL = {"WAIT", "QUERY", "RETRY"}


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    lo = int(index)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def bootstrap_median_ci(values: list[float], seed: int, samples: int = 10_000) -> list[float]:
    if not values:
        raise ValueError("empty_metric")
    rng = random.Random(seed)
    n = len(values)
    boot = [statistics.median(values[rng.randrange(n)] for _ in range(n))
            for _ in range(samples)]
    return [percentile(boot, 0.025), percentile(boot, 0.975)]


def recheck(evidence: Path) -> dict:
    summary = json.loads((evidence / "runner-summary.json").read_text(encoding="utf-8"))
    if summary.get("mode") != "formal" or summary.get("case_count") != 56:
        raise ValueError("not_the_frozen_56_case_formal_block")
    groups = {}
    for rel in summary["cases"]:
        row = json.loads((evidence / rel).read_text(encoding="utf-8"))
        groups[(row["rep"], row["scenario"], row["condition"])] = row

    pairs = []
    for rep in range(1, 9):
        for scenario in ("before", "after"):
            base = groups.get((rep, scenario, "NO_RELEASE_RECEIPT"))
            candidate = groups.get((rep, scenario, "VALID_RELEASE_RECEIPT"))
            if base is None or candidate is None:
                raise ValueError(f"missing_pair:{rep}:{scenario}")
            base_ns = base["decision_returned_ns"] - base["owner_actions"][0]["caller_returned_ns"]
            candidate_ns = candidate["decision_returned_ns"] - candidate["owner_actions"][0]["caller_returned_ns"]
            base_actions = sum(step["action"] in NONTERMINAL for step in base["decision_trace"])
            candidate_actions = sum(step["action"] in NONTERMINAL for step in candidate["decision_trace"])
            pairs.append({
                "rep": rep,
                "scenario": scenario,
                "no_receipt_latency_ns": base_ns,
                "valid_receipt_latency_ns": candidate_ns,
                "latency_reduction_ns": base_ns - candidate_ns,
                "latency_relative_reduction": (base_ns - candidate_ns) / base_ns,
                "no_receipt_nonterminal_actions": base_actions,
                "valid_receipt_nonterminal_actions": candidate_actions,
                "action_reduction": base_actions - candidate_actions,
                "action_relative_reduction": ((base_actions - candidate_actions) / base_actions
                                               if base_actions else 0.0),
            })

    latency_rel = [pair["latency_relative_reduction"] for pair in pairs]
    action_rel = [pair["action_relative_reduction"] for pair in pairs]
    latency_abs = [pair["latency_reduction_ns"] for pair in pairs]
    latency_gate = (statistics.median(latency_rel) >= 0.20
                    and bootstrap_median_ci(latency_rel, 2110)[0] > 0)
    action_gate = (statistics.median(action_rel) >= 0.20
                   and bootstrap_median_ci(action_rel, 2111)[0] > 0)
    if len(pairs) != 16:
        raise ValueError("primary_pair_count_not_16")
    return {
        "schema": "issue2107_pairwise_metric_recheck_v1",
        "formal_allocation": summary["allocation"],
        "pairs": pairs,
        "paired_count": len(pairs),
        "latency": {
            "median_pairwise_relative_reduction": statistics.median(latency_rel),
            "median_pairwise_relative_reduction_percent": statistics.median(latency_rel) * 100,
            "relative_reduction_bootstrap95": bootstrap_median_ci(latency_rel, 2110),
            "median_absolute_reduction_ns": statistics.median(latency_abs),
            "absolute_reduction_bootstrap95_ns": bootstrap_median_ci(latency_abs, 2107),
            "threshold_fraction": 0.20,
            "gate_pass": latency_gate,
        },
        "nonterminal_actions": {
            "median_pairwise_relative_reduction": statistics.median(action_rel),
            "relative_reduction_bootstrap95": bootstrap_median_ci(action_rel, 2111),
            "threshold_fraction": 0.20,
            "gate_pass": action_gate,
        },
        "disposition": "PASS_SCOPED_DECISION_VALUE" if latency_gate or action_gate else "HOLD_NO_DECISION_VALUE",
        "note": "Corrects paired aggregation and enforces the preregistered 20% threshold; frozen formal rows and original audit are unchanged.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = recheck(args.evidence)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "pairs"}, sort_keys=True))


if __name__ == "__main__":
    main()
