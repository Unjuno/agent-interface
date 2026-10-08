"""Belief-set bounded reachability candidate for finite deterministic fixtures."""

import argparse
import json
from pathlib import Path



def _canonical(values):
    return tuple(sorted(set(values)))


def _solve_at(problem, belief, horizon):
    marker = set(problem["marker"])
    unsafe = set(problem["unsafe"])
    if set(belief) <= marker:
        return {"ok": True, "policy": {"terminal": "VERIFIED_MARKER"}}
    if horizon <= 0 or set(belief) & unsafe:
        return {"ok": False}

    actions = sorted(problem["authorized_actions"])
    for action in actions:
        successors = set()
        valid = True
        for state in belief:
            edges = problem["transitions"].get(state, {}).get(action)
            if not edges:
                valid = False
                break
            successors.update(edges)
        if not valid or successors & unsafe:
            continue

        groups = {}
        for state in successors:
            observation = problem["observations"].get(state)
            if observation is None:
                valid = False
                break
            groups.setdefault(observation, set()).add(state)
        if not valid:
            continue

        branches = {}
        for observation in sorted(groups):
            next_belief = _canonical(groups[observation])
            result = _solve_at(problem, next_belief, horizon - 1)
            if not result["ok"]:
                valid = False
                break
            branches[observation] = result["policy"]
        if valid:
            return {
                "ok": True,
                "policy": {"action": action, "branches": branches},
            }
    return {"ok": False}


def classify(problem, budget):
    if (
        not problem.get("model_complete")
        or not problem.get("transition_map_complete", True)
        or not problem.get("generation_current")
        or not problem.get("marker_verified")
    ):
        return {
            "status": "UNKNOWN",
            "minimum_steps": None,
            "margin": None,
            "policy": None,
            "reason": "INCOMPLETE_OR_STALE_OR_UNVERIFIED",
        }

    initial = _canonical(problem["initial_belief"])
    for state in initial:
        if state not in problem["observations"]:
            return {
                "status": "UNKNOWN",
                "minimum_steps": None,
                "margin": None,
                "policy": None,
                "reason": "OBSERVATION_MISSING",
            }

    for horizon in range(budget + 1):
        result = _solve_at(problem, initial, horizon)
        if result["ok"]:
            return {
                "status": "RECOVERABLE",
                "minimum_steps": horizon,
                "margin": budget - horizon,
                "policy": result["policy"],
                "reason": None,
            }
    return {
        "status": "NOT_RECOVERABLE",
        "minimum_steps": None,
        "margin": None,
        "policy": None,
        "reason": "NO_COMMON_SAFE_POLICY_WITHIN_BUDGET",
    }


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        for horizon in fixture["horizons"]:
            budget = min(horizon, case.get("budget_cap", horizon))
            result = classify(case, budget)
            rows.append({
                "case_id": case["id"],
                "horizon": horizon,
                "effective_budget": budget,
                **result,
            })
    controls = []
    aliased = next(x for x in fixture["cases"] if x["id"] == "aliased-opposite-actions")
    for singleton in aliased["singleton_controls"]:
        controls.append({
            "belief": sorted(singleton),
            "result": classify({**aliased, "initial_belief": singleton}, 2),
        })
    return {"rows": rows, "singleton_controls": controls}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/input/input.json")
    parser.add_argument("--output", default="/output/candidate.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = run(fixture)
    output = Path(args.output)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"rows": len(result["rows"]), "status": "CANDIDATE_COMPLETE"},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
