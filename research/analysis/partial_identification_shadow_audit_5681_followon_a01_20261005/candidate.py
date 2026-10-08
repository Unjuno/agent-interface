"""Closed-form finite-frame partial-identification candidate (no GUI/runtime use)."""

import json
import sys
from fractions import Fraction
from pathlib import Path


CASE_KEYS = {
    "case_id",
    "capture_frame_complete",
    "out_of_frame_transition_known",
    "threshold",
    "rows",
}
ROW_KEYS = {"capture_id", "label", "audit_inclusion_probability"}
LABELS = {"positive", "negative", "unknown"}


def rational(value, field):
    if type(value) is not str:
        raise ValueError(f"{field}: expected canonical rational string")
    try:
        parsed = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{field}: invalid rational") from exc
    if f"{parsed.numerator}/{parsed.denominator}" != value:
        raise ValueError(f"{field}: noncanonical rational")
    return parsed


def ratio(value):
    return f"{value.numerator}/{value.denominator}"


def analyze(case):
    if type(case) is not dict or set(case) != CASE_KEYS:
        raise ValueError("case schema mismatch")
    case_id = case["case_id"]
    if type(case_id) is not str or not case_id:
        raise ValueError("case_id must be nonempty text")
    if type(case["capture_frame_complete"]) is not bool:
        raise ValueError("capture_frame_complete must be bool")
    if type(case["out_of_frame_transition_known"]) is not bool:
        raise ValueError("out_of_frame_transition_known must be bool")
    threshold = rational(case["threshold"], "threshold")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold outside binary prevalence range")
    rows = case["rows"]
    if type(rows) is not list or not rows:
        raise ValueError("rows must be a nonempty list")
    ids = []
    positives = 0
    unknown = 0
    zero_support = []
    for row in rows:
        if type(row) is not dict or set(row) != ROW_KEYS:
            raise ValueError("row schema mismatch")
        capture_id = row["capture_id"]
        if type(capture_id) is not str or not capture_id:
            raise ValueError("capture_id must be nonempty text")
        ids.append(capture_id)
        label = row["label"]
        if type(label) is not str or label not in LABELS:
            raise ValueError("unknown label vocabulary")
        probability = rational(row["audit_inclusion_probability"], "audit_inclusion_probability")
        if not 0 <= probability <= 1:
            raise ValueError("audit probability outside [0, 1]")
        if label == "positive":
            positives += 1
        elif label == "unknown":
            unknown += 1
            if probability == 0:
                zero_support.append(capture_id)
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate capture identity")

    bounds = None
    decision = "HOLD_INCOMPLETE_FRAME"
    if case["capture_frame_complete"]:
        count = len(rows)
        lower = Fraction(positives, count)
        upper = Fraction(positives + unknown, count)
        bounds = {"lower": ratio(lower), "upper": ratio(upper)}
        if lower > threshold:
            decision = "ROBUST_ABOVE_THRESHOLD"
        elif upper < threshold:
            decision = "ROBUST_BELOW_THRESHOLD"
        elif lower == threshold or upper == threshold:
            decision = "HOLD_TOUCHES_THRESHOLD"
        else:
            decision = "HOLD_SPANS_THRESHOLD"

    return {
        "case_id": case_id,
        "capture_frame_complete": case["capture_frame_complete"],
        "threshold": ratio(threshold),
        "observed_row_count": len(rows),
        "confirmed_positive_count": positives,
        "unknown_count": unknown,
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
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py CASES.json OUTPUT.json")
    cases = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    if type(cases) is not list:
        raise ValueError("case input must be a list")
    case_ids = [case.get("case_id") if type(case) is dict else None for case in cases]
    if len(case_ids) != len(set(case_ids)) or any(type(value) is not str or not value for value in case_ids):
        raise ValueError("case identities must be unique nonempty text")
    output = {"schema": "partial-identification-candidate-v1", "cases": [analyze(case) for case in cases]}
    Path(argv[2]).write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(output["cases"]), "action_authority": "NONE"}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
