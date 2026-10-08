#!/usr/bin/env python3
"""Issue #8654 C03 independent raw-only auditor. Never imports candidate.py."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

N = 16
Q = 0.25
TRUTH = {
    "STABLE": {"cue": 1.0, "alternative": 0.0},
    "REVERSAL": {"cue": 0.0, "alternative": 1.0},
    "GLOBAL_SHIFT": {"cue": 0.0, "alternative": -1.0},
}
REGIME_NAMES = tuple(TRUTH)

def independent_binomial_mass(k):
    return math.comb(N, k) * (Q ** k) * ((1.0 - Q) ** (N - k))

def expected_diagnostic(regime, k0, k1):
    truth = TRUTH[regime]
    cue_count = (N - k0) + (N - k1)
    alternative_count = k0 + k1
    cue_sum = cue_count * truth["cue"]
    alternative_sum = alternative_count * truth["alternative"]
    cue_mean = cue_sum / ((1.0 - Q) * (2 * N))
    alternative_mean = alternative_sum / (Q * (2 * N))
    difference = cue_mean - alternative_mean
    support = all(0 < k < N for k in (k0, k1))
    if not support:
        label = "UNIDENTIFIABLE"
    elif difference < 0:
        label = "REVERSAL"
    elif cue_mean > 0.5:
        label = "STABLE"
    else:
        label = "GLOBAL_SHIFT"
    return {
        "arm": "DIAGNOSTIC",
        "regime": regime,
        "k0_alt": k0,
        "k1_alt": k1,
        "probability": independent_binomial_mass(k0) * independent_binomial_mass(k1),
        "cue_count": cue_count,
        "alternative_count": alternative_count,
        "cue_reward_sum": cue_sum,
        "alternative_reward_sum": alternative_sum,
        "complete_support": support,
        "cue_mean_ht": cue_mean,
        "alternative_mean_ht": alternative_mean,
        "contrast_ht": difference,
        "decision": label,
    }

def expected_greedy(regime):
    cue_total = 2 * N * TRUTH[regime]["cue"]
    return {
        "arm": "GREEDY_CUE_ONLY",
        "regime": regime,
        "k0_alt": 0,
        "k1_alt": 0,
        "probability": 1.0,
        "cue_count": 2 * N,
        "alternative_count": 0,
        "cue_reward_sum": cue_total,
        "alternative_reward_sum": 0.0,
        "complete_support": False,
        "cue_mean_ht": None,
        "alternative_mean_ht": None,
        "contrast_ht": None,
        "decision": "UNIDENTIFIABLE",
    }

def same_number(actual, wanted):
    return (
        type(actual) in (int, float)
        and math.isfinite(actual)
        and math.isclose(actual, wanted, rel_tol=0.0, abs_tol=1e-14)
    )

def matches(row, expected):
    if not isinstance(row, dict) or set(row) != set(expected):
        return False
    for key, wanted in expected.items():
        actual = row.get(key)
        if wanted is None:
            if actual is not None:
                return False
        elif isinstance(wanted, float):
            if not same_number(actual, wanted):
                return False
        elif type(actual) is not type(wanted) or actual != wanted:
            return False
    return True

def expected_for_key(key):
    arm, regime, k0, k1 = key
    if regime not in TRUTH:
        return None
    if arm == "DIAGNOSTIC":
        if type(k0) is not int or type(k1) is not int or not (0 <= k0 <= N and 0 <= k1 <= N):
            return None
        return expected_diagnostic(regime, k0, k1)
    if arm == "GREEDY_CUE_ONLY" and type(k0) is int and type(k1) is int and k0 == 0 and k1 == 0:
        return expected_greedy(regime)
    return None

def parse_raw(path):
    parsed = []
    with path.open("r", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.endswith("\n"):
                raise ValueError(f"line {number} lacks final newline")
            parsed.append(json.loads(line))
    return parsed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    errors = []
    try:
        rows = parse_raw(args.raw)
    except Exception as exc:
        rows = []
        errors.append(f"raw parse failed: {type(exc).__name__}: {exc}")

    keys = []
    for row in rows:
        if not isinstance(row, dict):
            keys.append(("INVALID", "INVALID", None, None))
        else:
            keys.append((row.get("arm"), row.get("regime"), row.get("k0_alt"), row.get("k1_alt")))
    expected_keys = {
        ("DIAGNOSTIC", regime, k0, k1)
        for regime in REGIME_NAMES
        for k0, k1 in itertools.product(range(N + 1), repeat=2)
    }
    expected_keys |= {("GREEDY_CUE_ONLY", regime, 0, 0) for regime in REGIME_NAMES}
    if len(rows) != 870 or len(set(keys)) != 870 or set(keys) != expected_keys:
        errors.append("row identity/cardinality mismatch")

    probability_mass = {}
    supported_mass = {}
    correct_mass = {}
    error_mass = {}
    supported_accuracy = {}
    stable_error_rows = 0
    stable_error_mass = 0.0
    for regime in REGIME_NAMES:
        diagnostic = [
            row for row in rows
            if isinstance(row, dict) and row.get("arm") == "DIAGNOSTIC" and row.get("regime") == regime
        ]
        probability_mass[regime] = math.fsum(
            row["probability"] for row in diagnostic
            if type(row.get("probability")) in (int, float) and math.isfinite(row["probability"])
        )
        if abs(probability_mass[regime] - 1.0) > 1e-12:
            errors.append(f"diagnostic probability mass mismatch: {regime}")
        mass_supported = math.fsum(
            row["probability"] for row in diagnostic
            if row.get("complete_support") is True and type(row.get("probability")) in (int, float)
        )
        mass_correct = math.fsum(
            row["probability"] for row in diagnostic
            if row.get("decision") == regime and type(row.get("probability")) in (int, float)
        )
        mass_error = math.fsum(
            row["probability"] for row in diagnostic
            if row.get("complete_support") is True and row.get("decision") != regime
            and type(row.get("probability")) in (int, float)
        )
        supported_mass[regime] = mass_supported
        correct_mass[regime] = mass_correct
        error_mass[regime] = mass_error
        supported_accuracy[regime] = (mass_correct / mass_supported) if mass_supported else None
        if regime == "STABLE":
            wrong = [
                row for row in diagnostic
                if row.get("complete_support") is True and row.get("decision") != "STABLE"
            ]
            stable_error_rows = len(wrong)
            stable_error_mass = math.fsum(
                row["probability"] for row in wrong
                if type(row.get("probability")) in (int, float)
            )

    for row in rows:
        if not isinstance(row, dict):
            continue
        key = (row.get("arm"), row.get("regime"), row.get("k0_alt"), row.get("k1_alt"))
        expected = expected_for_key(key)
        if expected is None or not matches(row, expected):
            errors.append(f"raw reconstruction mismatch: {key}")

    mutations = [
        lambda row: {**row, "probability": row["probability"] + 0.01},
        lambda row: {**row, "complete_support": not row["complete_support"]},
        lambda row: {**row, "cue_mean_ht": row["cue_mean_ht"] + 1.0},
        lambda row: {**row, "decision": "STABLE" if row["decision"] != "STABLE" else "REVERSAL"},
        lambda row: {**row, "arm": "GREEDY_CUE_ONLY"},
    ]
    probe = next(
        (row for row in rows if isinstance(row, dict) and row.get("arm") == "DIAGNOSTIC"
         and row.get("regime") == "STABLE" and row.get("k0_alt") == 9 and row.get("k1_alt") == 11),
        {},
    )
    rejected = sum(not matches(mutator(probe), expected_diagnostic("STABLE", 9, 11)) for mutator in mutations)
    if rejected != len(mutations):
        errors.append(f"mutation controls rejected {rejected}/{len(mutations)}")

    study_outcome = (
        "COUNTEREXAMPLE_TO_SUPPORT_SUFFICIENCY_SCOPED"
        if stable_error_mass > 0.0
        else "NO_COUNTEREXAMPLE_AT_DECLARED_GRID"
    )
    result = {
        "allocation": "8654-C03",
        "integrity_status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "study_outcome": study_outcome if not errors else None,
        "rows": len(rows),
        "diagnostic_rows_per_regime": 289,
        "greedy_rows": sum(
            1 for row in rows if isinstance(row, dict) and row.get("arm") == "GREEDY_CUE_ONLY"
        ),
        "probability_mass": probability_mass,
        "complete_support_probability_mass": supported_mass,
        "correct_probability_mass": correct_mass,
        "supported_error_probability_mass": error_mass,
        "accuracy_conditional_on_complete_support": supported_accuracy,
        "stable_supported_error_rows": stable_error_rows,
        "stable_supported_error_probability_mass": stable_error_mass,
        "mutations_rejected": rejected,
        "mutations_total": len(mutations),
        "errors": errors,
        "scope": "exact deterministic finite-sample method probe only",
        "raw_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest() if args.raw.exists() else None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)

if __name__ == "__main__":
    main()
