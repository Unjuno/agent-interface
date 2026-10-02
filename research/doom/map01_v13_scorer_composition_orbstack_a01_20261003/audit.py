#!/usr/bin/env python3
"""Independent, non-executing audit of the retained A01 candidate receipt."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    freeze_path = ROOT / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text())
    receipt = json.loads((ROOT / "INVOCATION_RECEIPT.json").read_text())
    raw_path = ROOT / "RAW_STDOUT.txt"
    raw = raw_path.read_text()
    errors = []
    if receipt["allocation_id"] != freeze["allocation_id"]:
        errors.append("allocation_id_mismatch")
    if receipt["image_id"] != freeze["image"].split("@", 1)[1]:
        errors.append("image_id_mismatch")
    if receipt["platform"] != freeze["platform"]:
        errors.append("platform_mismatch")
    if receipt["exit_code"] != 0 or receipt["test_count"] != 4:
        errors.append("candidate_exit_or_count_mismatch")
    if receipt["retry_count"] != 0 or receipt["candidate_invocations"] != 1:
        errors.append("candidate_cardinality_mismatch")
    if "Ran 4 tests in " not in raw or not raw.rstrip().endswith("OK"):
        errors.append("raw_stdout_contract_mismatch")
    if receipt["raw_stdout"] != raw_path.name:
        errors.append("raw_path_mismatch")
    source_hashes = {}
    for rel, expected in freeze["source_sha256"].items():
        source = ROOT.parents[2] / rel
        actual = sha(source)
        source_hashes[rel] = actual
        if actual != expected:
            errors.append("source_hash_mismatch:" + rel)
    return {
        "schema": "obstac-independent-audit-v1",
        "allocation_id": freeze["allocation_id"],
        "decision": "PASS_CONSTRUCTION_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "freeze_sha256": sha(freeze_path),
        "raw_stdout_sha256": sha(raw_path),
        "audited_source_sha256": source_hashes,
        "candidate_invocations": receipt["candidate_invocations"],
        "auditor_invocations": 1,
        "retry_count": receipt["retry_count"]
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True, indent=2))
