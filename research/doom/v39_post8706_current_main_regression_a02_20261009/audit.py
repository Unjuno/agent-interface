#!/usr/bin/env python3
"""Verify frozen source blobs and retained regression test logs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text())
    result = json.loads((PACKAGE / "RESULT.json").read_text())
    closure = json.loads((PACKAGE / "SOURCE_CLOSURE.json").read_text())
    expected = freeze["expected_test_count"]
    log_checks = {}
    for name in ("normal", "optimized"):
        path = PACKAGE / f"{name}.log"
        text = path.read_text()
        counts = re.findall(r"Ran (\d+) tests?", text)
        ok = bool(counts) and int(counts[-1]) == expected and text.rstrip().endswith("OK")
        if not ok:
            raise SystemExit(f"FAIL: {name} log does not show {expected} passing tests")
        log_checks[name] = {"tests": int(counts[-1]), "status": "PASS", "sha256": sha256(path)}

    changed = []
    for item in closure["files"]:
        current_spec = f"{freeze['tested_commit']}:{item['path']}"
        baseline_spec = f"{freeze['baseline_commit']}:{item['path']}"
        current_blob = subprocess.check_output(
            ["git", "rev-parse", "--verify", current_spec], cwd=ROOT, text=True).strip()
        baseline_blob = subprocess.check_output(
            ["git", "rev-parse", "--verify", baseline_spec], cwd=ROOT, text=True).strip()
        if current_blob != item["git_blob"] or baseline_blob != item["baseline_blob"]:
            raise SystemExit(f"FAIL: frozen source blob mismatch for {item['path']}")
        actually_changed = current_blob != baseline_blob
        if item["changed_since_baseline"] != actually_changed:
            raise SystemExit(f"FAIL: incorrect baseline comparison for {item['path']}")
        if actually_changed:
            changed.append(item["path"])
    expected_delta = ["research/live_control/test_input_owner_v12_explicit_up_cancel.py"]
    if len(closure["files"]) != 73 or changed != expected_delta:
        raise SystemExit("FAIL: unexpected static import closure delta")
    if result["tested_commit"] != freeze["tested_commit"]:
        raise SystemExit("FAIL: result/freeze source commit mismatch")

    audit = {
        "schema": "v39-post8706-current-main-regression-a02-audit-v2",
        "status": "PASS_SOURCE_AND_LOG_RECONCILIATION",
        "tested_commit": freeze["tested_commit"],
        "static_import_closure_files": len(closure["files"]),
        "changed_paths_since_baseline": changed,
        "production_source_changes_since_baseline": 0,
        "test_logs": log_checks,
        "scope": "Verifies recorded test logs and Git blob identities; does not independently prove live control behavior",
    }
    output = PACKAGE / "AUDIT_V2.json"
    if output.exists():
        raise SystemExit("STOP: refusing to overwrite existing audit")
    output.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
