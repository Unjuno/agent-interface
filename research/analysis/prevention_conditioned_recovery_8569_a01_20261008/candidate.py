#!/usr/bin/env python3
"""Candidate exact estimator for the frozen synthetic #8569 fixture."""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path


def f(value):
    return Fraction(value)


def rational(value):
    return f"{value.numerator}/{value.denominator}"


def metrics(mix, prevention, recovery):
    fail_mass = {regime: mix[regime] * (1 - prevention[regime]) for regime in mix}
    demand_total = sum(fail_mass.values(), Fraction(0))
    demand_mix = {regime: fail_mass[regime] / demand_total for regime in mix}
    marginal = {
        strategy: sum((mix[r] * recovery[strategy][r] for r in mix), Fraction(0))
        for strategy in recovery
    }
    conditional = {
        strategy: sum((demand_mix[r] * recovery[strategy][r] for r in mix), Fraction(0))
        for strategy in recovery
    }
    prevention_mass = sum((mix[r] * prevention[r] for r in mix), Fraction(0))
    joint = {s: prevention_mass + demand_total * conditional[s] for s in recovery}
    naive = {s: prevention_mass + demand_total * marginal[s] for s in recovery}
    return {
        "prevention_success_mass": rational(prevention_mass),
        "recovery_demand_mass": rational(demand_total),
        "recovery_demand_mix": {r: rational(v) for r, v in demand_mix.items()},
        "recovery_unconditional": {s: rational(v) for s, v in marginal.items()},
        "recovery_conditional": {s: rational(v) for s, v in conditional.items()},
        "joint_system_outcome": {s: rational(v) for s, v in joint.items()},
        "naive_joint_using_unconditional_recovery": {s: rational(v) for s, v in naive.items()},
    }


def calculate(fixture, fixture_bytes):
    mix = {r: f(v) for r, v in fixture["initial_mix"].items()}
    primary = metrics(
        mix,
        {r: f(v) for r, v in fixture["prevention_success"].items()},
        {s: {r: f(v) for r, v in rows.items()} for s, rows in fixture["recovery_success"].items()},
    )
    controls = {}
    for name, control in fixture["controls"].items():
        controls[name] = metrics(
            mix,
            {r: f(v) for r, v in control["prevention_success"].items()},
            {s: {r: f(v) for r, v in rows.items()} for s, rows in control["recovery_success"].items()},
        )
    return {
        "schema": "issue-8569-candidate-v1",
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "safe_stop_treatment": fixture["safe_stop_outcome"],
        "primary": primary,
        "controls": controls,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="trace_fixture.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture_bytes = Path(args.fixture).read_bytes()
    result = calculate(json.loads(fixture_bytes), fixture_bytes)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
