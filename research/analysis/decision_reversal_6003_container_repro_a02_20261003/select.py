#!/usr/bin/env python3
"""One deterministic selector run over the frozen synthetic decision table."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import platform
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE_PATH = HERE / "FREEZE.json"
OUT = HERE / "candidate_result.json"


def entropy(rows):
    return -sum(row["p"] * math.log2(row["p"])
                for row in rows if row["p"] > 0)


def ranks(freeze):
    scenarios = freeze["baseline_actions"]
    budget = freeze["budget"]
    sentinel_cost = freeze["hard_sentinel"]["cost"]
    experiments = freeze["selector_fixture"]["experiments"]
    feasible = [e for e in experiments if e["cost"] + sentinel_cost <= budget]
    cheapest = min(feasible, key=lambda e: (e["cost"], e["id"]))["id"]
    nominal = "nominal"
    entropy_rank = max(
        feasible,
        key=lambda e: (entropy(e["outcomes"][nominal]), -e["cost"], e["id"]),
    )["id"]

    scores = {}
    for experiment in feasible:
        scenario_scores = []
        for scenario, baseline in scenarios.items():
            reversible_mass = sum(
                row["p"] for row in experiment["outcomes"][scenario]
                if row["next_action"] != "STOP" and row["next_action"] != baseline
            )
            scenario_scores.append(reversible_mass)
        scores[experiment["id"]] = min(scenario_scores)
    best = max(scores.values(), default=0.0)
    robust = "UNRANKABLE" if best <= 1e-12 else min(
        (name for name, score in scores.items() if abs(score - best) <= 1e-12),
        key=lambda name: (next(e["cost"] for e in feasible if e["id"] == name), name),
    )
    return {
        "feasible": [e["id"] for e in feasible],
        "cheapest": cheapest,
        "nominal_entropy": entropy_rank,
        "robust_reversal": robust,
        "robust_scores": scores,
        "nominal_entropy_bits": {
            e["id"]: entropy(e["outcomes"][nominal]) for e in feasible
        },
        "scenario_entropy_bits": {
            e["id"]: {s: entropy(e["outcomes"][s]) for s in scenarios}
            for e in feasible
        },
    }


def make_null_control(freeze):
    null = copy.deepcopy(freeze)
    for experiment in null["selector_fixture"]["experiments"]:
        for scenario, baseline in null["baseline_actions"].items():
            for row in experiment["outcomes"][scenario]:
                if row["next_action"] != "STOP":
                    row["next_action"] = baseline
    return null


def main():
    freeze_bytes = FREEZE_PATH.read_bytes()
    freeze = json.loads(freeze_bytes)
    result = {
        "allocation_id": freeze["allocation_id"],
        "main_sha": freeze["main_sha"],
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "selector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "status": "SYNTHETIC_CONSTRUCTION_ONLY",
        "scientific_support_events": 0,
        "primary": ranks(freeze),
        "null_control": ranks(make_null_control(freeze)),
        "scope": "OrbStack container CPU reproduction of the frozen synthetic table; no model, GPU, or empirical observations",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(OUT), "primary": result["primary"],
                      "null_control": result["null_control"]}, sort_keys=True))


if __name__ == "__main__":
    main()
