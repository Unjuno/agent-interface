#!/usr/bin/env python3
"""Independent exact finite-fixture auditor; imports no candidate code."""
import json
import sys
from fractions import Fraction


EXPECTED_IDS = {
    "fast_receipt_complete_case_inversion",
    "equal_delay_null",
    "known_window_noninformative_censoring",
    "informative_censoring_or_ambiguous_attribution",
    "all_pending_initial_period",
}


def exact_bounds(rows):
    total = len(rows)
    yes = sum(row.get("effect_status") == "VERIFIED_SUCCESS" for row in rows)
    no = sum(row.get("effect_status") == "VERIFIED_FAILURE" for row in rows)
    pending = sum(row.get("effect_status") == "PENDING" for row in rows)
    assert total and yes + no + pending == total
    return Fraction(yes, total), Fraction(yes + pending, total)


def audit(visible, truth, candidate):
    errors = []
    cases = {x["case_id"]: x for x in visible.get("cases", [])}
    if set(cases) != EXPECTED_IDS:
        errors.append("fixture_case_set_mismatch")
    expected = truth.get("cases", {})
    observed = candidate.get("cases", {})
    if set(expected) != EXPECTED_IDS or set(observed) != EXPECTED_IDS:
        errors.append("result_case_set_mismatch")
    checks = {}
    for case_id in sorted(EXPECTED_IDS & set(cases) & set(expected) & set(observed)):
        case = cases[case_id]
        route_rows = {}
        ids = set()
        obligations = set()
        for row in case.get("attempts", []):
            if row.get("id") in ids or row.get("obligation_id") in obligations:
                errors.append(case_id + ":duplicate_attempt_or_obligation")
            ids.add(row.get("id")); obligations.add(row.get("obligation_id"))
            if row.get("effect_status") not in {"VERIFIED_SUCCESS", "VERIFIED_FAILURE", "PENDING"}:
                errors.append(case_id + ":invalid_effect_status")
            if row.get("effect_status") == "PENDING" and row.get("effect_ms") is not None:
                errors.append(case_id + ":pending_has_effect_time")
            if row.get("eligible"):
                route_rows.setdefault(row["route"], []).append(row)
        want = expected[case_id].get("expected")
        got = observed[case_id].get("classification")
        # A nonidentified case must not expose actionable route bounds.
        if want != "NONIDENTIFIABLE":
            for route, rows in route_rows.items():
                lo, hi = exact_bounds(rows)
                candidate_bound = observed[case_id].get("bounds", {}).get(route, {})
                if candidate_bound.get("lower") != str(lo) or candidate_bound.get("upper") != str(hi) or candidate_bound.get("n") != len(rows):
                    errors.append(case_id + ":bound_mismatch:" + route)
        elif observed[case_id].get("bounds"):
            errors.append(case_id + ":nonidentified_case_exposes_bounds")
        if got != want:
            errors.append(case_id + ":classification_mismatch")
        if case_id == "fast_receipt_complete_case_inversion" and got not in {"NO_RANKING", "NONIDENTIFIABLE"}:
            errors.append("receipt_or_complete_case_inversion_not_rejected")
        if case_id == "all_pending_initial_period" and any(
            observed[case_id].get("bounds", {}).get(r, {}).get("lower") != "0" or
            observed[case_id].get("bounds", {}).get(r, {}).get("upper") != "1"
            for r in route_rows
        ):
            errors.append("pending_not_bounded_zero_to_one")
        checks[case_id] = {"expected": want, "actual": got, "passed": got == want}
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL", "reconstructed": len(checks), "case_checks": checks, "errors": errors}


def main(visible_path, truth_path, candidate_path, output_path):
    with open(visible_path, encoding="utf-8") as f: visible = json.load(f)
    with open(truth_path, encoding="utf-8") as f: truth = json.load(f)
    with open(candidate_path, encoding="utf-8") as f: candidate = json.load(f)
    result = audit(visible, truth, candidate)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True); f.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:5]))
