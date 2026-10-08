#!/usr/bin/env python3
"""Finite no-model simulator and plug-in estimators for Issue #8595."""
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_spec(path):
    return json.loads(Path(path).read_text())


def l_value(rule, a, d, vl):
    if rule == "xor_a_d_vl":
        return (a + d + vl) % 2
    if rule == "vl":
        return vl
    if rule == "equals_a":
        return a
    raise ValueError("unknown L rule")


def standard_rows(spec):
    rows = []
    dom = spec["domains"]
    for case in spec["standard_cases"]:
        beta = case["mediator_effect_numerator"]
        for a in dom["route_assignment_a"]:
            for d in dom["baseline_difficulty_d"]:
                for vl in dom["state_noise_vl"]:
                    l = l_value(case["l_rule"], a, d, vl)
                    pnum = 1 + a + d + l
                    for vm in dom["mediator_noise_vm"]:
                        m = int(vm < pnum)
                        qnum = 1 + a + d + l + beta * m
                        for vy in dom["outcome_noise_vy"]:
                            y = int(vy < qnum)
                            rows.append({"case": case["name"], "a": a, "d": d, "l": l, "m": m, "y": y})
    return rows


def mean(rows, predicate, field):
    picked = [r[field] for r in rows if predicate(r)]
    return None if not picked else sum(picked) / len(picked)


def probability(rows, predicate):
    if not rows:
        return None
    return sum(1 for row in rows if predicate(row)) / len(rows)

def total_effect(rows):
    mu1 = mean(rows, lambda r: r["a"] == 1, "y")
    mu0 = mean(rows, lambda r: r["a"] == 0, "y")
    return mu1 - mu0


def gformula(rows, include_l):
    """Estimate psi(g_a) under outcome assignment 1, then contrast a=1 vs 0."""
    values = []
    for mediator_route in (0, 1):
        psi = 0.0
        for d in (0, 1):
            baseline_weight = 0.5
            outcome_rows_d = [r for r in rows if r["a"] == 1 and r["d"] == d]
            if include_l:
                for l in (0, 1):
                    l_rows = [r for r in outcome_rows_d if r["l"] == l]
                    if not l_rows:
                        # A zero-mass target stratum contributes nothing.
                        continue
                    l_weight = len(l_rows) / len(outcome_rows_d)
                    source = [r for r in rows if r["a"] == mediator_route and r["d"] == d and r["l"] == l]
                    if not source:
                        return None, "NOT_IDENTIFIABLE_POSITIVITY"
                    for m in (0, 1):
                        pm = probability(source, lambda r: r["m"] == m)
                        outcome = [r for r in l_rows if r["m"] == m]
                        if not outcome:
                            return None, "NOT_IDENTIFIABLE_OUTCOME_SUPPORT"
                        py = mean(outcome, lambda r: True, "y")
                        psi += baseline_weight * l_weight * pm * py
            else:
                source = [r for r in rows if r["a"] == mediator_route and r["d"] == d]
                for m in (0, 1):
                    pm = probability(source, lambda r: r["m"] == m)
                    outcome = [r for r in outcome_rows_d if r["m"] == m]
                    if not outcome:
                        return None, "NOT_IDENTIFIABLE_OUTCOME_SUPPORT"
                    py = mean(outcome, lambda r: True, "y")
                    psi += baseline_weight * pm * py
        values.append(psi)
    return values[1] - values[0], "ESTIMATED"


def oracle_interventional(case):
    """Structural g-formula using frozen equations, independent of observed fitting."""
    beta = case["mediator_effect_numerator"]
    psi = []
    for mediator_route in (0, 1):
        value = 0.0
        for d in (0, 1):
            for vl in (0, 1):
                l = l_value(case["l_rule"], 1, d, vl)
                pnum1 = 1 + mediator_route + d + l
                pm1 = pnum1 / 6.0
                q0 = (1 + 1 + d + l) / 8.0
                q1 = (1 + 1 + d + l + beta) / 8.0
                value += 0.25 * ((1.0 - pm1) * q0 + pm1 * q1)
        psi.append(value)
    return psi[1] - psi[0]


def hidden_pair():
    causal = []
    hidden = []
    for a in (0, 1):
        for u in range(40):
            rm, ry = u % 4, u // 4
            m = int(rm < (1 if a == 0 else 3))
            y = m ^ int(ry == 0)
            causal.append({"a": a, "m": m, "y": y})
        cells = ([(0, 0)] * 27 + [(0, 1)] * 3 + [(1, 0)] + [(1, 1)] * 9) if a == 0 else ([(0, 0)] * 9 + [(0, 1)] + [(1, 0)] * 3 + [(1, 1)] * 27)
        hidden.extend({"a": a, "m": m, "y": y} for m, y in cells)
    return causal, hidden


def observed_table(rows):
    return {f"a{a}_m{m}_y{y}": sum(1 for r in rows if r["a"] == a and r["m"] == m and r["y"] == y) for a in (0, 1) for m in (0, 1) for y in (0, 1)}


def run(spec):
    all_rows = standard_rows(spec)
    case_results = {}
    for case in spec["standard_cases"]:
        rows = [r for r in all_rows if r["case"] == case["name"]]
        long_value, long_status = gformula(rows, True)
        naive_value, naive_status = gformula(rows, False)
        case_results[case["name"]] = {
            "rows": len(rows), "total_assignment_effect": total_effect(rows),
            "longitudinal_interventional_effect": long_value, "longitudinal_status": long_status,
            "naive_baseline_only_effect": naive_value, "naive_status": naive_status,
            "structural_oracle_effect": oracle_interventional(case),
            "all_assigned_rows_retained": len(rows) == 384
        }
    causal, hidden = hidden_pair()
    pair = {
        "causal_observed_table": observed_table(causal),
        "hidden_observed_table": observed_table(hidden),
        "same_observed_law": observed_table(causal) == observed_table(hidden),
        "route_total_effect_causal": total_effect(causal),
        "route_total_effect_hidden": total_effect(hidden),
        "mediator_prevalence_difference": mean(causal, lambda r: r["a"] == 1, "m") - mean(causal, lambda r: r["a"] == 0, "m"),
        "true_mediator_effect_causal": 0.8,
        "true_mediator_effect_hidden": 0.0,
        "pathway_disposition": "NOT_IDENTIFIABLE_OBSERVATIONAL_EQUIVALENCE"
    }
    randomized_rows = []
    for a in (0, 1):
        for m in (0, 1):
            for error_index in range(10):
                randomized_rows.append({"a": a, "m": m, "error_index": error_index, "y": m ^ int(error_index == 0)})
    randomized_effect = mean(randomized_rows, lambda r: r["m"] == 1, "y") - mean(randomized_rows, lambda r: r["m"] == 0, "y")
    randomized_mediator = {"effect": randomized_effect, "rows": randomized_rows, "intervention": "randomize M independently; observe Y=M XOR Bernoulli(0.1)"}
    q = lambda a, m: (1 + a + 2 * m) / 8.0
    factorial_means = {f"a{a}_m{m}": q(a, m) for a in (0, 1) for m in (0, 1)}
    component_interaction = factorial_means["a1_m1"] - factorial_means["a1_m0"] - factorial_means["a0_m1"] + factorial_means["a0_m0"]
    known = case_results["known_mediation"]
    return {
        "schema": "issue-8595-candidate-raw-v1", "allocation": spec["allocation"],
        "spec_scenario_count": len(case_results), "rows": all_rows, "case_results": case_results,
        "hidden_equivalence": pair, "randomized_mediator_control": randomized_mediator,
        "known_case_component_factorial_means": factorial_means,
        "known_case_component_factorial_interaction": component_interaction,
        "known_case_interventional_mediator_effect": known["longitudinal_interventional_effect"],
        "authority": "NONE"
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(ROOT / "spec.json"))
    ap.add_argument("--output", default=str(ROOT / "results/candidate.raw.json"))
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit("refusing existing formal output")
    raw = run(load_spec(args.spec))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"allocation": raw["allocation"], "rows": len(raw["rows"]), "cases": len(raw["case_results"]), "output": str(out)}, sort_keys=True))

if __name__ == "__main__":
    main()
