#!/usr/bin/env python3
"""Audit saved A01 outputs without importing or executing the projector."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_interval(value):
    return (type(value) is list and len(value) == 2 and
            all(type(item) is int for item in value))


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    raw = json.loads((ROOT / "raw" / "A01.json").read_text())
    files = {
        "baseline_source": ROOT / "BASELINE_SOURCE.py.txt",
        "candidate_source": ROOT / "CANDIDATE_SOURCE.py.txt",
        "test_source": ROOT / "TEST_SOURCE.py.txt",
        "input": ROOT / "INPUT.jsonl",
        "runner": ROOT / "run_a01.py",
        "auditor": ROOT / "audit_a01.py",
        "auditor_test": ROOT / "test_audit_a01.py",
        "readme": ROOT / "README.md",
        "environment": ROOT / "ENVIRONMENT.json",
    }
    errors = []
    for name, path in files.items():
        observed = sha256(path)
        expected = freeze["sha256"][name]
        if observed != expected:
            errors.append(f"{name} hash mismatch")
    if raw.get("sources", {}).get("baseline_sha256") != freeze["sha256"]["baseline_source"]:
        errors.append("raw baseline source hash mismatch")
    if raw.get("sources", {}).get("candidate_sha256") != freeze["sha256"]["candidate_source"]:
        errors.append("raw candidate source hash mismatch")
    if raw.get("sources", {}).get("input_sha256") != freeze["sha256"]["input"]:
        errors.append("raw input hash mismatch")

    mutations = raw.get("application_flag_mutations", [])
    expected_mutations = [(row, layer) for row in range(2)
                          for layer in ("event", "measurement", "adapter_edge", "bracket")]
    observed_mutations = [(row.get("row_index"), row.get("layer")) for row in mutations]
    if observed_mutations != expected_mutations:
        errors.append("mutation matrix identity/order mismatch")
    for row in mutations:
        if row.get("candidate", {}).get("status") != "adapter_edge_receipt_incomplete":
            errors.append(f"candidate accepted contradictory application claim: {row}")
        if (row.get("candidate", {}).get("down_edge_interval_ns") is not None or
                row.get("candidate", {}).get("up_edge_interval_ns") is not None):
            errors.append("candidate exposed an interval for contradictory claim")
    baseline_false_accepts = [row for row in mutations
                              if row.get("baseline", {}).get("status") ==
                              "adapter_edge_brackets_paired"]

    sweep_summary = {}
    for implementation in ("baseline", "candidate"):
        sweep = raw.get("interval_sweep", {}).get(implementation, {})
        cases = sweep.get("cases", [])
        if len(cases) != 100:
            errors.append(f"{implementation} interval case count != 100")
        paired = incomplete = 0
        for index, row in enumerate(cases):
            down = row.get("down")
            up = row.get("up")
            intervals_valid = valid_interval(down) and valid_interval(up)
            if not intervals_valid:
                errors.append(f"{implementation} interval case {index} has invalid bounds")
            derived_ordered = intervals_valid and down[1] < up[0]
            recorded_ordered = row.get("expected_ordered")
            if (type(recorded_ordered) is not bool or
                    recorded_ordered != derived_ordered):
                errors.append(f"{implementation} interval case {index} ordering mismatch")
            # Derive classification from the interval bounds instead of trusting
            # the expected_ordered field retained alongside the output.
            ordered = derived_ordered
            expected_status = ("adapter_edge_brackets_paired" if ordered else
                               "adapter_edge_receipt_incomplete")
            if row.get("status") != expected_status:
                errors.append(f"{implementation} interval classification mismatch")
            if ordered:
                paired += 1
                if (row.get("down_edge_interval_ns") != row.get("down") or
                        row.get("up_edge_interval_ns") != row.get("up")):
                    errors.append(f"{implementation} interval output mismatch")
            else:
                incomplete += 1
                if (row.get("down_edge_interval_ns") is not None or
                        row.get("up_edge_interval_ns") is not None):
                    errors.append(f"{implementation} exposed unordered intervals")
        if (paired, incomplete) != (15, 85):
            errors.append(f"{implementation} expected 15/85, got {paired}/{incomplete}")
        sweep_summary[implementation] = {"cases": len(cases), "paired": paired,
                                        "incomplete": incomplete}

    if raw.get("valid_control", {}).get("status") != "adapter_edge_brackets_paired":
        errors.append("valid paired input control did not pair")
    if not baseline_false_accepts:
        errors.append("baseline did not reproduce a false accept")
    if raw.get("candidate_false_accept_count") != 0:
        errors.append("candidate false-accept total is nonzero")
    result = {
        "status": "PASS_SAVED_RESULT_AUDIT" if not errors else "FAIL_SAVED_RESULT_AUDIT",
        "errors": errors,
        "baseline_false_accept_count": len(baseline_false_accepts),
        "candidate_false_accept_count": raw.get("candidate_false_accept_count"),
        "interval_sweep": sweep_summary,
        "scope": "Saved-result consistency with strict ordering derived from saved interval bounds; does not validate source truth, X-server behavior, application consumption, or live task effect.",
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "raw" / "AUDIT.json").write_text(encoded)
    print(encoded, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
