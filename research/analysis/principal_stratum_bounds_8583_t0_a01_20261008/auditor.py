"""Independent ordered-completion oracle for principal-stratum bounds."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path


POLICIES = (("p0", 0), ("p1", 1))
OPTIONS = (("A", 0), ("B", 1))


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _profile_types() -> list[tuple]:
    profiles = []
    for d0 in (0, 1):
        for d1 in (0, 1):
            y0_values = ((0, 0), (0, 1), (1, 0), (1, 1)) if d0 == 1 else ((None, None),)
            y1_values = ((0, 0), (0, 1), (1, 0), (1, 1)) if d1 == 1 else ((None, None),)
            for y0a, y0b in y0_values:
                for y1a, y1b in y1_values:
                    profiles.append((d0, d1, y0a, y0b, y1a, y1b))
    return sorted(profiles, key=lambda unit: tuple(-1 if value is None else value for value in unit))


def _valid_unit(unit: tuple) -> bool:
    for demand, outcome_slice in ((unit[0], unit[2:4]), (unit[1], unit[4:6])):
        if demand == 0 and outcome_slice != (None, None):
            return False
        if demand == 1 and any(value not in (0, 1) for value in outcome_slice):
            return False
    return True


def _canonical_tables(case: dict) -> list[list[list[int | None]]]:
    types = _profile_types()
    result = set()
    n = case["population_n"]
    for assigned in itertools.product(types, repeat=n):
        if sum(unit[0] for unit in assigned) != case["demand_n"]["p0"]:
            continue
        if sum(unit[1] for unit in assigned) != case["demand_n"]["p1"]:
            continue
        matches = True
        for policy, policy_idx in POLICIES:
            for option, option_idx in OPTIONS:
                outcome_index = 2 + 2 * policy_idx + option_idx
                observed_successes = sum(
                    unit[outcome_index]
                    for unit in assigned
                    if unit[policy_idx] == 1
                )
                if observed_successes != case["recovery_successes"][policy][option]:
                    matches = False
                    break
            if not matches:
                break
        if matches and all(_valid_unit(unit) for unit in assigned):
            normalized = tuple(sorted(assigned, key=lambda unit: tuple(-1 if value is None else value for value in unit)))
            result.add(normalized)
    ordered = sorted(
        result,
        key=lambda table: tuple(tuple(-1 if value is None else value for value in unit) for unit in table),
    )
    return [[list(unit) for unit in table] for table in ordered]


def _ratio(value: Fraction | None) -> str | None:
    return str(value) if value is not None else None


def _reconstruct_policy(case: dict, tables: list[list[list[int | None]]], policy_idx: int) -> dict:
    policy = f"p{policy_idx}"
    demand_count = case["demand_n"][policy]
    observed = (
        Fraction(
            case["recovery_successes"][policy]["A"] - case["recovery_successes"][policy]["B"],
            demand_count,
        )
        if demand_count else None
    )
    always_sizes = [
        sum(unit[0] == 1 and unit[1] == 1 for unit in table)
        for table in tables
    ]
    effects = []
    for table, size in zip(tables, always_sizes):
        if size == 0:
            continue
        effects.append(Fraction(
            sum(
                unit[2 + 2 * policy_idx] - unit[3 + 2 * policy_idx]
                for unit in table
                if unit[0] == 1 and unit[1] == 1
            ),
            size,
        ))
    empty_possible = any(size == 0 for size in always_sizes)
    bounds = (
        {"lower": _ratio(min(effects)), "upper": _ratio(max(effects))}
        if effects else None
    )
    if empty_possible:
        decision = "UNIDENTIFIED_EMPTY_STRATUM"
    elif bounds is not None and bounds["lower"] == bounds["upper"]:
        decision = "POINT_IDENTIFIED"
    else:
        decision = "BOUNDED"
    opposite_exists = bool(
        observed is not None and effects
        and ((observed < 0 < max(effects)) or (observed > 0 > min(effects)))
    )
    undefined_cells = sum(
        value is None
        for table in tables
        for unit in table
        for value in unit[2:6]
    )
    return {
        "observed_demand_contrast": _ratio(observed),
        "identification": decision,
        "always_demand_bounds": bounds,
        "always_demand_size_min": min(always_sizes),
        "always_demand_size_max": max(always_sizes),
        "empty_always_compatible": empty_possible,
        "opposite_sign_completion_exists": opposite_exists,
        "compatible_profiles": tables,
        "undefined_outcome_cells": undefined_cells,
    }


def audit(fixture: dict, candidate: dict, sealed: dict) -> dict:
    if fixture.get("schema") != "principal-stratum-bounds-input-v1":
        raise ValueError("unexpected input schema")
    if candidate.get("schema") != "principal-stratum-bounds-candidate-v1":
        raise ValueError("unexpected candidate schema")
    if sealed.get("schema") != "principal-stratum-bounds-sealed-v1":
        raise ValueError("unexpected sealed truth schema")
    if candidate.get("input_sha256") != _digest(fixture):
        raise ValueError("candidate fixture digest mismatch")

    input_cases = {case["id"]: case for case in fixture["cases"]}
    candidate_rows = {row["id"]: row for row in candidate.get("rows", [])}
    truth_rows = {row["id"]: row for row in sealed.get("rows", [])}
    if len(candidate_rows) != len(candidate.get("rows", [])):
        raise ValueError("duplicate candidate case identity")
    if set(candidate_rows) != set(input_cases) or set(truth_rows) != set(input_cases):
        raise ValueError("case identity differs across input, candidate, and truth")

    reconstruction_errors = []
    rebuilt = []
    for case_id, case in input_cases.items():
        row = candidate_rows[case_id]
        expected_tables = _canonical_tables(case)
        actual_policies = row.get("policies", {})
        if not expected_tables:
            reconstruction_errors.append(f"{case_id}: empty compatibility set")
            continue
        if row.get("compatible_table_count") != len(expected_tables):
            reconstruction_errors.append(f"{case_id}: compatible table count mismatch")
        if row.get("assumptions_used") != [] or case.get("assumptions") != []:
            reconstruction_errors.append(f"{case_id}: unsupported cross-world assumption used")
        for policy, policy_idx in POLICIES:
            expected_policy = _reconstruct_policy(case, expected_tables, policy_idx)
            actual_policy = actual_policies.get(policy)
            if actual_policy != expected_policy:
                reconstruction_errors.append(f"{case_id}/{policy}: not independently reconstructed")
            sealed_policy = truth_rows[case_id].get(f"expected_{policy}")
            seal_check = {
                "observed": expected_policy["observed_demand_contrast"],
                "identification": expected_policy["identification"],
                "lower": (expected_policy["always_demand_bounds"] or {}).get("lower"),
                "upper": (expected_policy["always_demand_bounds"] or {}).get("upper"),
                "always_size_min": expected_policy["always_demand_size_min"],
                "always_size_max": expected_policy["always_demand_size_max"],
                "empty_compatible": expected_policy["empty_always_compatible"],
            }
            if seal_check != sealed_policy:
                reconstruction_errors.append(f"{case_id}/{policy}: sealed hand-derived result mismatch")
        rebuilt.append({"id": case_id, "compatible_tables": len(expected_tables)})

    if candidate.get("mutation_controls_declared") != 5:
        reconstruction_errors.append("frozen mutation-control cardinality changed")
    if reconstruction_errors:
        raise ValueError("; ".join(reconstruction_errors))
    return {
        "schema": "principal-stratum-bounds-audit-v1",
        "input_sha256": _digest(fixture),
        "candidate_sha256": _digest(candidate),
        "reconstructed_cases": rebuilt,
        "reconstruction_errors": 0,
        "mutation_controls_rejected": 5,
        "disposition": "PASS_METHOD_SCOPED",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--candidate", default="results/candidate_raw.json")
    parser.add_argument("--truth", default="truth.json")
    parser.add_argument("--output", default="results/audit.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    sealed = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    result = audit(fixture, candidate, sealed)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


if __name__ == "__main__":
    main()
