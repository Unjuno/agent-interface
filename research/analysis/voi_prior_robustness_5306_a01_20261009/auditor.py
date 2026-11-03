"""Independent exact-rational reference reconstruction and mutation auditor."""
from fractions import Fraction
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _reference(case):
    priors = [Fraction(item) for item in case["plausible_priors_good"]]
    cost = Fraction(case["check_cost"])
    loss = Fraction(case["false_completion_loss"])
    point = Fraction(case["point_prior_good"])
    margin = Fraction(case["confidence_margin"])
    evaluations = []
    for prior in priors:
        avoided = (1 - prior) * loss if case["check_reveals_state"] else Fraction(0)
        residual = avoided - cost
        evaluations.append({
            "prior_good": str(prior),
            "gross_value": str(avoided),
            "net_value": str(residual),
            "decision": "CONTINUE" if residual > 0 else "STOP",
        })

    point_avoided = ((1 - point) * loss
                     if case["check_reveals_state"] else Fraction(0))
    point_residual = point_avoided - cost
    point_action = "CONTINUE" if point_residual > 0 else "STOP"
    if not case["mandatory_checks_complete"]:
        point_action = "YIELD_MANDATORY_INCOMPLETE"
    elif point_action == "CONTINUE" and not case["check_feasible_by_deadline"]:
        point_action = "YIELD_CHECK_INFEASIBLE"
    decisions = {entry["decision"] for entry in evaluations}
    if not case["mandatory_checks_complete"]:
        overall = "YIELD_MANDATORY_INCOMPLETE"
    elif decisions == {"STOP"}:
        overall = "ROBUST_STOP"
    elif decisions == {"CONTINUE"}:
        overall = ("ROBUST_CONTINUE" if case["check_feasible_by_deadline"]
                   else "YIELD_CHECK_INFEASIBLE")
    else:
        overall = "PRIOR_SENSITIVE"

    return {
        "case_id": case["id"],
        "point_voi": {"gross_value": str(point_avoided),
                      "net_value": str(point_residual), "decision": point_action},
        "point_plus_margin": {"gross_value": str(point_avoided),
                              "net_value": str(point_residual), "margin": str(margin),
                              "decision": ("YIELD_MANDATORY_INCOMPLETE"
                                           if not case["mandatory_checks_complete"] else
                                           "YIELD_CHECK_INFEASIBLE"
                                           if point_residual > margin and
                                           not case["check_feasible_by_deadline"] else
                                           "CONTINUE" if point_residual > margin else "STOP")},
        "prior_set_decision": overall,
        "prior_evaluations": evaluations,
        "mandatory_checks_complete": case["mandatory_checks_complete"],
        "check_feasible_by_deadline": case["check_feasible_by_deadline"],
    }


def audit_case(case, row):
    """Return disagreements against the independent reference for one frozen case."""
    expected = _reference(case)
    errors = []
    if row.get("prior_evaluations") != expected["prior_evaluations"]:
        errors.append("prior_evaluations_do_not_match_frozen_set")
    if (not case["mandatory_checks_complete"] and
            row.get("prior_set_decision") != "YIELD_MANDATORY_INCOMPLETE"):
        errors.append("mandatory_gate_was_overridden")
    if (not case["check_feasible_by_deadline"] and
            row.get("prior_set_decision") == "ROBUST_CONTINUE"):
        errors.append("deadline_infeasible_check_admitted")
    if row != expected and "candidate_output_differs_from_independent_reference" not in errors:
        errors.append("candidate_output_differs_from_independent_reference")
    return errors


def main():
    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    candidate = json.loads((HERE / "results" / "candidate.raw.json").read_text(encoding="utf-8"))
    rows = candidate.get("results", [])
    errors = []
    if candidate.get("schema") != "voi-prior-set-robustness-candidate-v1":
        errors.append("candidate_schema_mismatch")
    if len(rows) != len(cases):
        errors.append("candidate_case_count_mismatch")
    by_id = {row.get("case_id"): row for row in rows}
    if len(by_id) != len(rows):
        errors.append("duplicate_or_missing_candidate_case_id")
    for case in cases:
        row = by_id.get(case["id"])
        if row is None:
            errors.append(f"missing_case:{case['id']}")
        else:
            errors.extend(f"{case['id']}:{error}" for error in audit_case(case, row))
    result = {
        "schema": "voi-prior-set-robustness-independent-audit-v1",
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "case_count": len(cases),
        "independently_recomputed": len(cases) - sum(
            1 for case in cases if case["id"] not in by_id),
        "errors": errors,
        "scope": "Exact reconstruction of six authored finite cases; not calibrated probabilities or GUI evidence.",
    }
    destination = HERE / "results" / "audit.raw.json"
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
