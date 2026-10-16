#!/usr/bin/env python3
"""Finite likelihood-set VOI selection; all arithmetic except entropy is exact."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
MODEL_PATH = HERE / "model.json"
MODEL = json.loads(MODEL_PATH.read_text())
STATES = MODEL["states"]
OUTCOMES = MODEL["outcomes"]
ROUTES = MODEL["routes"]
PRIOR = {s: Fraction(MODEL["prior"][s]) for s in STATES}
ROUTE_IDS = list(ROUTES)


def frac(x):
    return Fraction(str(x))


def likelihood(accuracy, state, outcome):
    positive = accuracy if state == "ready" else 1 - accuracy
    return positive if outcome == "positive" else 1 - positive


def model_set(case):
    ids = list(case["credal_accuracy_grid"])
    grids = [[frac(x) for x in case["credal_accuracy_grid"][i]] for i in ids]
    models = []
    for values in itertools.product(*grids):
        acc = dict(zip(ids, values))
        mid = ",".join(f"{i}={acc[i]}" for i in ids)
        models.append({"id": mid, "accuracy": acc})
    return models


def admissibility(case):
    decisions = {}
    available = set(case["evidence_available"])
    for check in case["checks"]:
        reasons = []
        if not check["safe"]:
            reasons.append("hard_gate_inadmissible")
        if check["source_epoch"] != case["current_epoch"]:
            reasons.append("stale_evidence")
        if not set(check["requires_evidence"]).issubset(available):
            reasons.append("dependency_unresolved")
        decisions[check["id"]] = {"admissible": not reasons, "reasons": reasons}
    return decisions


def expected_route_utility(route, model_acc, check_id=None, outcome=None):
    if check_id is None:
        return sum(PRIOR[s] * ROUTES[route][s] for s in STATES)
    return sum(PRIOR[s] * likelihood(model_acc[check_id], s, outcome) * ROUTES[route][s] for s in STATES)


def route_map(model_acc, check_id=None):
    if check_id is None:
        return {"no_observation": max(ROUTE_IDS, key=lambda r: (expected_route_utility(r, model_acc), -ROUTE_IDS.index(r)))}
    result = {}
    for outcome in OUTCOMES:
        result[outcome] = max(ROUTE_IDS, key=lambda r: (expected_route_utility(r, model_acc, check_id, outcome), -ROUTE_IDS.index(r)))
    return result


def no_check_value(model_acc):
    return max(expected_route_utility(r, model_acc) for r in ROUTE_IDS)


def check_value(model_acc, check_id, cost):
    after = Fraction(0)
    for outcome in OUTCOMES:
        route = route_map(model_acc, check_id)[outcome]
        after += expected_route_utility(route, model_acc, check_id, outcome)
    return after - no_check_value(model_acc) - cost


def entropy(p):
    p = float(p)
    return 0.0 if p in (0.0, 1.0) else -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def information_gain(model_acc, check_id):
    h_prior = entropy(PRIOR["ready"])
    h_after = 0.0
    for outcome in OUTCOMES:
        p_outcome = sum(PRIOR[s] * likelihood(model_acc[check_id], s, outcome) for s in STATES)
        if p_outcome:
            p_ready = PRIOR["ready"] * likelihood(model_acc[check_id], "ready", outcome) / p_outcome
            h_after += float(p_outcome) * entropy(p_ready)
    return h_prior - h_after


def robust_ranking(values):
    ids = list(next(iter(values.values()))) if values else []
    if not ids:
        return {"status": "UNKNOWN_NO_ADMISSIBLE_CHECK", "selected": None, "envelopes": {}}
    envelopes = {i: {"lower": min(v[i] for v in values.values()), "upper": max(v[i] for v in values.values())} for i in ids}
    if max(envelopes[i]["upper"] for i in ids) <= 0:
        return {"status": "STOP_NO_POSITIVE_NET_VOI", "selected": None, "envelopes": envelopes}
    winners = [i for i in ids if all(i == j or envelopes[i]["lower"] > envelopes[j]["upper"] for j in ids)]
    if len(winners) == 1:
        return {"status": "RANKING_INVARIANT", "selected": winners[0], "envelopes": envelopes}
    return {"status": "UNCERTAIN_MODEL_DEPENDENT_RANKING", "selected": None, "envelopes": envelopes}


def minimax_regret(values, costs):
    choices = [None, *(next(iter(values.values())).keys() if values else [])]
    worst = {}
    for choice in choices:
        losses = []
        for per_model in values.values():
            best = max(Fraction(0), *per_model.values())
            own = Fraction(0) if choice is None else per_model[choice]
            losses.append(best - own)
        worst[choice or "no_check"] = max(losses, default=Fraction(0))
    selected = min(choices, key=lambda c: (worst[c or "no_check"], Fraction(0) if c is None else costs[c], c or ""))
    return selected, worst


def truth_net_value(truth_acc, assumed_acc, check_id, cost):
    if check_id is None:
        route = route_map(assumed_acc)["no_observation"]
        return sum(PRIOR[s] * ROUTES[route][s] for s in STATES)
    routes = route_map(assumed_acc, check_id)
    return sum(PRIOR[s] * likelihood(truth_acc[check_id], s, o) * ROUTES[routes[o]][s]
               for s in STATES for o in OUTCOMES) - cost


def analyze_case(case):
    gates = admissibility(case)
    checks = [c for c in case["checks"] if gates[c["id"]]["admissible"]]
    check_costs = {c["id"]: frac(c["cost"]) for c in checks}
    point = {k: frac(v) for k, v in case["point_accuracy"].items()}
    models = model_set(case)
    matrix_values = {m["id"]: {c["id"]: check_value(m["accuracy"], c["id"], check_costs[c["id"]]) for c in checks}
                     for m in models}
    point_values = {c["id"]: check_value(point, c["id"], check_costs[c["id"]]) for c in checks}
    if checks:
        positive = [c["id"] for c in checks if point_values[c["id"]] > 0]
        point_choice = max(positive, key=lambda i: (point_values[i], -ord(i[0]))) if positive else None
        cost_choice = min(checks, key=lambda c: (check_costs[c["id"]], c["id"]))["id"]
        igs = {c["id"]: information_gain(point, c["id"]) for c in checks}
        ig_choice = max(igs, key=lambda i: (igs[i], -ord(i[0])))
    else:
        point_choice = cost_choice = ig_choice = None
        igs = {}
    ranking = robust_ranking(matrix_values)
    if ranking["status"] == "RANKING_INVARIANT":
        envelope_choice = ranking["selected"]
        fallback_worst = {}
    elif ranking["status"] == "UNCERTAIN_MODEL_DEPENDENT_RANKING":
        envelope_choice, fallback_worst = minimax_regret(matrix_values, check_costs)
        ranking["fallback"] = "MINIMAX_REGRET_SEPARATE_FROM_FIXED_MEASURE_ENVELOPE"
        ranking["fallback_worst_regret_by_choice"] = {k: str(v) for k, v in fallback_worst.items()}
        ranking["selected"] = envelope_choice
    else:
        envelope_choice = None
    policies = {"point_model": point_choice, "cost_only": cost_choice, "information_gain": ig_choice,
                "fixed_measure_envelope": envelope_choice}
    member_accuracy = [{k: v for k, v in m["accuracy"].items()} for m in models]
    evaluation = []
    for truth_kind, truths in case["evaluation_accuracy"].items():
        for idx, raw_truth in enumerate(truths):
            truth = {k: frac(v) for k, v in raw_truth.items()}
            in_set = truth in member_accuracy
            truth_id = f"{truth_kind}_{idx}"
            best = max([truth_net_value(truth, truth, None, Fraction(0)),
                        *(truth_net_value(truth, truth, c["id"], check_costs[c["id"]]) for c in checks)])
            policy_scores = {}
            for pname, choice in policies.items():
                value = truth_net_value(truth, point, choice, Fraction(0) if choice is None else check_costs[choice])
                policy_scores[pname] = {"selected_check": choice, "expected_net_utility": str(value),
                                        "oracle_net_utility": str(best), "regret": str(best - value)}
            evaluation.append({"truth_id": truth_id, "in_credal_set": in_set, "accuracy": {k: str(v) for k, v in truth.items()},
                               "policies": policy_scores})
    details = []
    for model in models:
        ma = model["accuracy"]
        check_details = {}
        for check in checks:
            cid = check["id"]
            check_details[cid] = {
                "net_voi": str(matrix_values[model["id"]][cid]),
                "likelihood_matrix": {
                    "ready": {"positive": str(likelihood(ma[cid], "ready", "positive")), "negative": str(likelihood(ma[cid], "ready", "negative"))},
                    "not_ready": {"positive": str(likelihood(ma[cid], "not_ready", "positive")), "negative": str(likelihood(ma[cid], "not_ready", "negative"))}},
                "posterior_ready": {o: str(PRIOR["ready"] * likelihood(ma[cid], "ready", o) /
                    sum(PRIOR[s] * likelihood(ma[cid], s, o) for s in STATES)) for o in OUTCOMES},
                "route_by_outcome": route_map(ma, cid),
                "information_gain_bits": information_gain(ma, cid)
            }
        details.append({"model_id": model["id"], "accuracy": {k: str(v) for k, v in ma.items()}, "checks": check_details})
    in_set_regret = {p: max((frac(e["policies"][p]["regret"]) for e in evaluation if e["in_credal_set"]), default=Fraction(0))
                     for p in policies}
    return {
        "case_id": case["id"],
        "admissibility": gates,
        "credal_model_count": len(models),
        "point_model_net_voi": {k: str(v) for k, v in point_values.items()},
        "point_model_information_gain_bits": igs,
        "fixed_measure_net_voi_by_model": {k: {i: str(v) for i, v in m.items()} for k, m in matrix_values.items()},
        "fixed_measure_ranking": {**ranking, "envelopes": {k: {a: str(v) for a, v in item.items()} for k, item in ranking["envelopes"].items()}},
        "policy_selections": policies,
        "max_regret_over_in_set_truths": {k: str(v) for k, v in in_set_regret.items()},
        "evaluation": evaluation,
        "model_details": details
    }


def main():
    rows = [analyze_case(c) for c in MODEL["cases"]]
    # These are method outcomes, not performance claims for a deployment.
    pass_method = (
        rows[0]["fixed_measure_ranking"]["status"] == "RANKING_INVARIANT"
        and rows[1]["fixed_measure_ranking"]["status"] == "RANKING_INVARIANT"
        and rows[2]["fixed_measure_ranking"]["status"] == "UNCERTAIN_MODEL_DEPENDENT_RANKING"
        and rows[4]["admissibility"]["check_B_dep"]["admissible"] is False
        and rows[4]["admissibility"]["check_C_stale"]["admissible"] is False
        and rows[4]["admissibility"]["check_D_hard"]["admissible"] is False
        and rows[5]["fixed_measure_ranking"]["status"] == "UNKNOWN_NO_ADMISSIBLE_CHECK"
        and rows[5]["admissibility"]["check_D_hard"]["admissible"] is False
    )
    in_set_h = (
        Fraction(rows[2]["max_regret_over_in_set_truths"]["fixed_measure_envelope"])
        < Fraction(rows[2]["max_regret_over_in_set_truths"]["point_model"])
        and rows[0]["max_regret_over_in_set_truths"]["fixed_measure_envelope"] == rows[0]["max_regret_over_in_set_truths"]["point_model"]
        and rows[1]["max_regret_over_in_set_truths"]["fixed_measure_envelope"] == rows[1]["max_regret_over_in_set_truths"]["point_model"]
    )
    outside_rows = [e for row in rows for e in row["evaluation"] if not e["in_credal_set"]]
    outside_not_flagged = bool(outside_rows) and all(
        row["fixed_measure_ranking"]["status"] == "RANKING_INVARIANT"
        and row["policy_selections"]["fixed_measure_envelope"] is not None
        for row in rows if any(not e["in_credal_set"] for e in row["evaluation"]))
    result = {"protocol": MODEL["protocol"], "scope": "finite authored likelihood models only; no live calibration or GUI result",
              "model_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
              "decision_rule": MODEL["ranking_rule"], "fallback_rule": MODEL["fallback_rule"],
              "cases": rows, "pass_method_scoped": pass_method,
              "h_pass_scoped": in_set_h,
              "outside_set_not_flagged": outside_not_flagged}
    print(json.dumps(result, sort_keys=True, indent=2))
    if not (pass_method and in_set_h):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
