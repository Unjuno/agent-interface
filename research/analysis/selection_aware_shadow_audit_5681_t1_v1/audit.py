"""Independent auditor; imports neither the candidate nor its implementation."""

from copy import deepcopy
from fractions import Fraction
import itertools
import json
import sys


def _s(value):
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _expected_rows(case):
    if case == "event_dependent":
        return [
            *[{"source_id": f"event-{i}", "label": 1, "gate_decision": "suppressed", "inclusion_probability": "1/2"} for i in range(4)],
            *[{"source_id": f"quiet-{i}", "label": 0, "gate_decision": "delivered", "inclusion_probability": "1"} for i in range(4)],
        ]
    if case == "label_independent_null":
        return [
            {"source_id": f"null-{i}", "label": int(i < 4), "gate_decision": "delivered", "inclusion_probability": "1/2"}
            for i in range(8)
        ]
    if case == "zero_inclusion":
        return [
            *[{"source_id": f"zero-event-{i}", "label": 1, "gate_decision": "suppressed", "inclusion_probability": "0"} for i in range(4)],
            *[{"source_id": f"zero-quiet-{i}", "label": 0, "gate_decision": "delivered", "inclusion_probability": "1"} for i in range(4)],
        ]
    return None


def _expected_draws(rows):
    randomized = [row for row in rows if Fraction(row["inclusion_probability"]) < 1]
    always = {row["source_id"] for row in rows if Fraction(row["inclusion_probability"]) == 1}
    draws = []
    n = len(rows)
    for choices in itertools.product((0, 1), repeat=len(randomized)):
        selected = set(always)
        probability = Fraction(1)
        for row, included in zip(randomized, choices):
            pi = Fraction(row["inclusion_probability"])
            probability *= pi if included else 1 - pi
            if included:
                selected.add(row["source_id"])
        total = sum((
            Fraction(row["label"]) / Fraction(row["inclusion_probability"])
            for row in rows if row["source_id"] in selected
        ), Fraction(0))
        draws.append({
            "selected_ids": sorted(selected),
            "design_probability": _s(probability),
            "ht_prevalence": _s(total / n),
        })
    expectation = sum(
        Fraction(item["design_probability"]) * Fraction(item["ht_prevalence"])
        for item in draws
    )
    return draws, expectation


def _core(raw):
    errors = []
    if not isinstance(raw, dict) or raw.get("schema") != "selection-aware-shadow-audit-t1-v1":
        return ["invalid top-level schema"]
    if raw.get("design") != "independent_bernoulli_exhaustive":
        errors.append("unexpected sampling design")
    cases = raw.get("cases")
    if not isinstance(cases, dict) or set(cases) != {
        "event_dependent", "label_independent_null", "zero_inclusion", "uncaptured_transient"
    }:
        return ["case table missing or unexpected"]

    for name in ("event_dependent", "label_independent_null", "zero_inclusion"):
        case = cases.get(name)
        expected_rows = _expected_rows(name)
        if not isinstance(case, dict):
            errors.append(f"{name}: missing case")
            continue
        rows = case.get("units")
        if rows != expected_rows:
            errors.append(f"{name}: source IDs, labels, gate decisions, or inclusion probabilities differ")
        if not isinstance(rows, list) or len(rows) != 8:
            errors.append(f"{name}: malformed finite frame")
            continue
        try:
            for row in rows:
                pi = Fraction(row["inclusion_probability"])
                if pi < 0 or pi > 1:
                    raise ValueError("probability outside [0,1]")
            truth = Fraction(sum(row["label"] for row in rows), len(rows))
            delivered = [row for row in rows if row["gate_decision"] == "delivered"]
            delivered_truth = Fraction(sum(row["label"] for row in delivered), len(delivered))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            errors.append(f"{name}: invalid row values")
            continue
        if case.get("frame_size") != 8 or case.get("full_prevalence") != _s(truth):
            errors.append(f"{name}: finite-frame truth mismatch")
        if case.get("delivered_prevalence") != _s(delivered_truth):
            errors.append(f"{name}: delivered-only prevalence mismatch")

        if name == "zero_inclusion":
            if case.get("status") != "NOT_ESTIMABLE" or "ht_expected_prevalence" in case:
                errors.append("zero_inclusion: recovery claim was not refused")
            if (case.get("reasons") != ["zero_inclusion_target"]
                    or case.get("draws") != [] or case.get("draw_count") != 0):
                errors.append("zero_inclusion: refusal metadata mismatch")
            if not any(row["label"] == 1 and row["inclusion_probability"] == "0" for row in rows):
                errors.append("zero_inclusion: missing zero-support target")
            continue

        try:
            expected_draws, expectation = _expected_draws(rows)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            errors.append(f"{name}: cannot independently enumerate the design")
            continue
        if case.get("status") != "ESTIMABLE":
            errors.append(f"{name}: unexpected estimability status")
        if case.get("draw_count") != len(expected_draws) or case.get("draws") != expected_draws:
            errors.append(f"{name}: exhaustive draw table or probabilities mismatch")
        if case.get("ht_expected_prevalence") != _s(expectation):
            errors.append(f"{name}: design expectation mismatch")
        if expectation != truth:
            errors.append(f"{name}: independent Horvitz-Thompson expectation not equal to truth")

    event = cases.get("event_dependent", {})
    null = cases.get("label_independent_null", {})
    if event.get("full_prevalence") == event.get("delivered_prevalence"):
        errors.append("event_dependent: delivered-only bias was not demonstrated")
    null_units = null.get("units")
    if isinstance(null_units, list) and all(isinstance(row, dict) for row in null_units):
        if null_units and len({row.get("inclusion_probability") for row in null_units}) != 1:
            errors.append("label_independent_null: audit probability depends on label")

    transient = cases.get("uncaptured_transient")
    if not isinstance(transient, dict):
        errors.append("uncaptured_transient: missing case")
    else:
        if transient.get("status") != "OUT_OF_FRAME_NOT_ESTIMABLE":
            errors.append("uncaptured_transient: out-of-frame refusal missing")
        if "ht_expected_prevalence" in transient or "estimate" in transient:
            errors.append("uncaptured_transient: unsupported numerical recovery claim")
        if transient.get("frame_size") != 8 or transient.get("out_of_frame_event_count") != 1:
            errors.append("uncaptured_transient: frame boundary mismatch")
        if transient.get("out_of_frame_event") != {"source_id": "transient-between-captures", "label": 1}:
            errors.append("uncaptured_transient: transient identity mismatch")
        if transient.get("reasons") != ["event_not_in_capture_grid"]:
            errors.append("uncaptured_transient: refusal reason mismatch")
    return errors


def _corruption_controls(raw):
    mutations = {
        "source_id": lambda value: value["cases"]["event_dependent"]["units"][0].__setitem__("source_id", "forged"),
        "semantic_label": lambda value: value["cases"]["event_dependent"]["units"][0].__setitem__("label", 0),
        "inclusion_probability": lambda value: value["cases"]["event_dependent"]["units"][0].__setitem__("inclusion_probability", "1"),
        "gate_decision": lambda value: value["cases"]["event_dependent"]["units"][0].__setitem__("gate_decision", "delivered"),
        "draw_probability": lambda value: value["cases"]["event_dependent"]["draws"][0].__setitem__("design_probability", "0"),
        "ht_value": lambda value: value["cases"]["event_dependent"]["draws"][0].__setitem__("ht_prevalence", "999"),
        "missing_draw": lambda value: value["cases"]["event_dependent"]["draws"].pop(),
    }
    return {
        name: bool(_core((lambda altered: (mutation(altered), altered)[1])(deepcopy(raw))))
        for name, mutation in mutations.items()
    }


def audit(raw):
    errors = _core(raw)
    controls = _corruption_controls(raw) if not errors else {}
    if controls and not all(controls.values()):
        errors.append("one or more independent corruption controls were not rejected")
    return {
        "status": "PASS" if not errors and len(controls) == 7 else "FAIL",
        "errors": errors,
        "corruption_controls_passed": sum(controls.values()),
        "corruption_controls": controls,
        "auditor": "independent-raw-only-t1-v1",
    }


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        print(json.dumps(audit(json.load(stream)), sort_keys=True, separators=(",", ":")))
