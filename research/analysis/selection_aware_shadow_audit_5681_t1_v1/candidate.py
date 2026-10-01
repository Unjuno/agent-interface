"""Exhaustively enumerate the preregistered finite Bernoulli designs."""

from fractions import Fraction
import itertools
import json


def _fraction(value):
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _enumerate_case(rows):
    randomized = [row for row in rows if Fraction(row["inclusion_probability"]) < 1]
    draws = []
    n = len(rows)
    truth = Fraction(sum(row["label"] for row in rows), n)
    for bits in itertools.product((False, True), repeat=len(randomized)):
        selected = {row["source_id"] for row in rows if Fraction(row["inclusion_probability"]) == 1}
        probability = Fraction(1)
        for row, included in zip(randomized, bits):
            pi = Fraction(row["inclusion_probability"])
            probability *= pi if included else 1 - pi
            if included:
                selected.add(row["source_id"])
        estimate_total = sum((
            Fraction(row["label"], 1) / Fraction(row["inclusion_probability"])
            for row in rows
            if row["source_id"] in selected
        ), Fraction(0))
        draws.append({
            "selected_ids": sorted(selected),
            "design_probability": _fraction(probability),
            "ht_prevalence": _fraction(estimate_total / n),
        })
    expectation = sum(
        Fraction(draw["design_probability"]) * Fraction(draw["ht_prevalence"])
        for draw in draws
    )
    delivered = [row for row in rows if row["gate_decision"] == "delivered"]
    delivered_prevalence = (
        Fraction(sum(row["label"] for row in delivered), len(delivered))
        if delivered else None
    )
    return {
        "status": "ESTIMABLE",
        "frame_size": n,
        "units": rows,
        "full_prevalence": _fraction(truth),
        "delivered_prevalence": None if delivered_prevalence is None else _fraction(delivered_prevalence),
        "draw_count": len(draws),
        "draws": draws,
        "ht_expected_prevalence": _fraction(expectation),
    }


def _unit(source_id, label, decision, inclusion_probability):
    return {
        "source_id": source_id,
        "label": label,
        "gate_decision": decision,
        "inclusion_probability": inclusion_probability,
    }


def build():
    event_rows = [
        *[_unit(f"event-{index}", 1, "suppressed", "1/2") for index in range(4)],
        *[_unit(f"quiet-{index}", 0, "delivered", "1") for index in range(4)],
    ]
    null_rows = [
        _unit(f"null-{index}", int(index < 4), "delivered", "1/2")
        for index in range(8)
    ]
    zero_rows = [
        *[_unit(f"zero-event-{index}", 1, "suppressed", "0") for index in range(4)],
        *[_unit(f"zero-quiet-{index}", 0, "delivered", "1") for index in range(4)],
    ]
    zero_case = {
        "status": "NOT_ESTIMABLE",
        "frame_size": 8,
        "units": zero_rows,
        "reasons": ["zero_inclusion_target"],
        "draws": [],
        "draw_count": 0,
    }
    transient_case = {
        "status": "OUT_OF_FRAME_NOT_ESTIMABLE",
        "frame_size": 8,
        "out_of_frame_event_count": 1,
        "out_of_frame_event": {"source_id": "transient-between-captures", "label": 1},
        "reasons": ["event_not_in_capture_grid"],
    }
    return {
        "schema": "selection-aware-shadow-audit-t1-v1",
        "design": "independent_bernoulli_exhaustive",
        "cases": {
            "event_dependent": _enumerate_case(event_rows),
            "label_independent_null": _enumerate_case(null_rows),
            "zero_inclusion": zero_case,
            "uncaptured_transient": transient_case,
        },
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True, separators=(",", ":")))
