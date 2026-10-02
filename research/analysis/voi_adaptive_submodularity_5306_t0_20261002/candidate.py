#!/usr/bin/env python3
"""Myopic net-VOI policy under an explicitly declared finite model."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def q(value: str) -> Fraction:
    return Fraction(value)


def posterior(case: dict, observations: dict[str, str]) -> dict[str, Fraction]:
    weights: dict[str, Fraction] = {}
    checks = {check["id"]: check for check in case["checks"]}
    for state, prior in case["states"].items():
        weight = q(prior)
        for check_id, outcome in observations.items():
            check = checks[check_id]
            if check.get("correlation") == "same_realized_outcome_as_A" and check_id == "A_COPY" and "A" in observations:
                probability = Fraction(int(observations.get("A") == outcome))
            else:
                probability = q(check["likelihood"][state][outcome])
            weight *= probability
        weights[state] = weight
    total = sum(weights.values(), Fraction())
    if not total:
        raise ValueError("IMPOSSIBLE_PARTIAL_OBSERVATION")
    return {state: weight / total for state, weight in weights.items()}


def predictive(case: dict, observations: dict[str, str], check: dict) -> dict[str, Fraction]:
    result = {outcome: Fraction() for outcome in check["likelihood"][next(iter(case["states"]))]}
    belief = posterior(case, observations)
    for outcome in result:
        for state, probability in belief.items():
            if check.get("correlation") == "same_realized_outcome_as_A" and check["id"] == "A_COPY" and "A" in observations:
                likelihood = Fraction(int(observations.get("A") == outcome))
            else:
                likelihood = q(check["likelihood"][state][outcome])
            result[outcome] += probability * likelihood
    return result


def accuracy(case: dict, observations: dict[str, str]) -> Fraction:
    return max(posterior(case, observations).values())


def marginal(case: dict, observations: dict[str, str], check: dict) -> Fraction:
    current = accuracy(case, observations)
    return sum((probability * accuracy(case, observations | {check["id"]: outcome})
                for outcome, probability in predictive(case, observations, check).items() if probability), Fraction()) - current


def greedy_tree(case: dict, observations: dict[str, str] | None = None,
                used: tuple[str, ...] = (), spent: Fraction = Fraction()) -> dict:
    observations = observations or {}
    budget = q(case["budget"])
    eligible = [c for c in case["checks"] if c["id"] not in used and spent + q(c["cost"]) <= budget]
    scored = [(marginal(case, observations, c) - q(c["cost"]), c["id"], c) for c in eligible]
    positive = [row for row in scored if row[0] > 0]
    if not positive:
        return {"action": "STOP", "observations": observations, "accuracy": str(accuracy(case, observations)), "expected_cost": "0"}
    _, _, chosen = max(positive, key=lambda row: (row[0], row[1]))
    branches = {}
    for outcome, p_outcome in predictive(case, observations, chosen).items():
        if p_outcome:
            branches[outcome] = {"probability": str(p_outcome), "next": greedy_tree(case, observations | {chosen["id"]: outcome}, used + (chosen["id"],), spent + q(chosen["cost"]))}
    return {"action": chosen["id"], "observations": observations, "marginal": str(marginal(case, observations, chosen)), "cost": chosen["cost"], "branches": branches}


def fixed_checklist(case: dict) -> dict:
    """Expected accuracy/cost of running every declared check in order."""
    def walk(observations: dict[str, str], index: int) -> tuple[Fraction, Fraction]:
        if index == len(case["checks"]):
            return accuracy(case, observations), Fraction()
        check = case["checks"][index]
        for previous in observations:
            if previous == check["id"]:
                raise ValueError("DUPLICATE_CHECK_ID")
        cost = q(check["cost"])
        if sum((q(case["checks"][i]["cost"]) for i in range(index + 1)), Fraction()) > q(case["budget"]):
            return accuracy(case, observations), Fraction()
        rows = [(p, walk(observations | {check["id"]: outcome}, index + 1))
                for outcome, p in predictive(case, observations, check).items() if p]
        return (sum((p * result[0] for p, result in rows), Fraction()),
                cost + sum((p * result[1] for p, result in rows), Fraction()))
    expected_accuracy, expected_cost = walk({}, 0)
    return {"expected_accuracy": str(expected_accuracy), "expected_cost": str(expected_cost), "net_value": str(expected_accuracy - expected_cost)}


def run(model: dict) -> dict:
    cases = {}
    for case in model["cases"]:
        checks = {c["id"]: c for c in case["checks"]}
        cases[case["id"]] = {
            "initial_marginals": {key: str(marginal(case, {}, check)) for key, check in checks.items()},
            "greedy_tree": greedy_tree(case),
            "fixed_checklist": fixed_checklist(case),
        }
    gates = []
    for control in model["gate_controls"]:
        feasible = control["fresh"] and control["current_generation"] == control["evidence_generation"]
        feasible = feasible and any(q(cost) <= q(control["budget"]) for cost in control["check_costs"].values())
        gates.append({"id": control["id"], "optional_calls": 0,
                      "disposition": "CONTINUE" if feasible else "YIELD"})
    return {"schema": "voi-adaptive-submodularity-candidate-v1", "cases": cases, "gate_controls": gates}


def main() -> None:
    model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
    output = run(model)
    out = ROOT / "results" / "candidate.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out.relative_to(ROOT)), "case_count": len(output["cases"]), "gate_count": len(output["gate_controls"])}))


if __name__ == "__main__":
    main()
