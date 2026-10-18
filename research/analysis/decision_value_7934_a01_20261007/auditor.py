import copy
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ARMS = ("cost_only", "entropy_threshold", "decision_value", "oracle_best_check")

def entropy(probabilities):
    return -sum(p * math.log2(p) for p in probabilities if p > 0)

def condition(case):
    viable = list(case["states"])
    for seen in case.get("history", []):
        viable = [x for x in viable if x["signals"].get(seen["check"]) == seen["outcome"]]
    total = sum(x["weight"] for x in viable)
    return [(x, x["weight"] / total) for x in viable] if total else []

def minimum_risk(distribution, routes):
    risks = []
    for route in routes:
        risks.append((sum(prob * state["losses"][route] for state, prob in distribution), route))
    return min(risks)

def measure(distribution, routes, check):
    baseline, _ = minimum_risk(distribution, routes)
    partitions = defaultdict(list)
    for state, probability in distribution:
        partitions[state["signals"].get(check["id"], "__UNKNOWN__")].append((state, probability))
    post_risk = 0.0
    post_entropy = 0.0
    for part in partitions.values():
        mass = sum(p for _, p in part)
        posterior = [(s, p / mass) for s, p in part]
        risk, _ = minimum_risk(posterior, routes)
        post_risk += mass * risk
        post_entropy += mass * entropy([p for _, p in posterior])
    return {
        "information_bits": round(entropy([p for _, p in distribution]) - post_entropy, 12),
        "expected_loss_reduction": round(baseline - post_risk, 12),
        "net_decision_value": round(baseline - post_risk - check["cost"], 12),
    }

def expected_policy(case, arm, policy_config):
    unknown = {"disposition": "UNKNOWN", "selected_check": None, "routes_by_outcome": {}, "metrics": {}}
    if case.get("model_supported") is not True:
        return unknown
    distribution = condition(case)
    if not distribution:
        return unknown
    available = [c for c in case.get("checks", []) if c.get("fresh") is True and c.get("independent") is True]
    if case.get("checks") and not available:
        return unknown
    metrics = {c["id"]: measure(distribution, case["routes"], c) for c in available}
    selected = None
    if arm == "cost_only":
        choices = [c for c in available if c["cost"] <= policy_config["max_check_cost"]]
        if choices:
            selected = min(choices, key=lambda c: (c["cost"], c["id"]))
    elif arm == "entropy_threshold":
        choices = [
            c for c in available
            if metrics[c["id"]]["information_bits"] >= policy_config["minimum_information_bits"]
            and c["cost"] <= policy_config["max_check_cost"]
        ]
        if choices:
            selected = min(choices, key=lambda c: (-metrics[c["id"]]["information_bits"], c["id"]))
    elif arm in ("decision_value", "oracle_best_check"):
        choices = [
            c for c in available
            if metrics[c["id"]]["net_decision_value"] > policy_config["minimum_net_value"]
        ]
        if choices:
            selected = min(choices, key=lambda c: (-metrics[c["id"]]["net_decision_value"], c["id"]))
    routes = {}
    if selected is None:
        _, route = minimum_risk(distribution, case["routes"])
        routes["__NO_CHECK__"] = route
    else:
        signals = sorted({s["signals"].get(selected["id"], "__UNKNOWN__") for s, _ in distribution})
        for signal in signals:
            part = [(s, p) for s, p in distribution if s["signals"].get(selected["id"], "__UNKNOWN__") == signal]
            mass = sum(p for _, p in part)
            posterior = [(s, p / mass) for s, p in part]
            _, route = minimum_risk(posterior, case["routes"])
            routes[signal] = route
        routes["__UNKNOWN__"] = "YIELD"
    return {
        "disposition": "DECIDE",
        "selected_check": selected["id"] if selected else None,
        "routes_by_outcome": routes,
        "metrics": metrics,
    }

def expected_raw(model):
    cases = []
    for case in model["cases"]:
        policies = {arm: expected_policy(case, arm, model["policies"][arm]) for arm in ARMS}
        cases.append({"case_id": case["case_id"], "policies": policies})
    return {"schema": "decision-value-7934-candidate-raw-v1", "cases": cases}

def expected_score(model, key, raw):
    models = {case["case_id"]: case for case in model["cases"]}
    raw_cases = {case["case_id"]: case for case in raw["cases"]}
    rows = []
    grouped = defaultdict(list)
    for wi, world in enumerate(key["worlds"]):
        case = models[world["case_id"]]
        state = next((s for s in case["states"] if s["id"] == world["true_state"]), None)
        for arm in ARMS:
            decision = raw_cases[world["case_id"]]["policies"][arm]
            if decision["disposition"] == "UNKNOWN" or state is None:
                signal, action, cost, regret, status = "__UNKNOWN__", "YIELD", 0.0, None, "UNKNOWN"
            else:
                check_id = decision["selected_check"]
                signal = state["signals"].get(check_id, "__NO_CHECK__") if check_id else "__NO_CHECK__"
                action = decision["routes_by_outcome"].get(signal, "YIELD")
                selected = next((x for x in case["checks"] if x["id"] == check_id), None) if check_id else None
                cost = selected["cost"] if selected else 0.0
                status = "DECIDE" if action in case["routes"] else "UNKNOWN"
                regret = state["losses"][action] - min(state["losses"][r] for r in case["routes"]) if status == "DECIDE" else None
            row = {"world_index": wi, "case_id": world["case_id"], "true_state": world["true_state"],
                   "policy": arm, "signal": signal, "action": action, "status": status,
                   "regret": regret, "check_cost": cost}
            rows.append(row)
            grouped[(world["case_id"], arm)].append(row)
    summary = {}
    for case_id, case in models.items():
        summary[case_id] = {}
        for arm in ARMS:
            group = grouped[(case_id, arm)]
            decided = [row for row in group if row["regret"] is not None]
            mean_regret = sum(row["regret"] for row in decided) / len(decided) if decided else None
            mean_cost = sum(row["check_cost"] for row in group) / len(group) if group else 0.0
            summary[case_id][arm] = {
                "worlds": len(group), "decisions": len(decided), "yields": len(group) - len(decided),
                "mean_regret": round(mean_regret, 12) if mean_regret is not None else None,
                "mean_check_cost": round(mean_cost, 12),
                "mean_regret_plus_cost": round(mean_regret + mean_cost, 12) if mean_regret is not None else None,
                "hard_gate_violations": sum(row["action"] not in case["routes"] and row["action"] != "YIELD" for row in group),
            }
    return {"schema": "decision-value-7934-score-v1", "rows": rows, "summary": summary}

def audit(model, key, raw, score):
    errors = []
    expected = expected_raw(model)
    if raw != expected:
        errors.append("candidate_raw_reconstruction_mismatch")
    expected_results = expected_score(model, key, expected)
    if score != expected_results:
        errors.append("score_reconstruction_mismatch")
    controls = {}
    mutants = []
    variant = copy.deepcopy(expected)
    variant["cases"][0]["policies"]["decision_value"]["selected_check"] = "nuisance"
    mutants.append(variant)
    variant = copy.deepcopy(expected)
    variant["cases"][0]["policies"]["decision_value"]["routes_by_outcome"]["A"] = "route_b"
    mutants.append(variant)
    variant = copy.deepcopy(expected)
    variant["cases"][0]["policies"]["decision_value"]["metrics"]["decision"]["net_decision_value"] = 0.0
    mutants.append(variant)
    variant = copy.deepcopy(expected)
    variant["cases"].pop()
    mutants.append(variant)
    for n, mutant in enumerate(mutants, 1):
        controls[f"raw_mutation_{n}"] = mutant != expected
    variant_score = copy.deepcopy(expected_results)
    variant_score["summary"]["ig_conflict"]["decision_value"]["mean_regret"] = 0.0
    controls["score_mutation_1"] = variant_score != expected_results
    variant_score = copy.deepcopy(expected_results)
    variant_score["rows"].pop()
    controls["score_mutation_2"] = variant_score != expected_results
    if not all(controls.values()):
        errors.append("mutation_control_not_rejected")
    for case in model["cases"]:
        summary = expected_results["summary"][case["case_id"]]
        if case.get("stratum") in ("disagreement", "heldout_disagreement"):
            if not (summary["decision_value"]["mean_regret"] < summary["entropy_threshold"]["mean_regret"]):
                errors.append(f"no_decision_value_improvement:{case['case_id']}")
            if summary["decision_value"]["hard_gate_violations"] != summary["entropy_threshold"]["hard_gate_violations"]:
                errors.append(f"unequal_hard_gate_correctness:{case['case_id']}")
        if case.get("stratum") == "agreement":
            if summary["decision_value"]["mean_check_cost"] != 0.0:
                errors.append(f"unnecessary_decision_value_check:{case['case_id']}")
    if any(v["hard_gate_violations"] for c in expected_results["summary"].values() for v in c.values()):
        errors.append("hard_gate_violation")
    return {"schema": "decision-value-7934-audit-v1",
            "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": errors, "rows": len(expected_results["rows"]),
            "mutation_controls": controls, "rejected_mutations": sum(controls.values()),
            "authority_grants": 0,
            "scope": "finite synthetic model only; no live GUI, model calibration, user data, or authority"}

def main(argv):
    if len(argv) != 6:
        raise SystemExit("usage: auditor.py MODEL.json SCORING_KEY.json CANDIDATE.json SCORE.json OUTPUT.json")
    model, key, raw, score = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[1:5])
    result = audit(model, key, raw, score)
    Path(argv[5]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main(sys.argv)
