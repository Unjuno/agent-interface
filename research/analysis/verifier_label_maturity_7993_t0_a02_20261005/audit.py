"""Independent raw-only exact auditor; intentionally imports no candidate code."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
from fractions import Fraction
from pathlib import Path


ESTIMAND = "SUPERPOPULATION_EXPECTED_ERROR_RISK"


def enc(value: Fraction | None) -> str | None:
    if value is None:
        return None
    return f"{value.numerator}/{value.denominator}"


def reconstruct(public: dict) -> dict:
    rows_out = []
    for case in public["ipcw_cases"]:
        model = case["censor_model"]
        q = {name: Fraction(value) for name, value in model["resolution_probability"].items()}
        if model["declared"] != "KNOWN_INDEPENDENT_WITHIN_STRATUM" or any(value == 0 for value in q.values()):
            raise ValueError("eligible case has an unsupported or zero-support model")
        total = Fraction(0)
        for row in case["rows"]:
            if row["status"] == "RESOLVED":
                total += Fraction(row["error"], 1) / q[row["stratum"]]
            elif row["status"] != "UNRESOLVED":
                raise ValueError("unknown resolution status")
        rows_out.append(
            {
                "case_id": case["case_id"],
                "status": "ASSUMPTION_CONDITIONAL_ESTIMATE",
                "estimand": ESTIMAND,
                "estimate": enc(total / case["population_size"]),
                "finite_cohort_point_claim": None,
            }
        )
    zero = public["zero_support_case"]
    return {
        "schema": "unjuno.issue7993.ipcw_candidate.v1",
        "cases": rows_out,
        "zero_support": {
            "case_id": zero["case_id"],
            "status": "UNKNOWN_NONPOSITIVITY",
            "estimand": ESTIMAND,
            "estimate": None,
            "finite_cohort_point_claim": None,
        },
    }


def check(public: dict, truth: dict, candidate_output: dict) -> list[str]:
    errors: list[str] = []
    expected_output = reconstruct(public)
    if candidate_output != expected_output:
        errors.append("candidate output differs from independent row reconstruction")

    design = truth["design"]
    strata = design["strata"]
    p = {name: Fraction(value) for name, value in design["error_probability"].items()}
    target = sum((p[stratum] for stratum in strata), Fraction(0)) / len(strata)
    if target != Fraction(design["true_expected_risk"]):
        errors.append("declared expected-risk target does not match stratum design")
    if design["independent_resolution_given_stratum"] is not True:
        errors.append("the eligible censoring design lacks its declared independence condition")

    oracle = {row["case_id"]: row for row in truth["ipcw_cases"]}
    public_cases = {row["case_id"]: row for row in public["ipcw_cases"]}
    candidate_cases = {row["case_id"]: row for row in candidate_output.get("cases", [])}
    if len(public_cases) != 64 or len(oracle) != 64 or set(public_cases) != set(oracle):
        errors.append("the finite enumerated input/truth frame is not exactly 64 cases")
    if set(candidate_cases) != set(public_cases):
        errors.append("candidate omitted or added an enumerated case")

    observed_states = set()
    total_weight = Fraction(0)
    weighted_estimate = Fraction(0)
    for case_id, case in public_cases.items():
        record = oracle.get(case_id)
        if record is None:
            continue
        errors_vector = tuple(record["latent_errors"])
        resolved_vector = tuple(record["resolved"])
        state_key = (errors_vector, resolved_vector[:2])
        if state_key in observed_states:
            errors.append(f"{case_id}: duplicate latent/resolution state")
        observed_states.add(state_key)
        if resolved_vector[2:] != (1, 1):
            errors.append(f"{case_id}: q=1 stratum failed to resolve")
        if len(errors_vector) != 4 or len(resolved_vector) != 4:
            errors.append(f"{case_id}: incorrect four-unit oracle width")
            continue

        q = {name: Fraction(value) for name, value in case["censor_model"]["resolution_probability"].items()}
        if q != {"A": Fraction(1, 2), "B": Fraction(1, 1)}:
            errors.append(f"{case_id}: unexpected resolution model")
        recomputed_weight = Fraction(1)
        for index, (stratum, error, resolved) in enumerate(zip(strata, errors_vector, resolved_vector)):
            recomputed_weight *= p[stratum] if error else 1 - p[stratum]
            if stratum == "A":
                recomputed_weight *= q[stratum] if resolved else 1 - q[stratum]
            elif not resolved:
                recomputed_weight = Fraction(0)
        weight = Fraction(record["probability_weight"])
        if weight != recomputed_weight:
            errors.append(f"{case_id}: probability weight is inconsistent with the design")
        total_weight += weight

        rows_by_id = {row["row_id"]: row for row in case["rows"]}
        for index, (stratum, error, resolved) in enumerate(zip(strata, errors_vector, resolved_vector)):
            row = rows_by_id.get(f"u{index}")
            if row is None or row.get("stratum") != stratum:
                errors.append(f"{case_id}: row identity or stratum mismatch")
                continue
            if (row["status"] == "RESOLVED") != bool(resolved):
                errors.append(f"{case_id}: visible status disagrees with resolution truth")
            if resolved and row.get("error") != error:
                errors.append(f"{case_id}: visible resolved outcome disagrees with truth")
            if not resolved and "error" in row:
                errors.append(f"{case_id}: candidate-visible unresolved row leaked its outcome")

        candidate_row = candidate_cases.get(case_id)
        if candidate_row is not None and candidate_row.get("estimate") is not None:
            weighted_estimate += weight * Fraction(candidate_row["estimate"])

    all_states = {
        (tuple(y), tuple(d))
        for y in itertools.product((0, 1), repeat=4)
        for d in itertools.product((0, 1), repeat=2)
    }
    if observed_states != all_states:
        errors.append("the enumerated latent/outcome state support is incomplete")
    if total_weight != 1:
        errors.append(f"exact joint probability mass is {enc(total_weight)}, not 1/1")
    if weighted_estimate != target:
        errors.append(
            f"exact IPCW expected value {enc(weighted_estimate)} differs from target {enc(target)}"
        )

    zero_case = public["zero_support_case"]
    zero_truth = truth["zero_support_truth"]
    if zero_case["censor_model"]["resolution_probability"].get("A") != "0/1":
        errors.append("zero-support control is not zero support")
    zrows = {row["row_id"]: row for row in zero_case["rows"]}
    if zrows.get("zA", {}).get("status") != "UNRESOLVED" or "error" in zrows.get("zA", {}):
        errors.append("zero-support unresolved outcome is not hidden")
    if len(zero_truth["latent_errors"]) != zero_case["population_size"]:
        errors.append("zero-support oracle width mismatch")
    zero_out = candidate_output.get("zero_support", {})
    if zero_out.get("status") != "UNKNOWN_NONPOSITIVITY" or zero_out.get("estimate") is not None:
        errors.append("zero support did not return UNKNOWN without an estimate")

    return errors


def mutate(output: dict) -> dict[str, dict]:
    variants = {}
    m = copy.deepcopy(output)
    m["cases"].pop()
    variants["drop_enumerated_case"] = m
    m = copy.deepcopy(output)
    m["cases"][0]["estimate"] = "0/1" if m["cases"][0]["estimate"] != "0/1" else "1/1"
    variants["change_cell_estimate"] = m
    m = copy.deepcopy(output)
    m["cases"][0]["estimand"] = "FINITE_COHORT_REALIZED_RISK"
    variants["conflate_superpopulation_with_cohort"] = m
    m = copy.deepcopy(output)
    m["cases"][0]["finite_cohort_point_claim"] = m["cases"][0]["estimate"]
    variants["add_finite_cohort_point_claim"] = m
    m = copy.deepcopy(output)
    m["zero_support"]["status"] = "ASSUMPTION_CONDITIONAL_ESTIMATE"
    m["zero_support"]["estimate"] = "0/1"
    variants["estimate_through_zero_support"] = m
    m = copy.deepcopy(output)
    m["zero_support"]["finite_cohort_point_claim"] = "0/1"
    variants["claim_finite_cohort_risk_at_zero_support"] = m
    return variants


def audit_document(public: dict, truth: dict, output: dict) -> dict:
    errors = check(public, truth, output)
    mutations = {
        name: {"rejected": bool(check(public, truth, variant)), "errors": check(public, truth, variant)}
        for name, variant in mutate(output).items()
    }
    if not all(result["rejected"] for result in mutations.values()):
        errors.append("one or more frozen mutation controls were accepted")
    disposition = "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD"
    target = Fraction(truth["design"]["true_expected_risk"])
    weighted = Fraction(0)
    truth_by_id = {row["case_id"]: row for row in truth["ipcw_cases"]}
    for row in output["cases"]:
        weighted += Fraction(truth_by_id[row["case_id"]]["probability_weight"]) * Fraction(row["estimate"])
    return {
        "schema": "unjuno.issue7993.ipcw_audit.v1",
        "disposition": disposition,
        "scope": "exact IPCW expectation subgate only; not full Issue #7993 completion",
        "public_case_count": len(public["ipcw_cases"]),
        "state_support_count": 64,
        "exact_probability_mass": "1/1",
        "exact_ipcw_expectation": enc(weighted),
        "true_design_risk": enc(target),
        "independent_errors": errors,
        "mutation_controls": mutations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    public = json.loads(Path(args.input).read_text(encoding="utf-8"))
    truth = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    candidate_output = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    result = audit_document(public, truth, candidate_output)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
