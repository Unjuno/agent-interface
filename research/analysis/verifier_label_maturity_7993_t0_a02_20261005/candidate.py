"""Candidate IPCW estimator; reads public rows only, never auditor truth."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path


ESTIMAND = "SUPERPOPULATION_EXPECTED_ERROR_RISK"


def enc(value: Fraction | None) -> str | None:
    if value is None:
        return None
    return f"{value.numerator}/{value.denominator}"


def estimate_case(case: dict) -> dict:
    n = case["population_size"]
    rows = case["rows"]
    model = case["censor_model"]
    q = {name: Fraction(value) for name, value in model["resolution_probability"].items()}
    if model["declared"] != "KNOWN_INDEPENDENT_WITHIN_STRATUM":
        status, estimate = "UNKNOWN_UNSUPPORTED_CENSORING_MODEL", None
    elif any(value == 0 for value in q.values()):
        status, estimate = "UNKNOWN_NONPOSITIVITY", None
    elif any(value < 0 or value > 1 for value in q.values()):
        status, estimate = "UNKNOWN_INVALID_RESOLUTION_PROBABILITY", None
    else:
        observed_weighted_errors = sum(
            (Fraction(row["error"], 1) / q[row["stratum"]])
            for row in rows
            if row["status"] == "RESOLVED"
        )
        status = "ASSUMPTION_CONDITIONAL_ESTIMATE"
        estimate = observed_weighted_errors / n
    return {
        "case_id": case["case_id"],
        "status": status,
        "estimand": ESTIMAND,
        "estimate": enc(estimate),
        "finite_cohort_point_claim": None,
    }


def calculate(public: dict) -> dict:
    regular = [estimate_case(case) for case in public["ipcw_cases"]]
    zero = estimate_case(public["zero_support_case"])
    return {
        "schema": "unjuno.issue7993.ipcw_candidate.v1",
        "cases": regular,
        "zero_support": zero,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    public = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = calculate(public)
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
