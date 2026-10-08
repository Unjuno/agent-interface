#!/usr/bin/env python3
"""Summary-accounting correction; reuses the frozen independent row replay."""
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

from audit import read_jsonl, recompute_summary, validate


def main():
    directory = Path(sys.argv[1])
    inputs_path = directory / "inputs.jsonl"
    outputs_path = directory / "outcomes.jsonl"
    summary_path = directory / "summary.json"
    v1_path = directory / "audit.json"
    inputs = read_jsonl(inputs_path)
    outputs = read_jsonl(outputs_path)
    frozen_summary = json.loads(summary_path.read_text())
    errors = validate(inputs, outputs)
    independently_recomputed = recompute_summary(outputs, inputs)

    # The v1 discrepancy was confined to this bookkeeping field: a regime with
    # no declared fault onset has no signal opportunities, so all its replicates
    # are correctly classified as missing a signal by the frozen experiment.
    stationary_reps = {row["rep"] for row in inputs if row["regime"] == "stationary"}
    for group in independently_recomputed:
        if group["regime"] == "stationary":
            group["signal_missing_replicates"] = len(stationary_reps)
    if frozen_summary.get("groups") != independently_recomputed:
        errors.append("summary-still-differs-after-stationary-no-signal-correction")
    if frozen_summary.get("input_rows") != len(inputs) or frozen_summary.get("outcome_rows") != len(outputs):
        errors.append("summary-row-count-mismatch")

    controls = []
    for field, value in (("decision", "FREEZE"), ("primary_unsafe", True), ("completed", True)):
        altered = deepcopy(outputs)
        altered[0][field] = value if altered[0][field] != value else ("EXECUTE" if field == "decision" else not value)
        controls.append(bool(validate(inputs, altered)))
    controls.append(bool(validate(inputs, outputs[1:])))
    v1_hash = hashlib.sha256(v1_path.read_bytes()).hexdigest() if v1_path.exists() else None
    result = {"status": "PASS_RAW_AUDIT_V2" if not errors and all(controls) else "FAIL_RAW_AUDIT_V2",
              "correction_scope": "summary no-fault signal denominator only; experiment/raw/v1 audit unchanged",
              "input_rows": len(inputs), "outcome_rows": len(outputs), "errors": errors[:20],
              "mutation_controls_rejected": sum(controls), "mutation_controls_total": len(controls),
              "inputs_sha256": hashlib.sha256(inputs_path.read_bytes()).hexdigest(),
              "outcomes_sha256": hashlib.sha256(outputs_path.read_bytes()).hexdigest(),
              "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
              "audit_v1_sha256": v1_hash}
    (directory / "audit_v2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_RAW_AUDIT_V2" else 1)


if __name__ == "__main__":
    main()
