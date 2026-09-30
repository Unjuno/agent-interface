#!/usr/bin/env python3
"""Additive auditor successor for immutable allocation-01 raw bytes.

Reuses only audit-v1's candidate-independent row reconstruction. It recomputes
denominators, aggregate receipts, analytic coverage gates, and effective
mutation controls; it never imports run.py or reruns the simulation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import audit as v1

ALPHA = 0.10
TRIALS = 10_000
SAMPLE_SIZES = (4, 10)
TOLERANCE = 0.015


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    raw_bytes = args.raw.read_bytes()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in raw_bytes.splitlines()]
    failures = []
    freeze_dir = Path(__file__).resolve().parent
    successor_freeze = json.loads((freeze_dir / "AUDIT_V2_FREEZE.json").read_text(encoding="utf-8"))
    source_hashes = {}
    for name, expected_hash in successor_freeze.get("source_sha256", {}).items():
        actual_hash = hashlib.sha256((freeze_dir / name).read_bytes()).hexdigest()
        source_hashes[name] = actual_hash
        if actual_hash != expected_hash:
            failures.append("source_hash:" + name)
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    receipt_hash = hashlib.sha256(args.receipt.read_bytes()).hexdigest()
    if raw_hash != successor_freeze.get("formal_raw_sha256"):
        failures.append("formal_raw_hash")
    if receipt_hash != successor_freeze.get("formal_receipt_sha256"):
        failures.append("formal_receipt_hash")
    counts_by_n = {n: 0 for n in SAMPLE_SIZES}
    aggregate = {}
    for i, row in enumerate(rows):
        failures.extend(f"row{i}:{x}" for x in v1.row_errors(row))
        n = row.get("n")
        if n not in counts_by_n:
            failures.append(f"row{i}:unexpected_n")
            continue
        if row.get("trial") != counts_by_n[n]:
            failures.append(f"row{i}:trial_sequence")
        counts_by_n[n] += 1
        for condition, policies in row.get("outcomes", {}).items():
            for policy, outcome in policies.items():
                key = f"n{n}/{condition}/{policy}"
                acc = aggregate.setdefault(key, {k: 0 for k in ("true_included", "singleton", "wrong_singleton", "set_size", "empty")})
                for field, value in outcome.items():
                    acc[field] += int(value) if isinstance(value, bool) else value
    if len(rows) != 20_000 or counts_by_n != {4: TRIALS, 10: TRIALS}:
        failures.append("row_denominator")
    summary = {}
    for key, values in sorted(aggregate.items()):
        summary[key] = {
            "trials": TRIALS,
            "true_inclusion_rate": values["true_included"] / TRIALS,
            "singleton_rate": values["singleton"] / TRIALS,
            "wrong_singleton_rate": values["wrong_singleton"] / TRIALS,
            "mean_set_size": values["set_size"] / TRIALS,
            "empty_rate": values["empty"] / TRIALS,
        }
    if receipt.get("rows") != len(rows) or receipt.get("summary") != summary:
        failures.append("receipt_reconstruction")
    if (receipt.get("allocation"), receipt.get("seed"), receipt.get("alpha"), receipt.get("sample_sizes")) != (
        "conformal-risk-5315-v01-20260930-01", 5315, ALPHA, list(SAMPLE_SIZES)
    ):
        failures.append("receipt_frozen_parameters")
    expected = {}
    for n in SAMPLE_SIZES:
        ranks = {"plugin": math.ceil(n * (1 - ALPHA)), "conformal": math.ceil((n + 1) * (1 - ALPHA))}
        for condition in ("id", "shift"):
            for policy, k in ranks.items():
                key = f"n{n}/{condition}/{policy}"
                target = 1.0 if policy == "conformal" and k > n else (
                    k * (k + 1) / ((n + 1) * (n + 2)) if condition == "shift" else k / (n + 1)
                )
                expected[key] = target
                if abs(summary.get(key, {}).get("true_inclusion_rate", -100) - target) > TOLERANCE:
                    failures.append("finite_sample_oracle:" + key)
    for key, target in (("n4/id/raw", .81), ("n4/shift/raw", .6561)):
        if abs(summary.get(key, {}).get("true_inclusion_rate", -100) - target) > TOLERANCE:
            failures.append("raw_threshold_oracle:" + key)
    if summary.get("n4/id/conformal", {}).get("singleton_rate") != 0 or summary.get("n4/id/conformal", {}).get("mean_set_size") != 2:
        failures.append("underpowered_rank_singleton")
    if any(summary.get(f"n{n}/shift/known_shift_contract", {}).get("singleton_rate") != 0 for n in SAMPLE_SIZES):
        failures.append("known_shift_singleton")

    control = json.loads(json.dumps(rows[0]))
    before = control["outcomes"]["id"]["raw"]["singleton"]
    control["outcomes"]["id"]["raw"]["singleton"] = not before
    mutations = {
        "outcome_flip_detected": bool(v1.row_errors(control)),
        "threshold_change_detected": bool(v1.row_errors({**rows[0], "thresholds": {**rows[0]["thresholds"], "raw": 0.91}})),
        "calibration_corruption_detected": bool(v1.row_errors({**rows[0], "calibration_u": [1.5] + rows[0]["calibration_u"][1:]})),
    }
    if not all(mutations.values()):
        failures.append("mutation_controls")

    allocation_freeze = json.loads((freeze_dir / "FREEZE.json").read_text(encoding="utf-8"))
    v1_hash = hashlib.sha256((freeze_dir / "audit.py").read_bytes()).hexdigest()
    if v1_hash != allocation_freeze["source_sha256"]["audit.py"]:
        failures.append("v1_auditor_source_hash")
    result = {
        "status": "PASS_FIRST_UNIT_SCOPED" if not failures else "FAIL_AUDIT_V2",
        "allocation": "conformal-risk-5315-v01-20260930-01",
        "formal_invocations": 1,
        "audit_attempts": 2,
        "rows": len(rows),
        "raw_sha256": raw_hash,
        "receipt_reconstructed": receipt.get("summary") == summary,
        "source_hashes": source_hashes,
        "mutation_controls": mutations,
        "finite_sample_expected_inclusion": expected,
        "monte_carlo_tolerance": TOLERANCE,
        "failures": failures,
        "external_effect_or_authority_claim": False,
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
