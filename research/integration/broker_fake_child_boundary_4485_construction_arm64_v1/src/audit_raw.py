#!/usr/bin/env python3
"""Independent raw-only construction audit; imports neither broker nor runner."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def audit(raw: dict, expected_source_blob: str) -> list[str]:
    errors = []
    if raw.get("schema") != "broker-fake-child-boundary-construction-raw-v1": errors.append("schema")
    if raw.get("issue") != 5013 or raw.get("allocation") != "broker-fake-child-boundary-4485-arm64-construction-20260928-01": errors.append("allocation")
    if raw.get("source_git_blob") != expected_source_blob: errors.append("source_blob")
    if raw.get("source_sha256_before") != raw.get("source_sha256_after"): errors.append("source_hash_changed")
    if raw.get("case") != "ACTUAL_FAKE_CHILD_EXIT_23": errors.append("case")
    if raw.get("broker_process_exit") != 23: errors.append("broker_exit_not_propagated")
    receipt = raw.get("broker_receipt")
    if not isinstance(receipt, dict):
        errors.append("receipt_missing")
        receipt = {}
    if receipt.get("request_id") != "case-exit-23" or receipt.get("returncode") != 23: errors.append("receipt_exit")
    if receipt.get("authority_granted") is not False: errors.append("authority")
    if receipt.get("boundary") != "host-local-codex-exe": errors.append("boundary")
    if "error_class" in receipt or "stop_reason" in receipt: errors.append("unexpected_failure_receipt")
    if raw.get("response") != "partial fake-child response\n": errors.append("response")
    child = raw.get("fake_child_call")
    if not isinstance(child, dict):
        errors.append("fake_child_not_invoked")
        child = {}
    if child.get("intended_exit") != 23: errors.append("fake_child_exit_witness")
    if child.get("stdin") != "frozen construction probe\n": errors.append("stdin")
    argv = child.get("argv", [])
    if "exec" not in argv or "--output-schema" not in argv or "-C" not in argv: errors.append("child_argv")
    if raw.get("authority_requested") is not False: errors.append("request_authority")
    if not isinstance(receipt.get("started_ns"), int) or not isinstance(receipt.get("exited_ns"), int): errors.append("timestamps")
    return errors


def main(raw_path: Path, audit_path: Path, source_git_blob: str) -> None:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    errors = audit(raw, source_git_blob)
    mutations = {}
    controls = {
        "broker_exit": lambda d: d.update(broker_process_exit=0),
        "receipt_exit": lambda d: d["broker_receipt"].update(returncode=0),
        "authority": lambda d: d["broker_receipt"].update(authority_granted=True),
        "boundary": lambda d: d["broker_receipt"].update(boundary="other"),
        "response": lambda d: d.update(response=""),
        "child_count": lambda d: d.update(fake_child_call=None),
        "stdin": lambda d: d["fake_child_call"].update(stdin=""),
        "source_hash": lambda d: d.update(source_sha256_after="0" * 64),
    }
    for name, mutate in controls.items():
        import copy
        corrupt = copy.deepcopy(raw)
        mutate(corrupt)
        mutations[name] = bool(audit(corrupt, source_git_blob))
    rejected = sum(mutations.values())
    disposition = "STOP_RAW_AUDIT" if errors else ("PASS_REAL_FAKE_CHILD_NONZERO_CONSTRUCTION_SCOPED" if rejected == len(controls) else "FAIL_AUDIT_CORRUPTION_GATE")
    result = {
        "schema": "broker-fake-child-boundary-construction-audit-v1",
        "disposition": disposition,
        "errors": errors,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "mutation_controls_rejected": rejected,
        "mutation_control_count": len(controls),
        "mutation_controls": mutations,
        "formal_issue_5013_cases": 0,
        "scope": "one ARM64 Python container and one fake-child exit-23 case only",
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if errors or rejected != len(controls): raise SystemExit(1)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
