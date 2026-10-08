"""Independent audit of A01's one raw-input mutation experiment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def classify_from_raw(row):
    samples = row.get("samples")
    admitted = row.get("admitted_ns")
    first_input = row.get("first_input_ns")
    max_gap = row.get("max_gap_ns")
    if (type(admitted) is not int or type(first_input) is not int or
            type(max_gap) is not int or max_gap <= 0 or
            type(row.get("missed_periods")) is not int or row["missed_periods"] != 0 or
            admitted >= first_input or type(samples) is not list or not samples):
        return "POST_CANCELLATION_COOCCURRENCE"
    if any(type(item) is not list or len(item) != 2 or
           type(item[0]) is not int or type(item[1]) is not int or item[1] < 0
           for item in samples):
        return "POST_CANCELLATION_COOCCURRENCE"
    if any(right[0] <= left[0] for left, right in zip(samples, samples[1:])):
        return "POST_CANCELLATION_COOCCURRENCE"
    baseline = next((item for item in samples if admitted < item[0] < first_input), None)
    if baseline is None:
        return "POST_CANCELLATION_COOCCURRENCE"
    for timestamp, score in samples:
        if timestamp <= first_input:
            continue
        if timestamp - baseline[0] > max_gap:
            return "POST_CANCELLATION_COOCCURRENCE"
        if score > baseline[1]:
            return "ADMISSION_BRACKETED_PROGRESS"
    return "POST_CANCELLATION_COOCCURRENCE"


def audit():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    run = json.loads((HERE / "RUN.json").read_text(encoding="utf-8"))
    errors = []
    expected_freeze_hash = hashlib.sha256((HERE / "FREEZE.json").read_bytes()).hexdigest()
    if run.get("freeze_sha256") != expected_freeze_hash:
        errors.append("freeze_hash")
    raw_bytes = (HERE / "frozen" / "raw.json").read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest() != freeze.get("source_sha256", {}).get("raw.json"):
        errors.append("frozen_raw_hash")
    original = json.loads(raw_bytes)
    if hashlib.sha256((HERE / "frozen" / "audit.py").read_bytes()).hexdigest() != freeze.get("source_sha256", {}).get("audit.py"):
        errors.append("frozen_auditor_hash")
    if hashlib.sha256((HERE / "frozen" / "candidate.py").read_bytes()).hexdigest() != freeze.get("source_sha256", {}).get("candidate.py"):
        errors.append("frozen_candidate_hash")
    baseline_row = next(row for row in original["rows"]
                        if row["id"] == freeze["mutation"]["row_id"])
    baseline_oracle = classify_from_raw(baseline_row)
    baseline_observed = baseline_row.get("observed", {}).get("decision")

    mutated_path = HERE / run.get("mutated", {}).get("audit", {}).get("directory", "") / "raw.json"
    if not mutated_path.is_file():
        errors.append("mutated_raw_missing")
        mutated = {}
        mutated_row = {}
    else:
        mutated = json.loads(mutated_path.read_bytes())
        mutated_row = next((row for row in mutated.get("rows", [])
                            if row.get("id") == freeze["mutation"]["row_id"]), {})
    mutation = freeze["mutation"]
    try:
        sample = mutated_row["samples"][mutation["sample_index"]]
        if sample[1] != mutation["score_after"] or sample[1] != 0:
            errors.append("mutation_not_applied")
    except (KeyError, IndexError, TypeError):
        errors.append("mutation_shape")
    mutated_oracle = classify_from_raw(mutated_row) if mutated_row else None
    mutated_observed = mutated_row.get("observed", {}).get("decision")
    baseline_audit = run.get("baseline", {}).get("audit", {})
    mutated_audit = run.get("mutated", {}).get("audit", {})
    if baseline_audit.get("exit_code") != 0 or baseline_audit.get("audit_pass") is not True:
        errors.append("baseline_audit_not_pass")
    if mutated_audit.get("exit_code") != 0 or mutated_audit.get("audit_pass") is not True:
        errors.append("mutated_old_auditor_did_not_pass")
    if baseline_oracle != baseline_observed:
        errors.append("baseline_oracle_disagrees")
    if mutated_oracle == mutated_observed:
        errors.append("mutation_did_not_diverge_from_retained_decision")
    if run.get("baseline_raw_sha256") != hashlib.sha256(raw_bytes).hexdigest():
        errors.append("baseline_raw_sha256")
    if run.get("mutated_raw_sha256") != hashlib.sha256(mutated_path.read_bytes()).hexdigest():
        errors.append("mutated_raw_sha256")
    outcome = "PASS_REPRODUCED_AUDITOR_FALSE_PASS" if not errors else "FAIL_AUDIT"
    return {
        "experiment_id": run.get("experiment_id"),
        "independent_audit": outcome,
        "checks": {
            "baseline_decision_recomputes": baseline_oracle == baseline_observed,
            "original_auditor_accepts_frozen_baseline": baseline_audit.get("audit_pass") is True,
            "mutated_input_changes_recomputed_decision": mutated_oracle != mutated_observed,
            "original_auditor_accepts_mutated_raw": mutated_audit.get("audit_pass") is True,
            "frozen_source_hashes_match": not any(error in errors for error in (
                "frozen_raw_hash", "frozen_auditor_hash", "frozen_candidate_hash")),
        },
        "baseline_recomputed": baseline_oracle,
        "baseline_retained": baseline_observed,
        "mutated_recomputed": mutated_oracle,
        "mutated_retained": mutated_observed,
        "errors": errors,
        "scope": "Synthetic scorer-attribution raw-audit integrity only; no runtime or causal claim.",
    }


if __name__ == "__main__":
    result = audit()
    (HERE / "AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["independent_audit"] == "PASS_REPRODUCED_AUDITOR_FALSE_PASS" else 1)
