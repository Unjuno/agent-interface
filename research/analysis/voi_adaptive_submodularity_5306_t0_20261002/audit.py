#!/usr/bin/env python3
"""Independent exact-rational audit; deliberately does not import candidate.py."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def F(x: str) -> Fraction:
    return Fraction(x)


def belief(m: dict, case: dict, obs: dict[str, str]) -> dict[str, Fraction]:
    checks = {c["id"]: c for c in case["checks"]}
    masses = {}
    for state, prior in case["states"].items():
        mass = F(prior)
        for cid, value in obs.items():
            spec = checks[cid]
            if cid == "A_COPY" and spec.get("correlation") == "same_realized_outcome_as_A" and "A" in obs:
                like = Fraction(value == obs.get("A"))
            else:
                like = F(spec["likelihood"][state][value])
            mass *= like
        masses[state] = mass
    total = sum(masses.values(), Fraction())
    if total == 0:
        raise AssertionError("impossible audit history")
    return {s: v / total for s, v in masses.items()}


def distribution(m: dict, case: dict, obs: dict[str, str], check: dict) -> dict[str, Fraction]:
    names = tuple(check["likelihood"][next(iter(case["states"]))])
    posterior = belief(m, case, obs)
    out = {name: Fraction() for name in names}
    for name in names:
        for state, p in posterior.items():
            if check["id"] == "A_COPY" and check.get("correlation") == "same_realized_outcome_as_A" and "A" in obs:
                likelihood = Fraction(name == obs.get("A"))
            else:
                likelihood = F(check["likelihood"][state][name])
            out[name] += p * likelihood
    return out


def score(m: dict, case: dict, obs: dict[str, str]) -> Fraction:
    return max(belief(m, case, obs).values())


def gain(m: dict, case: dict, obs: dict[str, str], check: dict) -> Fraction:
    now = score(m, case, obs)
    return sum((p * score(m, case, obs | {check["id"]: y})
                for y, p in distribution(m, case, obs, check).items() if p), Fraction()) - now


def combine(m: dict, case: dict, obs: dict[str, str], used: tuple[str, ...], spent: Fraction) -> dict:
    """Enumerate STOP and every admissible next-check continuation exactly."""
    best = {"net": score(m, case, obs), "accuracy": score(m, case, obs), "cost": Fraction(), "action": "STOP", "branches": {}}
    for check in case["checks"]:
        cid, cost = check["id"], F(check["cost"])
        if cid in used or spent + cost > F(case["budget"]):
            continue
        parts = []
        for y, p in distribution(m, case, obs, check).items():
            if p:
                nxt = combine(m, case, obs | {cid: y}, used + (cid,), spent + cost)
                parts.append((p, y, nxt))
        accuracy = sum((p * nxt["accuracy"] for p, _, nxt in parts), Fraction())
        future_cost = cost + sum((p * nxt["cost"] for p, _, nxt in parts), Fraction())
        net = accuracy - future_cost
        if net > best["net"]:
            best = {"net": net, "accuracy": accuracy, "cost": future_cost, "action": cid,
                    "branches": {y: {"probability": str(p), "next": nxt} for p, y, nxt in parts}}
    return best


def fixed(m: dict, case: dict) -> tuple[Fraction, Fraction]:
    def fold(obs: dict[str, str], index: int) -> tuple[Fraction, Fraction]:
        if index == len(case["checks"]):
            return score(m, case, obs), Fraction()
        check = case["checks"][index]
        cost = F(check["cost"])
        if sum((F(case["checks"][j]["cost"]) for j in range(index + 1)), Fraction()) > F(case["budget"]):
            return score(m, case, obs), Fraction()
        children = [(p, fold(obs | {check["id"]: y}, index + 1))
                    for y, p in distribution(m, case, obs, check).items() if p]
        return (sum((p * child[0] for p, child in children), Fraction()),
                cost + sum((p * child[1] for p, child in children), Fraction()))
    return fold({}, 0)


def verify_candidate(m: dict, submitted: dict) -> dict:
    by_id = {c["id"]: c for c in m["cases"]}
    out = submitted["cases"]
    if set(out) != set(by_id):
        raise AssertionError("case identity mismatch")
    root = by_id["complementary_no_singleton_voi"]
    checks = {c["id"]: c for c in root["checks"]}
    delta_root = gain(m, root, {}, checks["B"])
    delta_after_negative = gain(m, root, {"A": "-"}, checks["B"])
    greedy = out[root["id"]]["greedy_tree"]
    if greedy["action"] != "STOP":
        raise AssertionError("myopic candidate did not stop at zero-gain root")
    fixed_row = out[root["id"]]["fixed_checklist"]
    fixed_accuracy, fixed_cost = fixed(m, root)
    if F(fixed_row["expected_accuracy"]) != fixed_accuracy or F(fixed_row["expected_cost"]) != fixed_cost:
        raise AssertionError("fixed policy outcome discrepancy")
    exact = combine(m, root, {}, (), Fraction())
    if exact["action"] != "A" or exact["branches"].get("-") is None:
        raise AssertionError("exact policy did not expose complementary continuation")
    if exact["branches"]["-"]["next"]["action"] != "B":
        raise AssertionError("exact policy failed to acquire B after A negative")
    if exact["net"] <= score(m, root, {}) or exact["net"] <= F(greedy["accuracy"]):
        raise AssertionError("exact policy has no strict net benefit over stopping")
    dup = by_id["perfect_duplicate_negative_control"]
    dup_checks = {c["id"]: c for c in dup["checks"]}
    dup_root = gain(m, dup, {}, dup_checks["A_COPY"])
    dup_after = gain(m, dup, {"A": "GOOD"}, dup_checks["A_COPY"])
    if not (delta_after_negative > delta_root and dup_after <= dup_root and dup_after == 0):
        raise AssertionError("conditional marginal controls did not match")
    expected_gates = {"stale_source": "YIELD", "deadline_infeasible": "YIELD"}
    if {x["id"]: x["disposition"] for x in submitted["gate_controls"]} != expected_gates:
        raise AssertionError("hard-gate disposition mismatch")
    if any(x["optional_calls"] != 0 for x in submitted["gate_controls"]):
        raise AssertionError("hard gate allowed optional calls")
    return {
        "decision": "COUNTEREXAMPLE_GREEDY_VOI_SCOPED",
        "conditional_marginals": {"B_before_evidence": str(delta_root), "B_after_A_negative": str(delta_after_negative), "duplicate_before": str(dup_root), "duplicate_after_A_GOOD": str(dup_after)},
        "myopic": {"action": greedy["action"], "accuracy": str(score(m, root, {})), "expected_cost": "0", "net": str(score(m, root, {}))},
        "exact_policy": {"first_action": exact["action"], "expected_accuracy": str(exact["accuracy"]), "expected_cost": str(exact["cost"]), "net": str(exact["net"])},
        "strict_net_gain_over_myopic": str(exact["net"] - score(m, root, {})),
        "gate_controls": expected_gates,
        "independent_errors": [],
    }


def main() -> None:
    m = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
    c = json.loads((ROOT / "results" / "candidate.json").read_text(encoding="utf-8"))
    result = verify_candidate(m, c)
    path = ROOT / "results" / "audit.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": len(result["independent_errors"])}))


if __name__ == "__main__":
    main()
