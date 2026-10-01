#!/usr/bin/env python3
"""Finite synthetic surrogate-gate candidate for Issue #5686 T0."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def summarize(rows):
    grouped = defaultdict(lambda: {0: [], 1: []})
    for row in rows:
        grouped[row["stratum"]][row["treatment"]].append(row)
    effects = []
    for stratum in sorted(grouped):
        arms = grouped[stratum]
        if not arms[0] or not arms[1]:
            raise ValueError(f"unpaired stratum: {stratum}")
        incomplete = any(r["endpoint"] != "verified" for arm in arms.values() for r in arm)
        # Lower latency is better; higher utility is better. Keep safety separate.
        delta_speed = (sum(r["latency_ms"] for r in arms[0]) / len(arms[0])
                       - sum(r["latency_ms"] for r in arms[1]) / len(arms[1]))
        delta_utility = (sum(r["utility"] for r in arms[1]) / len(arms[1])
                         - sum(r["utility"] for r in arms[0]) / len(arms[0]))
        delta_harm = (sum(r["safety_failure"] for r in arms[1]) / len(arms[1])
                      - sum(r["safety_failure"] for r in arms[0]) / len(arms[0]))
        effects.append({"stratum": stratum, "delta_speed_benefit_ms": delta_speed,
                        "delta_utility": delta_utility, "delta_harm": delta_harm,
                        "attempts": sum(map(len, arms.values())), "incomplete": incomplete})
    if any(e["incomplete"] for e in effects):
        disposition = "UNCERTAIN_INCOMPLETE_ENDPOINTS"
    elif any(e["delta_harm"] > 0 for e in effects):
        disposition = "REJECT_NONCOMPENSABLE_SAFETY_REGRESSION"
    elif any(e["delta_speed_benefit_ms"] > 0 and e["delta_utility"] < 0 for e in effects):
        disposition = "REJECT_EFFECT_DIRECTION_INVERSION"
    elif any(e["delta_speed_benefit_ms"] > 0 and e["delta_utility"] == 0 for e in effects):
        disposition = "REJECT_INTERMEDIATE_ONLY_EFFECT"
    elif all(e["delta_speed_benefit_ms"] > 0 and e["delta_utility"] > 0 for e in effects):
        disposition = "DIRECTION_CONCORDANT_IN_OBSERVED_STRATA_PREDICTIVE_VALIDITY_UNESTABLISHED"
    else:
        disposition = "NOT_PROMOTABLE"
    return {"world": rows[0]["world"], "attempt_count": len(rows),
            "naive_intermediate_only_rule_promotes": any(e["delta_speed_benefit_ms"] > 0 for e in effects),
            "strata": effects, "disposition": disposition}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixtures = json.loads(Path(args.input).read_text())
    required = {"world", "stratum", "attempt", "treatment", "latency_ms", "utility", "safety_failure", "endpoint"}
    if not fixtures or any(set(r) != required for r in fixtures):
        raise ValueError("fixture schema mismatch or empty input")
    worlds = defaultdict(list)
    for r in fixtures:
        if r["treatment"] not in (0, 1) or r["endpoint"] not in ("verified", "safe_stop", "unfinished", "missing"):
            raise ValueError("invalid treatment or endpoint status")
        worlds[r["world"]].append(r)
    with Path(args.output).open("w") as out:
        for world in sorted(worlds):
            for row in worlds[world]:
                out.write(json.dumps({"record_type": "attempt", "record": row}, sort_keys=True) + "\n")
            out.write(json.dumps({"record_type": "summary", "summary": summarize(worlds[world])}, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
