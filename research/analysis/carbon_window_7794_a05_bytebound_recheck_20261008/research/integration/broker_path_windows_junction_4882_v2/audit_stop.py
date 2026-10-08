"""Validate allocation-03 STOP integrity only; does not audit path behavior."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path) -> dict:
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    run = json.loads((root / "results/allocation-03/RUN_RECORD.json").read_text(encoding="utf-8"))
    raw_path = root / "results/allocation-03/RAW.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    cleanup = json.loads((root / "results/allocation-03/CLEANUP.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("allocation") != freeze.get("allocation") or run.get("allocation") != freeze.get("allocation"):
        errors.append("allocation_identity")
    if raw.get("source_main") != freeze.get("source_main"):
        errors.append("source_main")
    if raw.get("status") != "STOP_SETUP_JUNCTION_UNAVAILABLE" or raw.get("rows") != []:
        errors.append("stop_disposition")
    if raw.get("fixture", {}).get("setup", {}).get("returncode") != 1:
        errors.append("setup_receipt")
    if run.get("runner_invocations") != 1 or run.get("runner_exit_code") != 1 or run.get("path_case_rows") != 0:
        errors.append("run_record")
    if run.get("raw_sha256") != sha(raw_path):
        errors.append("raw_hash")
    for name, expected in freeze["files"].items():
        if sha(root / name) != expected:
            errors.append(name + "_freeze_hash")
    if cleanup.get("junctions_created") is not False or cleanup.get("fixture_path_published") is not False:
        errors.append("cleanup_scope")
    return {"schema": "broker_path_windows_junction_4882_v2_stop_audit_v1",
            "status": "PASS_STOP_RECORD_INTEGRITY" if not errors else "FAIL_STOP_RECORD_INTEGRITY",
            "errors": errors, "raw_sha256": sha(raw_path),
            "scope": "allocation-03 STOP integrity only; no path resolution behavior audited"}


if __name__ == "__main__":
    import json
    root = Path(__file__).resolve().parent
    result = audit(root)
    out = root / "results/allocation-03/STOP_AUDIT.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_STOP_RECORD_INTEGRITY" else 1)
