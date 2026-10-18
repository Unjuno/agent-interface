"""Exhaustive finite compatibility enumerator for binary principal strata."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path


POLICIES = ("p0", "p1")
OPTIONS = ("A", "B")


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _unit_types() -> list[tuple[int, int, int | None, int | None, int | None, int | None]]:
    result = []
    for d0, d1 in itertools.product((0, 1), repeat=2):
        y0_pairs = list(itertools.product((0, 1), repeat=2)) if d0 else [(None, None)]
        y1_pairs = list(itertools.product((0, 1), repeat=2)) if d1 else [(None, None)]
        for y0a, y0b in y0_pairs:
            for y1a, y1b in y1_pairs:
                result.append((d0, d1, y0a, y0b, y1a, y1b))
    return sorted(result, key=lambda row: tuple(-1 if value is None else value for value in row))


def _matches(profile: tuple, case: dict) -> bool:
    if sum(unit[0] for unit in profile) != case["demand_n"]["p0"]:
        return False
    if sum(unit[1] for unit in profile) != case["demand_n"]["p1"]:
        return False
    for pidx, policy in enumerate(POLICIES):
        for oidx, option in enumerate(OPTIONS):
            outcome_idx = 2 + pidx * 2 + oidx
            total = sum(unit[outcome_idx] or 0 for unit in profile)
            if total != case["recovery_successes"][policy][option]:
                return False
    return True


def _fraction(numerator: int, denominator: int) -> str:
    return str(Fraction(numerator, denominator))


def _policy_result(case: dict, compatible: list[tuple], policy_idx: int) -> dict:
    policy = POLICIES[policy_idx]
    demand_n = case["demand_n"][policy]
    observed = (
        _fraction(case["recovery_successes"][policy]["A"] - case["recovery_successes"][policy]["B"], demand_n)
        if demand_n else None
    )
    always_profiles = [
        profile for profile in compatible
        if sum(unit[0] == 1 and unit[1] == 1 for unit in profile) > 0
    ]
    empty_compatible = any(
        not any(unit[0] == 1 and unit[1] == 1 for unit in profile)
        for profile in compatible
    )
    sizes = [
        sum(unit[0] == 1 and unit[1] == 1 for unit in profile)
        for profile in compatible
    ]
    effects = []
    for profile in always_profiles:
        members = [unit for unit in profile if unit[0] == 1 and unit[1] == 1]
        effects.append(Fraction(sum(unit[2 + policy_idx * 2] - unit[3 + policy_idx * 2] for unit in members), len(members)))

    bounds = (
        {"lower": str(min(effects)), "upper": str(max(effects))}
        if effects else None
    )
    if empty_compatible:
        identification = "UNIDENTIFIED_EMPTY_STRATUM"
    elif bounds is not None and bounds["lower"] == bounds["upper"]:
        identification = "POINT_IDENTIFIED"
    else:
        identification = "BOUNDED"

    opposite = bool(
        observed is not None and effects
        and ((Fraction(observed) < 0 < max(effects))
             or (Fraction(observed) > 0 > min(effects)))
    )
    serialized_profiles = [list(map(list, profile)) for profile in compatible]
    undefined = sum(
        value is None
        for profile in compatible
        for unit in profile
        for value in unit[2:]
    )
    return {
        "observed_demand_contrast": observed,
        "identification": identification,
        "always_demand_bounds": bounds,
        "always_demand_size_min": min(sizes),
        "always_demand_size_max": max(sizes),
        "empty_always_compatible": empty_compatible,
        "opposite_sign_completion_exists": opposite,
        "compatible_profiles": serialized_profiles,
        "undefined_outcome_cells": undefined,
    }


def run(fixture: dict) -> dict:
    if fixture.get("schema") != "principal-stratum-bounds-input-v1":
        raise ValueError("unexpected input schema")
    rows = []
    types = _unit_types()
    for case in fixture["cases"]:
        n = case["population_n"]
        if not 0 <= case["demand_n"]["p0"] <= n or not 0 <= case["demand_n"]["p1"] <= n:
            raise ValueError("demand margins outside population")
        if case.get("assumptions") != []:
            raise ValueError("the frozen allocation uses no cross-world assumptions")
        for p in POLICIES:
            for option in OPTIONS:
                success = case["recovery_successes"][p][option]
                if not 0 <= success <= case["demand_n"][p]:
                    raise ValueError("recovery successes outside demand denominator")
        compatible = [
            profile for profile in itertools.combinations_with_replacement(types, n)
            if _matches(profile, case)
        ]
        if not compatible:
            raise ValueError(f"{case['id']}: no compatible latent table")
        rows.append({
            "id": case["id"],
            "assumptions_used": [],
            "compatible_table_count": len(compatible),
            "policies": {
                p: _policy_result(case, compatible, index)
                for index, p in enumerate(POLICIES)
            },
        })
    return {
        "schema": "principal-stratum-bounds-candidate-v1",
        "input_sha256": _digest(fixture),
        "mutation_controls_declared": 5,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--output", default="results/candidate_raw.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(run(fixture), stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


if __name__ == "__main__":
    main()
