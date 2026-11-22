"""Build the public exact-enumeration input and separate auditor-only truth."""

from __future__ import annotations

import itertools
import json
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STRATA = ["A", "A", "B", "B"]
P = {"A": Fraction(1, 4), "B": Fraction(3, 4)}
Q = {"A": Fraction(1, 2), "B": Fraction(1, 1)}


def enc(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def build() -> tuple[dict, dict]:
    public_cases = []
    oracle_cases = []
    case_no = 0
    for errors in itertools.product((0, 1), repeat=4):
        p_weight = Fraction(1)
        for stratum, error in zip(STRATA, errors):
            p_weight *= P[stratum] if error else 1 - P[stratum]
        for resolved_a in itertools.product((0, 1), repeat=2):
            resolved = [*resolved_a, 1, 1]
            q_weight = Fraction(1)
            for index, stratum in enumerate(STRATA[:2]):
                q_weight *= Q[stratum] if resolved[index] else 1 - Q[stratum]
            weight = p_weight * q_weight
            case_id = f"state_{case_no:02d}"
            rows = []
            for index, (stratum, error, is_resolved) in enumerate(
                zip(STRATA, errors, resolved)
            ):
                row = {
                    "row_id": f"u{index}",
                    "stratum": stratum,
                    "status": "RESOLVED" if is_resolved else "UNRESOLVED",
                }
                if is_resolved:
                    row["error"] = error
                rows.append(row)
            public_cases.append(
                {
                    "case_id": case_id,
                    "population_size": 4,
                    "rows": rows,
                    "censor_model": {
                        "declared": "KNOWN_INDEPENDENT_WITHIN_STRATUM",
                        "resolution_probability": {key: enc(value) for key, value in Q.items()},
                    },
                }
            )
            oracle_cases.append(
                {
                    "case_id": case_id,
                    "latent_errors": list(errors),
                    "resolved": resolved,
                    "probability_weight": enc(weight),
                }
            )
            case_no += 1

    zero_support = {
        "case_id": "zero_support",
        "population_size": 2,
        "rows": [
            {"row_id": "zA", "stratum": "A", "status": "UNRESOLVED"},
            {"row_id": "zB", "stratum": "B", "status": "RESOLVED", "error": 0},
        ],
        "censor_model": {
            "declared": "KNOWN_INDEPENDENT_WITHIN_STRATUM",
            "resolution_probability": {"A": "0/1", "B": "1/1"},
        },
    }
    public = {
        "schema": "unjuno.issue7993.ipcw_public.v1",
        "ipcw_cases": public_cases,
        "zero_support_case": zero_support,
    }
    truth = {
        "schema": "unjuno.issue7993.ipcw_audit_truth.v1",
        "design": {
            "strata": STRATA,
            "error_probability": {key: enc(value) for key, value in P.items()},
            "true_expected_risk": "1/2",
            "independent_resolution_given_stratum": True,
        },
        "ipcw_cases": oracle_cases,
        "zero_support_truth": {"latent_errors": [1, 0]},
    }
    return public, truth


def write() -> None:
    public, truth = build()
    (ROOT / "public_input.json").write_text(
        json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / "auditor_truth.json").write_text(
        json.dumps(truth, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    write()
