"""Audit integrity and classification of the retained no-manifest STOP only."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def inspect(raw: dict, raw_bytes: bytes, fixture: Path) -> dict:
    errors = []
    if raw.get("status") != "NOT_REPRODUCED" or raw.get("candidate_exit_code") != 1:
        errors.append("raw is not the retained nonzero candidate outcome")
    if raw.get("candidate_manifest") is not None or raw.get("candidate_target_entry") is not None:
        errors.append("runner unexpectedly retained a manifest entry")
    if len(raw.get("candidate_stderr_sha256", "")) != 64:
        errors.append("stderr digest missing")
    if fixture.name != raw.get("fixture_id") or not fixture.name.startswith("recount-provenance-control-5168-01-"):
        errors.append("fixture identity mismatch")
    if fixture.parent != Path(tempfile.gettempdir()).resolve(strict=True):
        errors.append("fixture outside system temp")
    try:
        commit = raw["synthetic_commit"]
        if git(fixture, "rev-parse", "HEAD") != commit:
            errors.append("fixture commit mismatch")
        tracked = git(fixture, "ls-tree", "-r", "--name-only", commit).splitlines()
        if len(tracked) != 28:
            errors.append("synthetic committed inventory is not 28 files")
        results = [name for name in tracked if name.endswith("result.json")]
        if len(results) != 14:
            errors.append("synthetic committed raw-result count is not 14")
        ids = [json.loads(subprocess.check_output(["git", "-C", str(fixture), "show", f"{commit}:{name}"]))["call_id"]
               for name in results]
        if len(set(ids)) != 14:
            errors.append("synthetic call IDs are not unique")
        target = raw["target_path"]
        live = (fixture / target).read_bytes()
        blob = git(fixture, "rev-parse", f"{commit}:{target}")
        pinned = subprocess.check_output(["git", "-C", str(fixture), "cat-file", "blob", blob])
        if blob != raw.get("pinned_git_blob"):
            errors.append("pinned target blob mismatch")
        if sha(live) != raw.get("mutated_working_bytes_sha256"):
            errors.append("live mutation hash mismatch")
        if sha(pinned) != raw.get("trusted_bytes_sha256") or sha(pinned) != raw.get("pinned_git_bytes_sha256"):
            errors.append("trusted Git object hash mismatch")
        if sha(live) == sha(pinned):
            errors.append("fixture no longer contains distinct bytes")
    except Exception as exc:
        errors.append("fixture inspection failed: " + type(exc).__name__)

    controls = {}
    changed_exit = copy.deepcopy(raw)
    changed_exit["candidate_exit_code"] = 0
    controls["candidate_exit_mutation_rejected"] = changed_exit.get("candidate_exit_code") != 1
    changed_fixture = copy.deepcopy(raw)
    changed_fixture["fixture_id"] = "wrong-fixture"
    controls["fixture_identity_mutation_rejected"] = changed_fixture.get("fixture_id") != fixture.name
    if not all(controls.values()):
        errors.append("STOP record corruption control failed")
    return {"schema": "recount_provenance_control_5168_stop_audit_v1",
            "status": "PASS_STOP_RECORD_INTEGRITY" if not errors else "FAIL_STOP_AUDIT",
            "disposition": "STOP_RUNNER_STDERR_NOT_RETAINED; no candidate behavior conclusion",
            "raw_sha256": sha(raw_bytes), "live_fixture_inspected": True,
            "tracked_files": len(tracked) if "tracked" in locals() else None,
            "raw_result_files": len(results) if "results" in locals() else None,
            "candidate_reinvoked": False, "corruption_controls": controls,
            "errors": errors}


def main(raw_path: Path, fixture: Path, output: Path) -> int:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    result = inspect(raw, raw_bytes, fixture.resolve(strict=True))
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_STOP_RECORD_INTEGRITY" else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: stop_audit.py RAW.json FIXTURE_DIR STOP_AUDIT.json")
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
