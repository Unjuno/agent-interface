#!/usr/bin/env python3
"""Independent raw-only auditor; intentionally imports no candidate module."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ALPHA = 0.10
TRIALS = 10_000
SAMPLE_SIZES = (4, 10)
TOLERANCE = 0.015


def threshold(values, rank):
    if rank > len(values):
        return math.inf
    return sorted(values)[rank - 1]


def expected_outcome(q, true_score, false_score, shift_flag=False):
    if shift_flag:
        labels = ["FAIL", "PASS"]
    else:
        labels = []
        if true_score <= q:
            labels.append("PASS")
        if false_score <= q:
            labels.append("FAIL")
    singleton = len(labels) == 1
    return {
        "true_included": "PASS" in labels,
        "singleton": singleton,
        "wrong_singleton": singleton and labels[0] != "PASS",
        "set_size": len(labels),
        "empty": not labels,
    }


def same_number(observed, expected):
    if expected is None:
        return observed is None
    return isinstance(observed, (int, float)) and math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-14)


def row_errors(row):
    errors = []
    n = row.get("n")
    if n not in SAMPLE_SIZES or not isinstance(row.get("trial"), int):
        return ["row_identity"]
    cal_u = row.get("calibration_u")
    if not isinstance(cal_u, list) or len(cal_u) != n or any(not isinstance(x, (int, float)) or not 0 <= x < 1 for x in cal_u):
        return ["calibration_shape"]
    try:
        calibration = [math.sqrt(x) for x in cal_u]
        expected_ranks = {"plugin": math.ceil(n * (1 - ALPHA)), "conformal": math.ceil((n + 1) * (1 - ALPHA))}
        expected_q = {
            "raw": 0.90,
            "plugin": threshold(calibration, expected_ranks["plugin"]),
            "conformal": threshold(calibration, expected_ranks["conformal"]),
        }
        if row.get("ranks") != expected_ranks:
            errors.append("rank_mismatch")
        got_q = row.get("thresholds", {})
        for key, value in expected_q.items():
            if key not in got_q or not same_number(got_q[key], None if math.isinf(value) else value):
                errors.append("threshold_" + key)
        uniforms = {key: row.get(key) for key in ("id_u", "id_false_u", "shift_u", "shift_false_u")}
        if any(not isinstance(x, (int, float)) or not 0 <= x < 1 for x in uniforms.values()):
            return errors + ["test_uniforms"]
        tests = {
            "id": (math.sqrt(uniforms["id_u"]), math.sqrt(uniforms["id_false_u"])),
            "shift": (uniforms["shift_u"] ** 0.25, uniforms["shift_false_u"] ** 0.25),
        }
        actual = row.get("outcomes", {})
        for condition, (true_score, false_score) in tests.items():
            for policy, q in expected_q.items():
                expect = expected_outcome(q, true_score, false_score)
                if actual.get(condition, {}).get(policy) != expect:
                    errors.append(f"outcome_{condition}_{policy}")
            if condition == "shift":
                expect = expected_outcome(expected_q["conformal"], true_score, false_score, True)
                if actual.get(condition, {}).get("known_shift_contract") != expect:
                    errors.append("known_shift_contract")
    except (TypeError, ValueError, OverflowError):
        errors.append("row_exception")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    raw_bytes = args.raw.read_bytes()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in raw_bytes.splitlines()]
    errors = []
    freeze_path = Path(__file__).resolve().parent / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    source_checks = {}
    for name, expected_hash in freeze.get("source_sha256", {}).items():
        actual_hash = hashlib.sha256((freeze_path.parent / name).read_bytes()).hexdigest()
        source_checks[name] = actual_hash == expected_hash
        if not source_checks[name]:
            errors.append("source_hash_" + name)
    expected_counts = {n: 0 for n in SAMPLE_SIZES}
    aggregates = {}
    for index, row in enumerate(rows):
        errors.extend(f"row{index}:{error}" for error in row_errors(row))
        n = row.get("n")
        if n in expected_counts:
            if row.get("trial") != expected_counts[n]:
                errors.append(f"row{index}:trial_order")
            expected_counts[n] += 1
        for condition, policies in row.get("outcomes", {}).items():
            for policy, fields in policies.items():
                key = f"n{n}/{condition}/{policy}"
                counts = aggregates.setdefault(key, {name: 0 for name in ("true_included", "singleton", "wrong_singleton", "set_size", "empty")})
                for name, value in fields.items():
                    counts[name] += int(value) if isinstance(value, bool) else value
    if expected_counts != {n: TRIALS for n in SAMPLE_SIZES} or len(rows) != TRIALS * len(SAMPLE_SIZES):
        errors.append("denominator")
    summary = {}
    for key, values in sorted(aggregates.items()):
        summary[key] = {
            "trials": TRIALS,
            "true_inclusion_rate": values["true_included"] / TRIALS,
            "singleton_rate": values["singleton"] / TRIALS,
            "wrong_singleton_rate": values["wrong_singleton"] / TRIALS,
            "mean_set_size": values["set_size"] / TRIALS,
            "empty_rate": values["empty"] / TRIALS,
        }
    if receipt.get("summary") != summary or receipt.get("rows") != len(rows):
        errors.append("receipt_aggregate")
    if receipt.get("seed") != 5315 or receipt.get("alpha") != ALPHA or receipt.get("sample_sizes") != list(SAMPLE_SIZES):
        errors.append("receipt_contract")
    theoretical = {}
    for n in SAMPLE_SIZES:
        plug_k = math.ceil(n * (1 - ALPHA))
        conformal_k = math.ceil((n + 1) * (1 - ALPHA))
        for condition, shift in (("id", False), ("shift", True)):
            for policy, k in (("plugin", plug_k), ("conformal", conformal_k)):
                key = f"n{n}/{condition}/{policy}"
                if policy == "conformal" and k > n:
                    target = 1.0
                elif shift:
                    target = k * (k + 1) / ((n + 1) * (n + 2))
                else:
                    target = k / (n + 1)
                theoretical[key] = target
                if abs(summary.get(key, {}).get("true_inclusion_rate", -10.0) - target) > TOLERANCE:
                    errors.append("oracle_tolerance_" + key)
    if abs(summary.get("n4/id/raw", {}).get("true_inclusion_rate", -10) - 0.81) > TOLERANCE:
        errors.append("raw_id_oracle")
    if abs(summary.get("n4/shift/raw", {}).get("true_inclusion_rate", -10) - 0.6561) > TOLERANCE:
        errors.append("raw_shift_oracle")
    if any(summary.get(f"n{n}/shift/known_shift_contract", {}).get("singleton_rate") != 0 for n in SAMPLE_SIZES):
        errors.append("shift_singleton")
    if summary.get("n4/id/conformal", {}).get("singleton_rate") != 0 or summary.get("n4/id/conformal", {}).get("mean_set_size") != 2:
        errors.append("unattainable_rank_not_full_set")
    # Mutation controls prove the checker notices altered outcomes, cutoffs, and denominators.
    control_row = rows[0]
    mutation_controls = {}
    for name, mutate in (
        ("altered_outcome", lambda x: x["outcomes"]["id"]["raw"].update(singleton=True)),
        ("altered_threshold", lambda x: x["thresholds"].update(raw=0.91)),
        ("altered_calibration", lambda x: x["calibration_u"].__setitem__(0, 1.5)),
    ):
        changed = json.loads(json.dumps(control_row))
        mutate(changed)
        mutation_controls[name] = bool(row_errors(changed))
    if not all(mutation_controls.values()):
        errors.append("mutation_control")
    audit = {
        "status": "PASS_FIRST_UNIT_SCOPED" if not errors else "FAIL_AUDIT",
        "issue": 5315,
        "rows": len(rows),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "source_hash_checks": source_checks,
        "row_errors": errors,
        "mutation_controls": mutation_controls,
        "theoretical_true_inclusion": theoretical,
        "monte_carlo_tolerance": TOLERANCE,
        "all_rank_above_n_return_full_set": summary.get("n4/id/conformal", {}).get("mean_set_size") == 2,
        "shift_flag_singleton_rate_zero": all(summary.get(f"n{n}/shift/known_shift_contract", {}).get("singleton_rate") == 0 for n in SAMPLE_SIZES),
        "external_effect_or_authority_claim": False,
    }
    args.out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
