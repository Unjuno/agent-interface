#!/usr/bin/env python3
"""Authored finite coalition tables and attempt-level endpoint vectors."""
from __future__ import annotations

from fractions import Fraction
import itertools
import json
import sys
from pathlib import Path


CASES = {
    "additive_2f": {"factors": ["A", "B"], "values": {"-": 0, "A": 2, "B": 1, "AB": 3}, "feasible": ["-", "A", "B", "AB"]},
    "positive_interaction_2f": {"factors": ["A", "B"], "values": {"-": 0, "A": 1, "B": 2, "AB": 5}, "feasible": ["-", "A", "B", "AB"]},
    "negative_interaction_2f": {"factors": ["A", "B"], "values": {"-": 0, "A": 3, "B": 2, "AB": 4}, "feasible": ["-", "A", "B", "AB"]},
    "three_factor_reversal": {"factors": ["A", "B", "C"], "values": {"-": 0, "A": 4, "B": 3, "C": 0, "AB": 7, "AC": 4, "BC": 10, "ABC": 11}, "feasible": ["-", "A", "B", "C", "AB", "AC", "BC", "ABC"]},
    "infeasible_missing_B": {"factors": ["A", "B"], "values": {"-": 0, "A": 2, "AB": 4}, "feasible": ["-", "A", "AB"]},
}


def factorial(values: dict[str, int], factors: list[str]) -> dict:
    n = len(factors)
    alloc = {f: Fraction(0) for f in factors}
    for order in itertools.permutations(factors):
        coalition = ""
        prior = values["-"]
        for factor in order:
            coalition = "".join(sorted(coalition + factor))
            key = coalition or "-"
            marginal = values[key] - prior
            alloc[factor] += Fraction(marginal, 1) / math_factorial(n)
            prior = values[key]
    return {k: fraction(v) for k, v in alloc.items()}


def math_factorial(n: int) -> int:
    return 1 if n < 2 else n * math_factorial(n - 1)


def fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def attempts_for(case_id: str, coalition: str, success_count: int) -> list[dict]:
    rows = []
    for index in range(20):
        success = index < success_count
        rows.append({
            "attempt": index + 1,
            "reported_effect": success,
            "oracle_effect": success,
            "safety_events": 0,
            "latency_ms": 100 + 10 * len(coalition) + index * 3,
            "tokens": 20 + 2 * len(coalition) + index,
        })
    return rows


def main(output: str) -> None:
    records = []
    for case_id, spec in CASES.items():
        arms = []
        for coalition in spec["feasible"]:
            success_count = spec["values"][coalition]
            arms.append({
                "coalition": coalition,
                "feasible": True,
                "attempts": attempts_for(case_id, coalition, success_count),
            })
        possible = ["".join(c) or "-" for size in range(len(spec["factors"]) + 1) for c in itertools.combinations(spec["factors"], size)]
        missing = sorted(set(possible) - set(spec["feasible"]))
        complete = not missing
        metrics = {
            "success_rate": {arm["coalition"]: fraction(Fraction(sum(a["reported_effect"] for a in arm["attempts"]), len(arm["attempts"]))) for arm in arms},
            "safety_events": {arm["coalition"]: sum(a["safety_events"] for a in arm["attempts"]) for arm in arms},
            "mean_latency_ms": {arm["coalition"]: fraction(Fraction(sum(a["latency_ms"] for a in arm["attempts"]), len(arm["attempts"]))) for arm in arms},
            "mean_tokens": {arm["coalition"]: fraction(Fraction(sum(a["tokens"] for a in arm["attempts"]), len(arm["attempts"]))) for arm in arms},
        }
        interaction = None
        sh = None
        base_marginals = None
        if complete:
            v = {k: Fraction(value, 20) for k, value in spec["values"].items()}
            if len(spec["factors"]) == 2:
                a, b = spec["factors"]
                interaction = fraction(v["AB"] - v[a] - v[b] + v["-"])
                base_marginals = {a: fraction(v[a] - v["-"]), b: fraction(v[b] - v["-"])}
            sh = factorial({k: Fraction(value, 20) for k, value in spec["values"].items()}, spec["factors"])
        record = {
            "case_id": case_id,
            "factors": spec["factors"],
            "arms": arms,
            "infeasible_coalitions": missing,
            "disposition": "ANALYZE" if complete else "HOLD_NO_FEASIBLE_FACTORIAL",
            "metrics": metrics,
            "primary_characteristic": "success_rate",
            "interaction_2f": interaction,
            "baseline_marginals": base_marginals,
            "shapley": sh,
            "safety_scalarized": False,
        }
        records.append(record)
    with Path(output).open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"cases": len(records), "coalitions": sum(len(r["arms"]) for r in records), "attempts": sum(len(a["attempts"]) for r in records for a in r["arms"]), "output": output}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python simulate.py OUTPUT.jsonl")
    main(sys.argv[1])
