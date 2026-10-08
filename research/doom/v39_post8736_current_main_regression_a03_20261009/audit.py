#!/usr/bin/env python3
"""Saved-output verifier for the exact-main V39 regression replay."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED_COMMIT = "ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385"
EXPECTED_ALLOCATION = "V39-CURRENT-MAIN-REGRESSION-A03-FFE5292-20261009"
EXPECTED_MODULES = [
    "research.doom.test_map01_overlap_controller_v39",
    "research.doom.test_map01_overlap_controller_v39_dual_signal",
    "research.doom.test_map01_overlap_controller_v39_cover_terminal",
    "research.doom.test_map01_v39_pending_observation_drain",
    "research.doom.test_session_map01_v15",
    "research.live_control.test_executor_v13",
    "research.live_control.test_input_owner_v12_explicit_up_cancel",
]

def verify_hash_manifest(root, manifest_name="SHA256SUMS.txt"):
    """Verify that the manifest covers every package file except itself."""
    root = Path(root)
    manifest = root / manifest_name
    derived_receipt = root / "results/custody-audit/audit-v3.json"
    if not manifest.is_file() or manifest.is_symlink():
        return False
    entries = {}
    try:
        lines = manifest.read_text(encoding="utf-8").splitlines()
        for line in lines:
            match = re.fullmatch(r"([0-9a-f]{64})  (\./.+)", line)
            if not match:
                return False
            expected, listed = match.groups()
            relative = Path(listed[2:])
            if relative.is_absolute() or ".." in relative.parts or listed in entries:
                return False
            path = root / relative
            if path.is_symlink() or not path.is_file():
                return False
            entries[listed] = (expected, path)
        actual_files = {
            "./" + path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path not in (manifest, derived_receipt)
        }
        if set(entries) != actual_files:
            return False
        return all(
            hashlib.sha256(path.read_bytes()).hexdigest() == expected
            for expected, path in entries.values()
        )
    except (OSError, UnicodeError):
        return False

def verify_records(freeze, result, closure, receipts, logs):
    checks = {}
    checks["package_hash_manifest"] = verify_hash_manifest(HERE)
    checks["freeze_schema"] = freeze.get("schema") == "v39-post8736-current-main-regression-a03-freeze-v1"
    checks["result_schema"] = result.get("schema") == "v39-post8736-current-main-regression-a03-result-v1"
    checks["allocation_identity"] = freeze.get("allocation_id") == result.get("allocation_id") == EXPECTED_ALLOCATION
    checks["exact_frozen_commit"] = freeze.get("tested_commit") == result.get("tested_commit") == closure.get("source_commit") == EXPECTED_COMMIT
    checks["module_manifest"] = freeze.get("test_modules") == EXPECTED_MODULES
    parent = freeze.get("parent_replay", {})
    checks["parent_snapshot_distinct"] = parent.get("pr") == 8731 and parent.get("head") == closure.get("source_pr_head") and parent.get("tested_commit") != EXPECTED_COMMIT
    source_meta = freeze.get("static_import_closure", {})
    checks["closure_linkage"] = source_meta == {
        "source": "PR #8731 SOURCE_CLOSURE.json",
        "file_count": 73,
        "current_main_missing_paths": 0,
        "current_main_changed_blob_ids": 0,
    } and closure.get("source_pr") == 8731 and closure.get("closure_entries") == 73
    checks["closure_reconciliation"] = closure.get("status") == "PASS_IDENTITY_MATCH" and closure.get("missing_paths") == [] and closure.get("changed_blob_paths") == []
    scope = freeze.get("scope", {})
    checks["scope_consistency"] = (
        scope.get("source_and_fake_x_regression_only") is True
        and scope.get("game_model_vm_gui_or_native_input") is False
        and scope.get("live_allocation") is False
        and scope.get("formal_pass") is False
        and result.get("live_allocation") is False
        and result.get("formal_pass") is False
        and result.get("disposition") == "PASS_SOURCE_FAKE_X_REGRESSION_CURRENT_MAIN"
    )
    checks["runtime_identity"] = freeze.get("runtime", {}).get("python") == "CPython 3.12.14" and freeze.get("runtime", {}).get("platform") == "macOS arm64"
    checks["exit_receipt"] = receipts == {"normal_exit": 0, "optimized_exit": 0, "normal_tests": 107, "optimized_tests": 107}
    for mode in ("normal", "optimized"):
        log = logs[mode]
        entry = result.get(mode, {})
        checks[f"{mode}_test_receipt"] = (
            entry.get("tests") == 107 and entry.get("passed") == 107
            and entry.get("failed") == 0 and entry.get("exit") == 0
            and "Ran 107 tests" in log and log.rstrip().endswith("OK")
            and "FAILED" not in log
        )
    return checks

def main():
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    result=json.loads((HERE/'RESULT.json').read_text())
    closure=json.loads((HERE/'results/source-closure-audit.json').read_text())
    receipts=json.loads((HERE/'results/exit-codes.json').read_text())
    logs={mode:(HERE/'results'/f'{mode}.log').read_text() for mode in ('normal','optimized')}
    checks=verify_records(freeze,result,closure,receipts,logs)
    output={'schema':'v39-post8736-current-main-regression-a03-audit-v3','status':'PASS_SAVED_EVIDENCE' if all(checks.values()) else 'FAIL_SAVED_EVIDENCE','checks':checks,'check_count':len(checks),'formal_pass':False,'scope':'saved-log/source-identity custody including package hash manifest; no independent rerun'}
    print(json.dumps(output,indent=2,sort_keys=True))
    if not all(checks.values()): raise SystemExit(1)
if __name__=='__main__':main()
