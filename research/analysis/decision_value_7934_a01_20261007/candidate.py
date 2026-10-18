import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def entropy(weights):
    total = sum(weights)
    if total <= 0:
        return 0.0
    return -sum((w / total) * math.log2(w / total) for w in weights if w > 0)


def posterior(case):
    states = list(case["states"])
    for item in case.get("history", []):
        states = [s for s in states if s["signals"].get(item["check"]) == item["outcome"]]
    total = sum(s["weight"] for s in states)
    if total <= 0:
        return []
    return [(s, s["weight"] / total) for s in states]


def bayes_risk(distribution, routes):
    if not distribution:
        return math.inf, None
    risks = {
        route: sum(prob * state["losses"][route] for state, prob in distribution)
        for route in routes
    }
    route = min(routes, key=lambda r: (risks[r], r))
    return risks[route], route


def check_metrics(distribution, routes, check):
    current_risk, _ = bayes_risk(distribution, routes)
    groups = defaultdict(list)
    for state, prob in distribution:
        signal = state["signals"].get(check["id"], "__UNKNOWN__")
        groups[signal].append((state, prob))
    expected_risk = 0.0
    expected_entropy = 0.0
    for group in groups.values():
        mass = sum(prob for _, prob in group)
        conditioned = [(state, prob / mass) for state, prob in group]
        group_risk, _ = bayes_risk(conditioned, routes)
        expected_risk += mass * group_risk
        expected_entropy += mass * entropy([prob for _, prob in conditioned])
    information = entropy([prob for _, prob in distribution]) - expected_entropy
    return {
        "information_bits": round(information, 12),
        "expected_loss_reduction": round(current_risk - expected_risk, 12),
        "net_decision_value": round(current_risk - expected_risk - check["cost"], 12),
    }


def route_map(distribution, routes, check):
    if check is None:
        _, route = bayes_risk(distribution, routes)
        return {"__NO_CHECK__": route or "YIELD"}
    outcomes = {state["signals"].get(check["id"], "__UNKNOWN__") for state, _ in distribution}
    result = {}
    for outcome in sorted(outcomes):
        group = [
            (state, prob)
            for state, prob in distribution
            if state["signals"].get(check["id"], "__UNKNOWN__") == outcome
        ]
        mass = sum(prob for _, prob in group)
        conditioned = [(state, prob / mass) for state, prob in group]
        _, route = bayes_risk(conditioned, routes)
        result[outcome] = route or "YIELD"
    result["__UNKNOWN__"] = "YIELD"
    return result


def decide_case(case, policy_name, policy_config):
    empty = {"disposition": "UNKNOWN", "selected_check": None, "routes_by_outcome": {}, "metrics": {}}
    if not case.get("model_supported", False):
        return empty
    distribution = posterior(case)
    if not distribution:
        return empty
    checks = [c for c in case.get("checks", []) if c.get("fresh") and c.get("independent")]
    if case.get("checks") and not checks:
        return empty
    metrics = {c["id"]: check_metrics(distribution, case["routes"], c) for c in checks}
    selected = None
    if policy_name == "cost_only":
        affordable = [c for c in checks if c["cost"] <= policy_config["max_check_cost"]]
        if affordable:
            selected = min(affordable, key=lambda c: (c["cost"], c["id"]))
    elif policy_name == "entropy_threshold":
        informative = [
            c for c in checks
            if metrics[c["id"]]["information_bits"] >= policy_config["minimum_information_bits"]
            and c["cost"] <= policy_config["max_check_cost"]
        ]
        if informative:
            selected = min(informative, key=lambda c: (-metrics[c["id"]]["information_bits"], c["id"]))
    elif policy_name in ("decision_value", "oracle_best_check"):
        valued = [
            c for c in checks
            if metrics[c["id"]]["net_decision_value"] > policy_config["minimum_net_value"]
        ]
        if valued:
            selected = min(valued, key=lambda c: (-metrics[c["id"]]["net_decision_value"], c["id"]))
    return {
        "disposition": "DECIDE",
        "selected_check": selected["id"] if selected else None,
        "routes_by_outcome": route_map(distribution, case["routes"], selected),
        "metrics": metrics,
    }


def run(model):
    return {
        "schema": "decision-value-7934-candidate-raw-v1",
        "cases": [
            {
                "case_id": case["case_id"],
                "policies": {
                    name: decide_case(case, name, model["policies"][name])
                    for name in ("cost_only", "entropy_threshold", "decision_value", "oracle_best_check")
                },
            }
            for case in model["cases"]
        ],
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py MODEL.json OUTPUT.json")
    model = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    output = run(model)
    Path(argv[2]).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
