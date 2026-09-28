"""Posthoc integrity check for the allocation-02 setup STOP only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path) -> dict:
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    raw_path = root / "results/allocation-02/RAW.json"
    run_path = root / "results/allocation-02/RUN_RECORD.json"
    cleanup_path = root / "results/allocation-02/CLEANUP.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    run = json.loads(run_path.read_text(encoding="utf-8"))
    cleanup = json.loads(cleanup_path.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "broker_path_windows_junction_4882_raw_v1":
        errors.append("raw_schema")
    if raw.get("allocation") != freeze.get("allocation") or run.get("allocation") != freeze.get("allocation"):
        errors.append("allocation_identity")
    if raw.get("source_main") != freeze.get("source_main"):
        errors.append("source_main")
    if raw.get("candidate_git_blob") != freeze.get("upstream_candidate", {}).get("git_blob"):
        errors.append("candidate_blob")
    for name in ("path_policy.py", "runner.py", "audit.py"):
        if sha256(root / name) != freeze["files"][name]:
            errors.append(name + "_freeze_digest")
    if raw.get("candidate_sha256") != freeze["files"]["path_policy.py"]:
        errors.append("raw_candidate_digest")
    if raw.get("runner_sha256") != freeze["files"]["runner.py"]:
        errors.append("raw_runner_digest")
    if raw.get("status") != "STOP_SETUP_JUNCTION_UNAVAILABLE" or raw.get("rows") != []:
        errors.append("stop_disposition")
    setup = raw.get("fixture", {}).get("setup", [])
    if len(setup) != 2 or not all(
        item.get("returncode") == 1 and item.get("setup_ok") is False for item in setup
    ):
        errors.append("setup_receipts")
    if (
        run.get("runner_invocations") != 1
        or run.get("runner_exit_code") != 2
        or run.get("path_case_rows") != 0
        or run.get("cause") != "unknown"
        or run.get("raw_sha256") != sha256(raw_path)
    ):
        errors.append("run_record")
    if (
        cleanup.get("fixture_removed") is not False
        or cleanup.get("cleanup_status") != "NOT_COMPLETED_TOOL_POLICY_BLOCK"
    ):
        errors.append("cleanup_record")
    return {
        "schema": "broker_path_windows_junction_4882_stop_audit_v1",
        "status": "PASS_STOP_RECORD_INTEGRITY" if not errors else "FAIL_STOP_RECORD_INTEGRITY",
        "checks": ["frozen identities", "two setup return codes", "zero path rows", "run exit and cleanup record"],
        "raw_sha256": sha256(raw_path),
        "posthoc_auditor_sha256": sha256(Path(__file__).resolve()),
        "errors": errors,
        "scope": "setup STOP consistency only; no Windows path-resolution case was audited",
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    result = audit(root)
    output = root / "results/allocation-02/STOP_AUDIT.json"
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_STOP_RECORD_INTEGRITY" else 1)
