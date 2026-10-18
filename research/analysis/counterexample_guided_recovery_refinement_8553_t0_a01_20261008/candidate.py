#!/usr/bin/env python3
"""Finite belief-policy solver for the preregistered #8553 T0 fixture."""

import argparse
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def observations(case, state, features):
    actions = case["states"][state]["actions"]
    for action in actions.values():
        values = action.get("observations", {})
        if features and all(feature in values for feature in features):
            return tuple(values[feature] for feature in features)
    return ()


def solve(case, features, optimistic=False):
    states = case["states"]
    memo = {}

    def visit(belief, steps):
        belief = tuple(sorted(belief))
        key = (belief, steps)
        if key in memo:
            return memo[key]
        if all(states[state]["goal"] for state in belief):
            result = {"action": "GOAL", "branches": []}
            memo[key] = result
            return result
        if steps == 0:
            memo[key] = None
            return None
        enabled = []
        for state in belief:
            enabled.append({name for name, edge in states[state]["actions"].items()
                            if edge["enabled"] and (edge["safe"] or optimistic)})
        # In the intentionally unsound arm, the abstract transition for an
        # action is the union of its enabled concrete edges. This permits the
        # planted false witness; concrete validation must reject it.
        names = sorted(set.union(*enabled) if optimistic else set.intersection(*enabled)) if enabled else []
        for name in names:
            next_belief = []
            valid = True
            for state in belief:
                edge = states[state]["actions"].get(name)
                if edge is None or not edge["enabled"] or (not edge["safe"] and not optimistic):
                    if optimistic:
                        continue
                    valid = False
                    break
                next_belief.append(edge["next"])
            if optimistic:
                # An optimistic abstract successor retains only outcome
                # classes in which the chosen action reaches the goal.
                goal_successors = [s for s in next_belief if states[s]["goal"]]
                if goal_successors:
                    next_belief = goal_successors
            if not valid or not next_belief:
                continue
            groups = {}
            for nxt in next_belief:
                groups.setdefault(observations(case, nxt, features), set()).add(nxt)
            branches = []
            for signature, group in sorted(groups.items()):
                child = visit(group, steps - 1)
                if child is None:
                    break
                branches.append({"observation": list(signature), "policy": child})
            else:
                result = {"action": name, "branches": branches}
                memo[key] = result
                return result
        memo[key] = None
        return None

    policy = visit(case["start"], case["horizon"])
    return ("RECOVERABLE" if policy is not None else "NOT_RECOVERABLE"), policy


def safe_features(fixture):
    return sorted(p["id"] for p in fixture["predicate_catalog"] if p["safe_for_policy"])


def run(fixture):
    all_safe = safe_features(fixture)
    rows = []
    for case in fixture["cases"]:
        mode = case["coarse_abstraction"]
        coarse, coarse_policy = solve(case, [], optimistic=(mode == "optimistic-action-union"))
        fine, _ = solve(case, all_safe)
        truth, _ = solve(case, all_safe)
        cegar_features = []
        refinements = []
        cegar, policy = coarse, coarse_policy

        if coarse == "NOT_RECOVERABLE" and truth == "RECOVERABLE":
            candidates = []
            for feature in all_safe:
                changed = False
                for action in case["states"][case["start"][0]]["actions"].values():
                    vals = [case["states"][s]["actions"].get("inspect", {}).get("observations", {}).get(feature)
                            for s in case["start"]]
                    changed = changed or len(set(vals)) > 1
                if changed:
                    cost = next(p["cost"] for p in fixture["predicate_catalog"] if p["id"] == feature)
                    candidates.append((cost, feature))
            for _, feature in sorted(candidates):
                cegar_features.append(feature)
                refined, refined_policy = solve(case, cegar_features)
                refinements.append({"added": feature, "verdict": refined})
                if refined == "RECOVERABLE":
                    cegar, policy = refined, refined_policy
                    break
            if cegar != "RECOVERABLE":
                cegar, policy = "UNKNOWN", None
        elif coarse == "RECOVERABLE" and truth == "NOT_RECOVERABLE":
            refinements.append({"counterexample": "concrete-validation", "result": "spurious-recovery"})
            cegar, policy = "UNKNOWN", None

        rows.append({
            "case_id": case["id"],
            "coarse": {"verdict": coarse, "policy": coarse_policy},
            "fixed_fine": {"verdict": fine, "policy": solve(case, all_safe)[1]},
            "concrete_validation_verdict": truth,
            "cegar": {"verdict": cegar, "policy": policy,
                      "predicates_used": cegar_features, "refinements": refinements},
        })
    return {"schema": "recovery-abstraction-candidate-v1",
            "fixture_sha256": hashlib.sha256(canonical(fixture)).hexdigest(), "cases": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit("refusing to overwrite output")
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    result = run(fixture)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("candidate-output-written")


if __name__ == "__main__":
    main()
