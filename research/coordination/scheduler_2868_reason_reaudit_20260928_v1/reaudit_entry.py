#!/usr/bin/env python3
"""Read-only re-audit of the preserved #2868 raw; never invokes scheduler workers."""
import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git_blob_sha(data):
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()

def exact_bytes(path, expected_sha256):
    data = path.read_bytes()
    if sha(data) == expected_sha256:
        return data
    if data.endswith(b"\n") and sha(data[:-1]) == expected_sha256:
        return data[:-1]
    raise ValueError("SHA256_MISMATCH:" + path.name)

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: reaudit_entry.py RAW_JSON OUTPUT_JSON")
    raw_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])
    freeze = json.loads((ROOT / "REAUDIT_FREEZE.json").read_text(encoding="utf-8"))
    identity = {}
    for key, relative in freeze["file_paths"].items():
        data = exact_bytes(ROOT / relative, freeze["file_sha256"][key])
        identity[key] = {"sha256": sha(data), "bytes": len(data), "matches_freeze": True}

    scientific_freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    fixture_bytes = exact_bytes(ROOT / "scenarios.json", scientific_freeze["source_sha256"]["scenarios.json"])
    raw_sha_line = raw_path.with_name("raw.sha256").read_text(encoding="ascii").strip().split()
    if len(raw_sha_line) != 2 or raw_sha_line[1] != "raw.json":
        raise ValueError("RAW_SHA256_FILE_FORMAT")
    raw_bytes = exact_bytes(raw_path, raw_sha_line[0])
    if git_blob_sha(raw_bytes) != freeze["preserved_raw_git_blob"]:
        raise ValueError("RAW_GIT_BLOB_MISMATCH")
    raw = json.loads(raw_bytes)
    fixture = json.loads(fixture_bytes)

    prior_audit_bytes = exact_bytes(ROOT / "previous_audit.json", freeze["prior_audit_sha256"])
    prior_audit = json.loads(prior_audit_bytes)
    if prior_audit.get("decision") != "HOLD_OR_FAIL_SCHEDULER_SELECTION" or len(prior_audit.get("errors", [])) != 24:
        raise ValueError("PRIOR_STOP_RECORD_MISMATCH")
    stop_record = json.loads((ROOT / "STOP_REPORT.json").read_text(encoding="utf-8"))
    if stop_record.get("allocation") != raw.get("allocation") or stop_record.get("runner", {}).get("raw_sha256") != sha(raw_bytes):
        raise ValueError("STOP_RAW_LINK_MISMATCH")
    if prior_audit.get("raw_sha256") != sha(raw_bytes) or prior_audit.get("decision") != stop_record.get("independent_audit", {}).get("decision"):
        raise ValueError("PRIOR_AUDIT_STOP_LINK_MISMATCH")

    module_spec = importlib.util.spec_from_file_location("corrected_scheduler_audit", ROOT / "audit_corrected.py")
    audit = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(audit)
    errors = audit.audit_doc(raw, fixture, scientific_freeze)
    controls = audit.corruption_controls(raw, fixture, scientific_freeze)
    rejected = sum(bool(value) for value in controls.values())
    expected_controls = freeze["expected_corruption_controls"]
    reason_control_rejected = bool(controls.get("trace_reason", False))
    decision = (
        "PASS_REAUDIT_SEMANTICS_SCOPED"
        if not errors and rejected == expected_controls and reason_control_rejected
        else "HOLD_OR_FAIL_REAUDIT"
    )
    report = {
        "schema": "scheduler-selection-reaudit-v1",
        "allocation_reexecuted": False,
        "scheduler_worker_processes": 0,
        "preserved_raw_sha256": sha(raw_bytes),
        "preserved_raw_git_blob": git_blob_sha(raw_bytes),
        "rows_reaudited": len(raw.get("rows", [])),
        "prior_stop_decision_preserved": prior_audit["decision"],
        "prior_reference_trace_errors": len(prior_audit["errors"]),
        "prior_stop_reason": stop_record["stop_reason"],
        "decision": decision,
        "errors": errors,
        "corruption_controls": controls,
        "corruption_controls_rejected": rejected,
        "expected_corruption_controls": expected_controls,
        "trace_reason_corruption_rejected": reason_control_rejected,
        "frozen_inputs": identity,
        "scope": "posthoc raw-only independent-auditor correction check; not a rerun or retroactive relabeling of the consumed allocation",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    output_path.write_bytes(out)
    print(out.decode("utf-8"), end="")
    sys.exit(0 if decision == "PASS_REAUDIT_SEMANTICS_SCOPED" else 2)

if __name__ == "__main__":
    main()
