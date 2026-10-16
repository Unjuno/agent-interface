"""Run the frozen scorer-attribution auditor against one raw-input mutation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
FROZEN = HERE / "frozen"
CASES = HERE / "cases"


def classify_from_raw(row):
    """Small independent decision reconstruction; does not import candidate.py."""
    samples = row.get("samples")
    admitted_ns = row.get("admitted_ns")
    first_input_ns = row.get("first_input_ns")
    max_gap_ns = row.get("max_gap_ns")
    missed_periods = row.get("missed_periods")
    reject = {"decision": "POST_CANCELLATION_COOCCURRENCE"}
    if (type(admitted_ns) is not int or type(first_input_ns) is not int or
            type(max_gap_ns) is not int or max_gap_ns <= 0 or
            type(missed_periods) is not int or missed_periods < 0 or
            admitted_ns >= first_input_ns or missed_periods != 0 or
            type(samples) is not list or not samples):
        return reject
    if any(type(sample) is not list or len(sample) != 2 or
           type(sample[0]) is not int or type(sample[1]) is not int or sample[1] < 0
           for sample in samples):
        return reject
    if any(right[0] <= left[0] for left, right in zip(samples, samples[1:])):
        return reject
    baseline = next((sample for sample in samples
                     if admitted_ns < sample[0] < first_input_ns), None)
    if baseline is None:
        return reject
    for sample_ns, score in samples:
        if sample_ns <= first_input_ns:
            continue
        if sample_ns - baseline[0] > max_gap_ns:
            return reject
        if score > baseline[1]:
            return {"decision": "ADMISSION_BRACKETED_PROGRESS",
                    "baseline_ns": baseline[0],
                    "positive_sample_ns": sample_ns,
                    "gap_ns": sample_ns - baseline[0]}
    return reject


def run_audit_case(name: str, raw_bytes: bytes) -> dict:
    case_dir = CASES / name
    case_dir.mkdir(parents=True, exist_ok=False)
    (case_dir / "audit.py").write_bytes((FROZEN / "audit.py").read_bytes())
    (case_dir / "raw.json").write_bytes(raw_bytes)
    result = subprocess.run(
        [sys.executable, str(case_dir / "audit.py")],
        cwd=case_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    (case_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (case_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    (case_dir / "exit.txt").write_text(str(result.returncode), encoding="ascii")
    audit_report = json.loads((case_dir / "audit.json").read_text(encoding="utf-8"))
    return {
        "directory": f"cases/{name}",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "exit_code": result.returncode,
        "audit_pass": audit_report.get("pass"),
        "audit_errors": audit_report.get("errors"),
        "stdout_sha256": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest(),
    }


def main() -> int:
    original_bytes = (FROZEN / "raw.json").read_bytes()
    original = json.loads(original_bytes)
    baseline_row = next(row for row in original["rows"]
                        if row["id"] == "bracketed_bounded_positive")
    baseline_recomputed = classify_from_raw(baseline_row)
    if baseline_row.get("observed") != baseline_recomputed:
        raise SystemExit("frozen baseline already disagrees with independent reconstruction")

    mutated = json.loads(original_bytes)
    row = next(row for row in mutated["rows"]
               if row["id"] == "bracketed_bounded_positive")
    row["samples"][2][1] = 0
    mutated_bytes = (json.dumps(mutated, indent=2, sort_keys=True) + "\n").encode("utf-8")
    mutated_row = next(item for item in mutated["rows"]
                       if item["id"] == "bracketed_bounded_positive")
    mutated_recomputed = classify_from_raw(mutated_row)

    CASES.mkdir(exist_ok=False)
    baseline_audit = run_audit_case("baseline", original_bytes)
    mutated_audit = run_audit_case("positive_sample_removed", mutated_bytes)
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    result = {
        "experiment_id": "scorer-admission-audit-recompute-7471-a01",
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "baseline_raw_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "mutated_raw_sha256": hashlib.sha256(mutated_bytes).hexdigest(),
        "mutation": {
            "row_id": "bracketed_bounded_positive",
            "sample_index": 2,
            "score_before": 1,
            "score_after": 0,
            "preserved_declared_expected_and_observed": True,
        },
        "baseline": {
            "audit": baseline_audit,
            "independent_reconstruction": baseline_recomputed,
        },
        "mutated": {
            "audit": mutated_audit,
            "independent_reconstruction": mutated_recomputed,
            "retained_observed": mutated_row.get("observed"),
        },
        "outcome": (
            "FAIL_AUDITOR_ACCEPTS_RAW_MUTATION"
            if baseline_audit["exit_code"] == 0 and baseline_audit["audit_pass"] is True
            and mutated_audit["exit_code"] == 0 and mutated_audit["audit_pass"] is True
            and mutated_recomputed.get("decision") != mutated_row.get("observed", {}).get("decision")
            else "HOLD_EXPECTED_MUTATION_NOT_REPRODUCED"
        ),
        "scope": "Synthetic raw-result audit-integrity mutation only; no game, model, live input, GUI, container, or allocation.",
    }
    (HERE / "RUN.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"experiment_id": result["experiment_id"],
                      "outcome": result["outcome"],
                      "baseline_audit_pass": baseline_audit["audit_pass"],
                      "mutated_audit_pass": mutated_audit["audit_pass"],
                      "mutated_recomputed_decision": mutated_recomputed.get("decision"),
                      "mutated_retained_decision": mutated_row.get("observed", {}).get("decision")},
                     sort_keys=True))
    return 0 if result["outcome"] == "FAIL_AUDITOR_ACCEPTS_RAW_MUTATION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
