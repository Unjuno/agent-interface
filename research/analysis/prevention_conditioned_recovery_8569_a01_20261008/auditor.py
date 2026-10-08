#!/usr/bin/env python3
"""Independent exact-rational oracle for the frozen #8569 candidate output."""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path


def q(text):
    return Fraction(text)


def s(value):
    return f"{value.numerator}/{value.denominator}"


def reconstruct(mix_text, prevention_text, recovery_text):
    initial = {name: q(value) for name, value in mix_text.items()}
    prevented = {name: q(value) for name, value in prevention_text.items()}
    recovered = {strategy: {name: q(value) for name, value in row.items()} for strategy, row in recovery_text.items()}

    surviving_demand = {name: initial[name] - initial[name] * prevented[name] for name in initial}
    total_demand = sum(surviving_demand.values(), q("0"))
    conditional_population = {name: surviving_demand[name] / total_demand for name in initial}
    unconditional_rates = {
        strategy: sum((initial[name] * recovered[strategy][name] for name in initial), q("0"))
        for strategy in recovered
    }
    conditional_rates = {
        strategy: sum((conditional_population[name] * recovered[strategy][name] for name in initial), q("0"))
        for strategy in recovered
    }
    prevention_total = sum((initial[name] * prevented[name] for name in initial), q("0"))
    composed = {strategy: prevention_total + total_demand * conditional_rates[strategy] for strategy in recovered}
    mislabeled = {strategy: prevention_total + total_demand * unconditional_rates[strategy] for strategy in recovered}

    return {
        "prevention_success_mass": s(prevention_total),
        "recovery_demand_mass": s(total_demand),
        "recovery_demand_mix": {name: s(value) for name, value in conditional_population.items()},
        "recovery_unconditional": {name: s(value) for name, value in unconditional_rates.items()},
        "recovery_conditional": {name: s(value) for name, value in conditional_rates.items()},
        "joint_system_outcome": {name: s(value) for name, value in composed.items()},
        "naive_joint_using_unconditional_recovery": {name: s(value) for name, value in mislabeled.items()},
    }


def expected(fixture, fixture_bytes):
    mix = fixture["initial_mix"]
    result = {
        "schema": "issue-8569-candidate-v1",
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "safe_stop_treatment": "not-modeled",
        "primary": reconstruct(mix, fixture["prevention_success"], fixture["recovery_success"]),
        "controls": {},
    }
    for name, values in fixture["controls"].items():
        result["controls"][name] = reconstruct(mix, values["prevention_success"], values["recovery_success"])
    return result


def audit(candidate, fixture, fixture_bytes):
    want = expected(fixture, fixture_bytes)
    errors = []
    if candidate != want:
        errors.append("candidate_payload_differs_from_independent_exact_reconstruction")
    primary = candidate.get("primary", {})
    if primary.get("recovery_conditional", {}).get("A") == primary.get("recovery_conditional", {}).get("B"):
        errors.append("primary_conditional_strategies_not_ranked")
    if primary.get("recovery_unconditional", {}).get("A") == primary.get("recovery_unconditional", {}).get("B"):
        errors.append("primary_unconditional_strategies_not_ranked")
    if candidate.get("safe_stop_treatment") != "not-modeled":
        errors.append("safe_stop_outcome_was_fabricated")
    if not errors:
        p = candidate["primary"]
        if not (q(p["recovery_unconditional"]["A"]) > q(p["recovery_unconditional"]["B"])):
            errors.append("primary_unconditional_rank_not_A_over_B")
        if not (q(p["recovery_conditional"]["A"]) < q(p["recovery_conditional"]["B"])):
            errors.append("primary_conditional_rank_not_B_over_A")
        for name in ("A", "B"):
            if q(p["joint_system_outcome"][name]) == q(p["naive_joint_using_unconditional_recovery"][name]):
                errors.append(f"{name}_naive_joint_did_not_differ")
        control = candidate["controls"]["no_selection"]
        if control["recovery_demand_mix"] != fixture["initial_mix"]:
            errors.append("no_selection_control_mix_changed")
        if control["recovery_conditional"] != control["recovery_unconditional"]:
            errors.append("no_selection_control_rate_changed")
        stable = candidate["controls"]["equal_sensitivity"]
        if not (
            q(stable["recovery_unconditional"]["A"]) > q(stable["recovery_unconditional"]["B"])
            and q(stable["recovery_conditional"]["A"]) > q(stable["recovery_conditional"]["B"])
        ):
            errors.append("equal_sensitivity_control_rank_changed")
    return errors


def mutation_checks(candidate, fixture, fixture_bytes):
    variants = {}

    swap = json.loads(json.dumps(candidate))
    swap["primary"]["recovery_conditional"], swap["primary"]["recovery_unconditional"] = (
        swap["primary"]["recovery_unconditional"], swap["primary"]["recovery_conditional"]
    )
    variants["swap_conditional_unconditional"] = swap

    drop = json.loads(json.dumps(candidate))
    drop["primary"]["recovery_demand_mix"].pop("hard", None)
    variants["drop_hard_regime"] = drop

    reset = json.loads(json.dumps(candidate))
    reset["primary"]["recovery_demand_mix"] = fixture["initial_mix"]
    variants["reset_demand_to_initial_mix"] = reset

    stop = json.loads(json.dumps(candidate))
    stop["safe_stop_treatment"] = "success"
    variants["count_safe_stop_as_success"] = stop

    return {name: audit(variant, fixture, fixture_bytes) != [] for name, variant in variants.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--fixture", default="trace_fixture.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture_bytes = Path(args.fixture).read_bytes()
    fixture = json.loads(fixture_bytes)
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    errors = audit(candidate, fixture, fixture_bytes)
    mutations = mutation_checks(candidate, fixture, fixture_bytes)
    body = {
        "schema": "issue-8569-auditor-v1",
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(Path(args.candidate).read_bytes()).hexdigest(),
        "disposition": "PASS_METHOD_SCOPED" if not errors and all(mutations.values()) else "HOLD_FIXTURE_OR_ORACLE",
        "reconstruction_errors": errors,
        "mutation_controls_rejected": mutations,
        "all_mutations_rejected": bool(mutations) and all(mutations.values()),
    }
    Path(args.output).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
