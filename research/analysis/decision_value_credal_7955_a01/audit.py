#!/usr/bin/env python3
"""Independent direct-enumeration audit; does not import candidate.py."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
SPEC = json.loads((HERE / "model.json").read_text())
RESULT = json.loads((HERE / "result.json").read_text())
STATES = SPEC["states"]
OBS = SPEC["outcomes"]
ROUTES = SPEC["routes"]
PRIOR = {s: Fraction(SPEC["prior"][s]) for s in STATES}
route_order = list(ROUTES)
assert RESULT["model_sha256"] == hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest()


def f(x):
    return Fraction(str(x))


def channels(c):
    keys = tuple(c["credal_accuracy_grid"])
    axes = [tuple(f(v) for v in c["credal_accuracy_grid"][k]) for k in keys]
    return [dict(zip(keys, row)) for row in itertools.product(*axes)]


def gates(c):
    result = {}
    for chk in c["checks"]:
        causes = []
        if chk["safe"] is not True:
            causes.append("hard_gate_inadmissible")
        if chk["source_epoch"] != c["current_epoch"]:
            causes.append("stale_evidence")
        if set(chk["requires_evidence"]) - set(c["evidence_available"]):
            causes.append("dependency_unresolved")
        result[chk["id"]] = {"admissible": not causes, "reasons": causes}
    return result


def likelihood(a, s, o):
    ready_positive = a
    p = ready_positive if s == "ready" else 1 - ready_positive
    return p if o == "positive" else 1 - p


def value_of_route(r, a, q=None, obs=None):
    # Sum the joint state/observation mass directly; no posterior helper used.
    total = Fraction(0)
    for state in STATES:
        mass = PRIOR[state]
        if q is not None:
            mass *= likelihood(a[q], state, obs)
        total += mass * ROUTES[r][state]
    return total


def chosen_route(a, q=None, obs=None):
    scores = {r: value_of_route(r, a, q, obs) for r in route_order}
    # Deliberately keep the declared route-order tie rule.
    return max(route_order, key=lambda r: (scores[r], -route_order.index(r)))


def voi(a, q, cost):
    baseline = max(value_of_route(r, a) for r in route_order)
    observed = sum(max(value_of_route(r, a, q, o) for r in route_order) for o in OBS)
    return observed - baseline - cost


def ig(a, q):
    prior_entropy = 1.0
    conditional_entropy = 0.0
    for o in OBS:
        masses = {s: PRIOR[s] * likelihood(a[q], s, o) for s in STATES}
        z = sum(masses.values())
        posterior = masses["ready"] / z
        p = float(posterior)
        h = 0.0 if p in (0, 1) else -p * math.log2(p) - (1-p) * math.log2(1-p)
        conditional_entropy += float(z) * h
    return prior_entropy - conditional_entropy


def truth_value(truth, assumed, q, costs):
    if q is None:
        r = chosen_route(assumed)
        return value_of_route(r, truth)
    policy = {o: chosen_route(assumed, q, o) for o in OBS}
    total = sum(PRIOR[s] * likelihood(truth[q], s, o) * ROUTES[policy[o]][s]
                for s in STATES for o in OBS)
    return total - costs[q]


def check_case(c, got):
    assert got["case_id"] == c["id"]
    check_ids = {x["id"] for x in c["checks"]}
    assert set(c["point_accuracy"]) == check_ids
    assert set(c["calibration_sample"]["correct_per_state"]) == check_ids
    assert set(c["credal_accuracy_grid"]) == check_ids
    gate = gates(c)
    assert got["admissibility"] == gate
    eligible = [x["id"] for x in c["checks"] if gate[x["id"]]["admissible"]]
    costs = {x["id"]: f(x["cost"]) for x in c["checks"] if x["id"] in eligible}
    sets = channels(c)
    point = {k: f(v) for k, v in c["point_accuracy"].items()}
    assert all(point[k] in [m[k] for m in sets] for k in point)
    # Confirm the frozen calibration counts are exactly the point estimates.
    for q, ncorrect in c["calibration_sample"]["correct_per_state"].items():
        observed = Fraction(ncorrect, c["calibration_sample"]["n_per_state"])
        assert point[q] == observed, (c["id"], q, observed, point[q])

    per_model = []
    for m in sets:
        per_model.append({q: voi(m, q, costs[q]) for q in eligible})
    expected_details = []
    expected_value_table = {}
    for m in sets:
        md = {"accuracy": {k: str(v) for k, v in m.items()}, "checks": {}}
        model_id = ",".join(f"{k}={m[k]}" for k in m)
        expected_value_table[model_id] = {}
        for q in eligible:
            expected_value_table[model_id][q] = str(voi(m, q, costs[q]))
            post = {}
            routes = {}
            for o in OBS:
                joints = {s: PRIOR[s] * likelihood(m[q], s, o) for s in STATES}
                post[o] = str(joints["ready"] / sum(joints.values()))
                routes[o] = chosen_route(m, q, o)
                for state in STATES:
                    assert sum(likelihood(m[q], state, o) for o in OBS) == 1
            matrix = {
                "ready": {o: str(likelihood(m[q], "ready", o)) for o in OBS},
                "not_ready": {o: str(likelihood(m[q], "not_ready", o)) for o in OBS},
            }
            md["checks"][q] = {"net_voi": str(voi(m, q, costs[q])), "likelihood_matrix": matrix,
                               "posterior_ready": post, "route_by_outcome": routes,
                               "information_gain_bits": ig(m, q)}
        md["model_id"] = model_id
        expected_details.append(md)
    assert got["fixed_measure_net_voi_by_model"] == expected_value_table
    # Candidate serializes model ids using exactly the Cartesian-product order.
    assert len(got["model_details"]) == len(expected_details)
    for actual, expected in zip(got["model_details"], expected_details):
        assert actual["model_id"] == expected["model_id"]
        assert actual["accuracy"] == expected["accuracy"]
        assert set(actual["checks"]) == set(eligible)
        for q in eligible:
            a = actual["checks"][q]
            e = expected["checks"][q]
            assert a["net_voi"] == e["net_voi"]
            assert a["likelihood_matrix"] == e["likelihood_matrix"]
            assert a["posterior_ready"] == e["posterior_ready"]
            assert a["route_by_outcome"] == e["route_by_outcome"]
            assert math.isclose(a["information_gain_bits"], e["information_gain_bits"], abs_tol=1e-12)

    point_values = {q: voi(point, q, costs[q]) for q in eligible}
    assert got["point_model_net_voi"] == {q: str(v) for q, v in point_values.items()}
    point_ig = {q: ig(point, q) for q in eligible}
    assert set(got["point_model_information_gain_bits"]) == set(point_ig)
    for q in eligible:
        assert math.isclose(got["point_model_information_gain_bits"][q], point_ig[q], abs_tol=1e-12)

    envelope = {q: {"lower": min(row[q] for row in per_model), "upper": max(row[q] for row in per_model)} for q in eligible}
    for q in eligible:
        for bound in ("lower", "upper"):
            assert got["fixed_measure_ranking"]["envelopes"][q][bound] == str(envelope[q][bound])
    if not eligible:
        status, expected_envelope = "UNKNOWN_NO_ADMISSIBLE_CHECK", None
    elif max(x["upper"] for x in envelope.values()) <= 0:
        status, expected_envelope = "STOP_NO_POSITIVE_NET_VOI", None
    else:
        winners = [q for q in eligible if all(q == r or envelope[q]["lower"] > envelope[r]["upper"] for r in eligible)]
        if len(winners) == 1:
            status, expected_envelope = "RANKING_INVARIANT", winners[0]
        else:
            status, expected_envelope = "UNCERTAIN_MODEL_DEPENDENT_RANKING", None
    assert got["fixed_measure_ranking"]["status"] == status

    def worst_regret(choice):
        out = []
        for values in per_model:
            best = max([Fraction(0), *values.values()])
            own = Fraction(0) if choice is None else values[choice]
            out.append(best-own)
        return max(out, default=Fraction(0))

    if status == "RANKING_INVARIANT":
        envelope_choice = expected_envelope
    elif status == "UNCERTAIN_MODEL_DEPENDENT_RANKING":
        options = [None, *eligible]
        envelope_choice = min(options, key=lambda q: (worst_regret(q), Fraction(0) if q is None else costs[q], q or ""))
        assert got["fixed_measure_ranking"]["fallback"] == "MINIMAX_REGRET_SEPARATE_FROM_FIXED_MEASURE_ENVELOPE"
        reported = got["fixed_measure_ranking"]["fallback_worst_regret_by_choice"]
        assert reported["no_check"] == str(worst_regret(None))
        for q in eligible:
            assert reported[q] == str(worst_regret(q))
    else:
        envelope_choice = None
    choices = got["policy_selections"]
    assert choices["fixed_measure_envelope"] == envelope_choice
    positive = [q for q in eligible if point_values[q] > 0]
    expected_point = max(positive, key=lambda q: (point_values[q], -ord(q[0]))) if positive else None
    expected_cost = min(eligible, key=lambda q: (costs[q], q)) if eligible else None
    expected_ig = max(eligible, key=lambda q: (point_ig[q], -ord(q[0]))) if eligible else None
    assert choices["point_model"] == expected_point
    assert choices["cost_only"] == expected_cost
    assert choices["information_gain"] == expected_ig
    for q in choices.values():
        assert q is None or q in eligible, (c["id"], q, "inadmissible selection")

    members = sets
    eval_rows = []
    for kind, truths in c["evaluation_accuracy"].items():
        for idx, raw in enumerate(truths):
            truth = {k: f(v) for k, v in raw.items()}
            member = truth in members
            oracle = max([truth_value(truth, truth, None, costs),
                          *(truth_value(truth, truth, q, costs) for q in eligible)])
            policy_scores = {}
            for pname, q in choices.items():
                own = truth_value(truth, point, q, costs)
                policy_scores[pname] = {"selected_check": q, "expected_net_utility": str(own),
                                        "oracle_net_utility": str(oracle), "regret": str(oracle-own)}
            eval_rows.append({"truth_id": f"{kind}_{idx}", "in_credal_set": member,
                              "accuracy": {k: str(v) for k, v in truth.items()}, "policies": policy_scores})
    assert got["evaluation"] == eval_rows
    maxima = {p: max((f(r["policies"][p]["regret"]) for r in eval_rows if r["in_credal_set"]), default=Fraction(0)) for p in choices}
    assert got["max_regret_over_in_set_truths"] == {k: str(v) for k, v in maxima.items()}
    return maxima, eval_rows


assert RESULT["protocol"] == SPEC["protocol"]
assert RESULT["model_sha256"] == hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest()
FREEZE = json.loads((HERE / "FROZEN.json").read_text())
for name, expected_hash in FREEZE["source_sha256"].items():
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected_hash, name
assert len(RESULT["cases"]) == len(SPEC["cases"])
allmax = {}
all_eval = {}
for c, r in zip(SPEC["cases"], RESULT["cases"]):
    allmax[c["id"]], all_eval[c["id"]] = check_case(c, r)

# Preregistered method and bounded hypothesis criteria.
rev = allmax["ranking_reversal"]
assert rev["fixed_measure_envelope"] < rev["point_model"]
for cid in ("singleton_calibrated", "invariant_ranking"):
    assert allmax[cid]["fixed_measure_envelope"] == allmax[cid]["point_model"]
miss = next(x for x in all_eval["truth_outside_credal_set"] if not x["in_credal_set"])
assert miss["policies"]["fixed_measure_envelope"]["selected_check"] == "check_A"
assert miss["policies"]["fixed_measure_envelope"]["regret"] != "0"
assert RESULT["outside_set_not_flagged"] is True
for cid in ("dependency_and_staleness_gates", "no_admissible_check"):
    row = next(x for x in RESULT["cases"] if x["case_id"] == cid)
    assert row["admissibility"]["check_D_hard"] == {"admissible": False, "reasons": ["hard_gate_inadmissible"]}
    assert all(q != "check_D_hard" for q in row["policy_selections"].values())
assert RESULT["pass_method_scoped"] is True and RESULT["h_pass_scoped"] is True
summary = {
    "pass": True,
    "method_disposition": "PASS_METHOD_SCOPED",
    "hypothesis_disposition": "H_PASS_SCOPED",
    "case_count": len(RESULT["cases"]),
    "credal_grid_axes": sum(len(c["credal_accuracy_grid"]) for c in SPEC["cases"]),
    "model_check_value_rows": sum(sum(len(x["checks"]) for x in r["model_details"]) for r in RESULT["cases"]),
    "model_rows": sum(len(x["model_details"]) for x in RESULT["cases"]),
    "evaluation_truths": sum(len(r["evaluation"]) for r in RESULT["cases"]),
    "audit_checks": ["likelihood normalization", "posterior update", "route choice", "fixed-measure VOI",
                     "envelope endpoints", "invariant/uncertain ranking", "hard/dependency/freshness gates",
                     "cost-only and information-gain selection", "oracle regret", "out-of-set limitation"],
    "model_sha256": hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256((HERE / "candidate.py").read_bytes()).hexdigest(),
    "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
    "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(HERE / "audit.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
print(json.dumps(summary, sort_keys=True, indent=2))
