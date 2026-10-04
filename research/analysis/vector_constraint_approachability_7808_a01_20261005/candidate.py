"""Finite synthetic approachability comparison for Issue #7808 (no runtime authority)."""
import argparse
import hashlib
import json
from pathlib import Path

POLICIES = ("blackwell", "scalar", "independent_freeze")
TOL = 1e-9


def _debt(observed, target):
    n = len(observed)
    if not n:
        return [0.0 for _ in target]
    return [max(0.0, sum(row["vector"][d] for row in observed) - n * target[d])
            for d in range(len(target))]


def _select(policy, routes, profiles, debt, target):
    def utility(route):
        return int(bool(profiles[route]["useful_forecast"]))
    def total(route):
        return sum(profiles[route]["forecast"])
    if policy == "blackwell":
        score = lambda r: sum(debt[d] * profiles[r]["forecast"][d]
                              for d in range(len(target)))
        return min(routes, key=lambda r: (score(r), -utility(r), r))
    if policy == "scalar":
        return min(routes, key=lambda r: (total(r), -utility(r), r))
    pressured = [d for d, value in enumerate(debt) if value > TOL]
    safe = [r for r in routes
            if all(profiles[r]["forecast"][d] <= target[d] + TOL for d in pressured)]
    pool = safe or routes
    return min(pool, key=lambda r: (total(r), -utility(r), r))


def _actual(case, context, route, row, contexts):
    profile = contexts[context][route]
    override = case.get("overrides", {}).get(str(row), {}).get(route, {})
    vector = override.get("actual", profile["actual"])
    useful = override.get("verified_useful", profile["verified_useful"])
    return {"vector": list(vector), "useful_verified": bool(useful)}


def run_case(fixture, case):
    contexts = fixture["contexts"]
    target = case["target"]
    pending = []
    feedback = []
    steps = []
    missing = set(case["missing_rows"])
    delays = case.get("delay_by_row", {})
    for index, context in enumerate(case["contexts"]):
        ready = [e for e in pending if e["due_tick"] <= index]
        pending = [e for e in pending if e["due_tick"] > index]
        for event in ready:
            feedback.append({"row": event["row"], "route": event["route"],
                             "vector": event["vector"], "useful_verified": event["useful_verified"],
                             "received_tick": index})
        observed = [{"vector": e["vector"]} for e in feedback]
        debt = _debt(observed, target)
        gates = case["gates"][context]
        routes = [r for r in fixture["route_order"] if gates.get(r) is True]
        profiles = contexts[context]
        route = _select("blackwell", routes, profiles, debt, target)
        steps.append({"row": index, "context": context, "route": route,
                      "feedback_before": [e["row"] for e in feedback],
                      "forecast": list(profiles[route]["forecast"]),
                      "hard_gate_pass": bool(gates[route])})
        actual = _actual(case, context, route, index, contexts)
        if index not in missing:
            pending.append({"row": index, "route": route, "vector": actual["vector"],
                            "useful_verified": actual["useful_verified"],
                            "due_tick": index + int(delays.get(str(index), 0)) + 1})
    for tick in range(len(case["contexts"]), len(case["contexts"]) + len(case["contexts"]) + 1):
        ready = [e for e in pending if e["due_tick"] <= tick]
        pending = [e for e in pending if e["due_tick"] > tick]
        for event in ready:
            feedback.append({"row": event["row"], "route": event["route"],
                             "vector": event["vector"], "useful_verified": event["useful_verified"],
                             "received_tick": tick})
    feedback.sort(key=lambda e: e["row"])
    returned = {e["row"] for e in feedback}
    unknown = [i for i in range(len(steps)) if i not in returned]
    complete = not unknown
    if complete:
        means = [sum(e["vector"][d] for e in feedback) / len(steps)
                 for d in range(len(target))]
        claim = "WITHIN_TARGET" if all(means[d] <= target[d] + TOL
                                       for d in range(len(target))) else "OUTSIDE_TARGET"
    else:
        means = None
        claim = "UNKNOWN_INCOMPLETE_FEEDBACK"
    maximum = [max((e["vector"][d] for e in feedback), default=None)
               for d in range(len(target))]
    return {"steps": steps, "feedback": feedback, "unknown_feedback_rows": unknown,
            "complete_feedback": complete, "observed_mean": means,
            "max_observed_single_episode": maximum,
            "verified_useful_count": sum(bool(e["useful_verified"]) for e in feedback),
            "target_claim": claim}


def run(fixture):
    return {"schema": "vca7808-candidate-v1",
            "fixture_sha256": hashlib.sha256(json.dumps(fixture, sort_keys=True,
                                       separators=(",", ":")).encode()).hexdigest(),
            "case_order": fixture["case_order"],
            "policies": {case["id"]: {p: run_policy(fixture, case, p) for p in POLICIES}
                         for case in fixture["cases"]}}


def run_policy(fixture, case, policy):
    if policy == "blackwell":
        return run_case(fixture, case)
    # Each comparator uses exactly the same event schedule and frozen inputs.
    return simulate_other(fixture, case, policy)


def simulate_other(fixture, case, policy):
    contexts, target = fixture["contexts"], case["target"]
    pending, feedback, steps = [], [], []
    missing, delays = set(case["missing_rows"]), case.get("delay_by_row", {})
    for index, context in enumerate(case["contexts"]):
        ready = [e for e in pending if e["due_tick"] <= index]
        pending = [e for e in pending if e["due_tick"] > index]
        for event in ready:
            feedback.append({"row": event["row"], "route": event["route"],
                             "vector": event["vector"], "useful_verified": event["useful_verified"],
                             "received_tick": index})
        observed = [{"vector": e["vector"]} for e in feedback]
        debt = _debt(observed, target)
        gates = case["gates"][context]
        routes = [r for r in fixture["route_order"] if gates.get(r) is True]
        profiles = contexts[context]
        route = _select(policy, routes, profiles, debt, target)
        steps.append({"row": index, "context": context, "route": route,
                      "feedback_before": [e["row"] for e in feedback],
                      "forecast": list(profiles[route]["forecast"]),
                      "hard_gate_pass": bool(gates[route])})
        actual = _actual(case, context, route, index, contexts)
        if index not in missing:
            pending.append({"row": index, "route": route, "vector": actual["vector"],
                            "useful_verified": actual["useful_verified"],
                            "due_tick": index + int(delays.get(str(index), 0)) + 1})
    for tick in range(len(case["contexts"]), 2 * len(case["contexts"]) + 1):
        ready = [e for e in pending if e["due_tick"] <= tick]
        pending = [e for e in pending if e["due_tick"] > tick]
        for event in ready:
            feedback.append({"row": event["row"], "route": event["route"],
                             "vector": event["vector"], "useful_verified": event["useful_verified"],
                             "received_tick": tick})
    feedback.sort(key=lambda e: e["row"])
    returned = {e["row"] for e in feedback}
    unknown = [i for i in range(len(steps)) if i not in returned]
    complete = not unknown
    if complete:
        means = [sum(e["vector"][d] for e in feedback) / len(steps)
                 for d in range(len(target))]
        claim = "WITHIN_TARGET" if all(means[d] <= target[d] + TOL
                                       for d in range(len(target))) else "OUTSIDE_TARGET"
    else:
        means, claim = None, "UNKNOWN_INCOMPLETE_FEEDBACK"
    maximum = [max((e["vector"][d] for e in feedback), default=None)
               for d in range(len(target))]
    return {"steps": steps, "feedback": feedback, "unknown_feedback_rows": unknown,
            "complete_feedback": complete, "observed_mean": means,
            "max_observed_single_episode": maximum,
            "verified_useful_count": sum(bool(e["useful_verified"]) for e in feedback),
            "target_claim": claim}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    raw = run(fixture)
    Path(args.output).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": raw["schema"], "cases": len(raw["policies"]),
                      "policies_per_case": len(POLICIES)}))


if __name__ == "__main__":
    main()

