#!/usr/bin/env python3
"""Independent count-based auditor for Issue #8595; imports no candidate code."""
import argparse
import copy
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def expected_case_rows(case):
    result = Counter()
    beta = case["mediator_effect_numerator"]
    for a in (0, 1):
        for d in (0, 1):
            for v in (0, 1):
                rule = case["l_rule"]
                if rule == "xor_a_d_vl":
                    ell = (a + d + v) % 2
                elif rule == "vl":
                    ell = v
                elif rule == "equals_a":
                    ell = a
                else:
                    raise ValueError("unknown frozen state rule")
                threshold_m = 1 + a + d + ell
                for vm in range(6):
                    m = int(vm < threshold_m)
                    threshold_y = 1 + a + d + ell + beta * m
                    for vy in range(8):
                        y = int(vy < threshold_y)
                        result[(a, d, ell, m, y)] += 1
    return result


def fraction(n, d):
    if d == 0:
        raise ZeroDivisionError
    return Fraction(n, d)


def probability(rows, predicate):
    return fraction(sum(1 for r in rows if predicate(r)), len(rows))


def avg_y(rows):
    return fraction(sum(r["y"] for r in rows), len(rows))


def assignment_effect(rows):
    by_a = {a: [r for r in rows if r["a"] == a] for a in (0, 1)}
    return avg_y(by_a[1]) - avg_y(by_a[0])


def gformula(rows, conditioned_on_l):
    psi = []
    for route_m in (0, 1):
        value = Fraction(0, 1)
        for d in (0, 1):
            target = [r for r in rows if r["a"] == 1 and r["d"] == d]
            if conditioned_on_l:
                for ell in (0, 1):
                    target_dl = [r for r in target if r["l"] == ell]
                    if not target_dl:
                        continue
                    source_dl = [r for r in rows if r["a"] == route_m and r["d"] == d and r["l"] == ell]
                    if not source_dl:
                        return None, "NOT_IDENTIFIABLE_POSITIVITY"
                    lprob = fraction(len(target_dl), len(target))
                    for m in (0, 1):
                        p_m = probability(source_dl, lambda r, mm=m: r["m"] == mm)
                        target_dlm = [r for r in target_dl if r["m"] == m]
                        if not target_dlm:
                            return None, "NOT_IDENTIFIABLE_OUTCOME_SUPPORT"
                        value += Fraction(1, 2) * lprob * p_m * avg_y(target_dlm)
            else:
                source_d = [r for r in rows if r["a"] == route_m and r["d"] == d]
                for m in (0, 1):
                    p_m = probability(source_d, lambda r, mm=m: r["m"] == mm)
                    target_dm = [r for r in target if r["m"] == m]
                    if not target_dm:
                        return None, "NOT_IDENTIFIABLE_OUTCOME_SUPPORT"
                    value += Fraction(1, 2) * p_m * avg_y(target_dm)
        psi.append(value)
    return psi[1] - psi[0], "ESTIMATED"


def oracle_effect(case):
    beta = case["mediator_effect_numerator"]
    psi = []
    for mediator_route in (0, 1):
        total = Fraction(0, 1)
        for d in (0, 1):
            for v in (0, 1):
                if case["l_rule"] == "xor_a_d_vl":
                    ell = (1 + d + v) % 2
                elif case["l_rule"] == "vl":
                    ell = v
                else:
                    ell = 1
                p_m = Fraction(1 + mediator_route + d + ell, 6)
                y0 = Fraction(2 + d + ell, 8)
                y1 = Fraction(2 + d + ell + beta, 8)
                total += Fraction(1, 4) * ((1 - p_m) * y0 + p_m * y1)
        psi.append(total)
    return psi[1] - psi[0]


def row_counter(rows):
    return Counter((r["a"], r["d"], r["l"], r["m"], r["y"]) for r in rows)


def hidden_tables(spec):
    n = spec["hidden_confounding_pair"]["observed_cell_counts_per_40"]
    causal = {}
    hidden = {}
    for a in (0, 1):
        for m in (0, 1):
            for y in (0, 1):
                key = f"a{a}_m{m}_y{y}"
                causal[key] = n[key]
                hidden[key] = n[key]
    return causal, hidden


def check(raw, spec):
    if raw.get("schema") != "issue-8595-candidate-raw-v1":
        raise ValueError("raw schema")
    expected_names = {c["name"] for c in spec["standard_cases"]}
    if set(raw.get("case_results", {})) != expected_names:
        raise ValueError("case set")
    by_case = {name: [] for name in expected_names}
    for row in raw.get("rows", []):
        if set(row) != {"case", "a", "d", "l", "m", "y"} or row["case"] not in by_case:
            raise ValueError("row shape")
        by_case[row["case"]].append(row)
    all_checks = 0
    for case in spec["standard_cases"]:
        name = case["name"]
        rows = by_case[name]
        if len(rows) != 384:
            raise ValueError("all-assignment denominator")
        if row_counter(rows) != expected_case_rows(case):
            raise ValueError("structural row reconstruction")
        long_est, long_status = gformula(rows, True)
        naive_est, naive_status = gformula(rows, False)
        total = assignment_effect(rows)
        oracle = oracle_effect(case)
        result = raw["case_results"][name]
        expected_status = "NOT_IDENTIFIABLE_POSITIVITY" if name == "positivity_failure" else "ESTIMATED"
        if result["longitudinal_status"] != expected_status or long_status != expected_status:
            raise ValueError("longitudinal identification status")
        if expected_status == "ESTIMATED" and not math.isclose(result["longitudinal_interventional_effect"], float(long_est), abs_tol=1e-12):
            raise ValueError("longitudinal estimator mismatch")
        if not math.isclose(result["naive_baseline_only_effect"], float(naive_est), abs_tol=1e-12):
            raise ValueError("naive estimator mismatch")
        if not math.isclose(result["total_assignment_effect"], float(total), abs_tol=1e-12):
            raise ValueError("assignment total effect mismatch")
        if not math.isclose(result["structural_oracle_effect"], float(oracle), abs_tol=1e-12):
            raise ValueError("structural oracle mismatch")
        if result["all_assigned_rows_retained"] is not True:
            raise ValueError("assigned denominator marker")
        if name != "positivity_failure" and not math.isclose(float(long_est), float(oracle), abs_tol=1e-12):
            raise ValueError("identified g-formula fails oracle")
        all_checks += len(rows) + 6
    no_med = raw["case_results"]["no_mediation"]
    if abs(no_med["longitudinal_interventional_effect"]) > 1e-12:
        raise ValueError("false pathway in no-mediation case")
    if abs(no_med["naive_baseline_only_effect"]) < spec["frozen_gates"]["naive_no_mediation_abs_min"]:
        raise ValueError("naive comparator did not expose confounding")
    if raw["case_results"]["positivity_failure"]["longitudinal_interventional_effect"] is not None:
        raise ValueError("positivity failure emitted point estimate")
    causal, hidden = hidden_tables(spec)
    pair = raw["hidden_equivalence"]
    if pair["causal_observed_table"] != causal or pair["hidden_observed_table"] != hidden:
        raise ValueError("hidden-equivalence cell counts")
    if pair["causal_observed_table"] != pair["hidden_observed_table"] or pair["same_observed_law"] is not True:
        raise ValueError("observational equivalence not established")
    if not math.isclose(pair["route_total_effect_causal"], 0.4, abs_tol=1e-12) or not math.isclose(pair["route_total_effect_hidden"], 0.4, abs_tol=1e-12):
        raise ValueError("randomized route total effect")
    if pair["pathway_disposition"] != "NOT_IDENTIFIABLE_OBSERVATIONAL_EQUIVALENCE":
        raise ValueError("hidden-confounding disposition")
    if pair["true_mediator_effect_causal"] != 0.8 or pair["true_mediator_effect_hidden"] != 0.0:
        raise ValueError("non-equivalent pathway truths")
    rm = raw["randomized_mediator_control"]
    intervention_rows = rm.get("rows", [])
    if len(intervention_rows) != 40:
        raise ValueError("randomized mediator control row count")
    for a in (0, 1):
        for m in (0, 1):
            cell = [r for r in intervention_rows if r["a"] == a and r["m"] == m]
            if len(cell) != 10 or sum(r["y"] for r in cell) != (9 if m else 1):
                raise ValueError("randomized mediator intervention cell")
    intervention_effect = avg_y([r for r in intervention_rows if r["m"] == 1]) - avg_y([r for r in intervention_rows if r["m"] == 0])
    if rm["effect"] != float(intervention_effect) or rm["effect"] != 0.8:
        raise ValueError("randomized mediator positive control")
    means = raw["known_case_component_factorial_means"]
    expected_means = {"a0_m0":1/8,"a0_m1":3/8,"a1_m0":2/8,"a1_m1":4/8}
    if means != expected_means:
        raise ValueError("component factorial potential means")
    inter = raw["known_case_component_factorial_interaction"]
    path = raw["known_case_interventional_mediator_effect"]
    if not math.isclose(inter, 0.0, abs_tol=1e-12) or not math.isclose(path, 1/24, abs_tol=1e-12) or math.isclose(inter, path, abs_tol=1e-12):
        raise ValueError("component interaction confused with pathway estimand")
    if raw.get("authority") != "NONE":
        raise ValueError("authority inflation")
    return {"checks": all_checks + 16, "rows_reconstructed": sum(map(len, by_case.values())), "cases": len(by_case), "errors": 0}


def mutate_rejected(raw, spec, mutation):
    changed = copy.deepcopy(raw)
    if mutation == "drop_assignment":
        changed["rows"].pop()
    elif mutation == "flip_outcome":
        changed["rows"][0]["y"] ^= 1
    elif mutation == "forge_positivity":
        changed["case_results"]["positivity_failure"]["longitudinal_status"] = "ESTIMATED"
    elif mutation == "forge_hidden_law":
        changed["hidden_equivalence"]["hidden_observed_table"]["a1_m1_y1"] -= 1
    elif mutation == "hide_pathway_nonidentification":
        changed["hidden_equivalence"]["pathway_disposition"] = "IDENTIFIED"
    elif mutation == "inflate_authority":
        changed["authority"] = "ACTION_ALLOWED"
    else:
        raise ValueError("unknown mutation")
    try:
        check(changed, spec)
    except (ValueError, KeyError, TypeError, ZeroDivisionError):
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(ROOT / "spec.json"))
    ap.add_argument("--raw", default=str(ROOT / "results/candidate.raw.json"))
    ap.add_argument("--output", default=str(ROOT / "results/audit.raw.json"))
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit("refusing existing formal audit output")
    spec = json.loads(Path(args.spec).read_text())
    raw_bytes = Path(args.raw).read_bytes()
    raw = json.loads(raw_bytes)
    summary = check(raw, spec)
    mutations = {name: mutate_rejected(raw, spec, name) for name in ("drop_assignment", "flip_outcome", "forge_positivity", "forge_hidden_law", "hide_pathway_nonidentification", "inflate_authority")}
    if not all(mutations.values()):
        raise ValueError("mutation control accepted")
    summary.update({"allocation": spec["allocation"], "disposition": "PASS_METHOD_SCOPED", "mutation_controls": mutations, "mutation_rejections": f"{sum(mutations.values())}/{len(mutations)}", "candidate_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(), "authority": "NONE"})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(summary, sort_keys=True))

if __name__ == "__main__":
    main()
