"""Separate raw-only audit process; candidate module is never imported."""

import hashlib
import json
import os
import sys
from pathlib import Path

from audit import audit_bytes


ROOT = Path(__file__).parent
RESULTS = ROOT / "results"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    raw = (RESULTS / "candidate.stdout.json").read_bytes()
    run = json.loads((RESULTS / "RUN.json").read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "EXPECTED.json").read_text(encoding="utf-8"))
    audit = audit_bytes(raw, fixture, expected)
    expected_sources = freeze["frozen_source_sha256"]
    if run.get("candidate_invocations") != 1 or type(run.get("candidate_exit_code")) is not int or run["candidate_exit_code"] != 0:
        audit["errors"].append("RUN_RECEIPT_INVALID")
    if run.get("stdout_sha256") != sha256(raw):
        audit["errors"].append("RUN_RAW_HASH_MISMATCH")
    stderr = (RESULTS / "candidate.stderr.txt").read_bytes()
    if run.get("stderr_sha256") != sha256(stderr) or stderr:
        audit["errors"].append("CANDIDATE_STDERR_NOT_EMPTY_OR_HASH_MISMATCH")
    if run.get("source_sha256") != expected_sources:
        audit["errors"].append("RUN_SOURCE_HASH_MISMATCH")
    for name, frozen_sha in expected_sources.items():
        if sha256((ROOT / name).read_bytes()) != frozen_sha:
            audit["errors"].append(f"SOURCE_CHANGED_AFTER_FREEZE:{name}")
    if sha256(Path(__file__).read_bytes()) != expected_sources.get("audit_once.py"):
        audit["errors"].append("AUDITOR_SOURCE_HASH_MISMATCH")

    pristine = json.loads(raw.decode("utf-8"))
    missing_control = json.loads(json.dumps(pristine))
    missing_control["cases"][2]["ledger"].pop()
    missing_control_audit = audit_bytes(
        json.dumps(missing_control).encode("utf-8"), fixture, expected
    )
    changed_identity = json.loads(json.dumps(pristine))
    changed_identity["cases"][3]["ledger"][0]["assigned_seal"] = "tampered-seal"
    changed_identity_audit = audit_bytes(
        json.dumps(changed_identity).encode("utf-8"), fixture, expected
    )
    mutation_controls = {
        "omitted_control_row_rejected": "CONTROL_DENOMINATOR_MISMATCH:route_missingness" in missing_control_audit["errors"],
        "changed_assignment_seal_rejected": "ASSIGNMENT_SEAL_MISMATCH:foreign_join:direct:e1" in changed_identity_audit["errors"],
    }
    audit["mutation_controls"] = mutation_controls
    audit["candidate_raw_sha256"] = sha256(raw)
    audit["auditor_invocations"] = 1
    audit["base_main"] = freeze["base_main"]
    audit["allocation"] = freeze["allocation"]
    if not all(mutation_controls.values()):
        audit["errors"].append("MUTATION_CONTROL_NOT_REJECTED")
    audit["status"] = "PASS_METHOD_SCOPED" if not audit["errors"] else "FAIL_METHOD"
    write_new(RESULTS / "AUDIT.json", (json.dumps(audit, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"status": audit["status"], "errors": audit["errors"]}, sort_keys=True))
    return 0 if audit["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
