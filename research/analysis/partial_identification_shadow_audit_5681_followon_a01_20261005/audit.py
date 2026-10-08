"""Independent raw-only completion enumerator for the partial-ID candidate."""

import copy
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path


RESULT_KEYS = {
    "case_id",
    "capture_frame_complete",
    "threshold",
    "observed_row_count",
    "confirmed_positive_count",
    "unknown_count",
    "zero_support_unknown_ids",
    "bounds",
    "frame_decision",
    "overall_scope",
    "action_authority",
    "effect_safety_gate",
}


def _rational(value):
    if type(value) is not str:
        raise ValueError("not a rational string")
    result = Fraction(value)
    if f"{result.numerator}/{result.denominator}" != value:
        raise ValueError("noncanonical rational")
    return result


def _ratio(value):
    return f"{value.numerator}/{value.denominator}"


def _expected_from_completion(case):
    rows = case["rows"]
    unknown_rows = [row for row in rows if row["label"] == "unknown"]
    unknown_ids = [row["capture_id"] for row in unknown_rows]
    zero_support = [
        row["capture_id"]
        for row in unknown_rows
        if _rational(row["audit_inclusion_probability"]) == 0
    ]
    positives = sum(1 for row in rows if row["label"] == "positive")
    bounds = None
    decision = "HOLD_INCOMPLETE_FRAME"
    completion_count = 0
    if case["capture_frame_complete"]:
        count = len(rows)
        completion_prevalence = []
        for assignment in itertools.product((False, True), repeat=len(unknown_ids)):
            completion_count += 1
            completion_prevalence.append(Fraction(positives + sum(assignment), count))
        lower = min(completion_prevalence)
        upper = max(completion_prevalence)
        threshold = _rational(case["threshold"])
        bounds = {"lower": _ratio(lower), "upper": _ratio(upper)}
        if lower > threshold:
            decision = "ROBUST_ABOVE_THRESHOLD"
        elif upper < threshold:
            decision = "ROBUST_BELOW_THRESHOLD"
        elif lower == threshold or upper == threshold:
            decision = "HOLD_TOUCHES_THRESHOLD"
        else:
            decision = "HOLD_SPANS_THRESHOLD"
    return (
        {
            "case_id": case["case_id"],
            "capture_frame_complete": case["capture_frame_complete"],
            "threshold": _ratio(_rational(case["threshold"])),
            "observed_row_count": len(rows),
            "confirmed_positive_count": positives,
            "unknown_count": len(unknown_ids),
            "zero_support_unknown_ids": zero_support,
            "bounds": bounds,
            "frame_decision": decision,
            "overall_scope": (
                "HOLD_OUT_OF_FRAME_NOT_IDENTIFIABLE"
                if case["out_of_frame_transition_known"]
                else "CAPTURED_FRAME_ONLY"
            ),
            "action_authority": "NONE",
            "effect_safety_gate": "NOT_EVALUATED",
        },
        completion_count,
    )


def _core_errors(cases, document):
    errors = []
    if type(document) is not dict or set(document) != {"schema", "cases"}:
        return ["top-level schema mismatch"]
    if document["schema"] != "partial-identification-candidate-v1":
        errors.append("schema mismatch")
    results = document["cases"]
    if type(results) is not list or len(results) != len(cases):
        return errors + ["case count mismatch"]
    wanted_ids = [case.get("case_id") for case in cases]
    result_ids = [row.get("case_id") if type(row) is dict else None for row in results]
    if result_ids != wanted_ids or len(set(result_ids)) != len(result_ids):
        errors.append("case identity/order mismatch")
    for case, result in zip(cases, results):
        if type(result) is not dict or set(result) != RESULT_KEYS:
            errors.append(f"{case.get('case_id')}: result schema mismatch")
            continue
        try:
            expected, _ = _expected_from_completion(case)
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append(f"{case.get('case_id')}: invalid frozen case: {exc}")
            continue
        if result != expected:
            errors.append(f"{case['case_id']}: raw differs from completion enumeration")
    return errors


def audit_document(cases, document):
    errors = _core_errors(cases, document)
    completion_count = sum(
        _expected_from_completion(case)[1]
        for case in cases
        if case["capture_frame_complete"]
    )
    if errors:
        return {"errors": errors, "completion_count": completion_count, "mutation_controls_rejected": 0}

    controls = []

    def reject(name, mutate):
        corrupted = copy.deepcopy(document)
        mutate(corrupted)
        controls.append({"name": name, "rejected": bool(_core_errors(cases, corrupted))})

    reject("drop_case", lambda d: d["cases"].pop())
    reject("duplicate_case_id", lambda d: d["cases"][-1].update(case_id=d["cases"][0]["case_id"]))
    reject("narrow_zero_support_bounds", lambda d: d["cases"][0].update(bounds={"lower": "1/2", "upper": "1/2"}))
    reject("promote_all_unknown", lambda d: d["cases"][1].update(frame_decision="ROBUST_BELOW_THRESHOLD"))
    reject("hide_unknown_count", lambda d: d["cases"][0].update(unknown_count=0))
    reject("numeric_bounds_incomplete_frame", lambda d: d["cases"][6].update(bounds={"lower": "0/1", "upper": "1/1"}))
    reject("erase_out_of_frame_limit", lambda d: d["cases"][7].update(overall_scope="CAPTURED_FRAME_ONLY"))
    reject("inject_point_estimate", lambda d: d["cases"][0].update(point_estimate="1/2"))
    reject("change_equality_decision", lambda d: d["cases"][4].update(frame_decision="ROBUST_BELOW_THRESHOLD"))
    reject("alter_zero_support_identity", lambda d: d["cases"][0].update(zero_support_unknown_ids=[]))
    return {
        "errors": [],
        "completion_count": completion_count,
        "mutation_controls": controls,
        "mutation_controls_rejected": sum(1 for item in controls if item["rejected"]),
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: audit.py CASES.json CANDIDATE_RAW.json")
    cases = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    document = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    report = audit_document(cases, document)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not report["errors"] and report.get("mutation_controls_rejected") == 10 else 1)


if __name__ == "__main__":
    main(sys.argv)
