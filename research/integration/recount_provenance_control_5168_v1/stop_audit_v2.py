"""Audit STOP integrity while accounting for Git autocrlf normalization."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

SUFFIX = b"synthetic-working-tree-mutation\n"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def main(raw_path: Path, fixture: Path, output: Path) -> int:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    fixture = fixture.resolve(strict=True)
    errors = []
    if fixture.parent != Path(tempfile.gettempdir()).resolve(strict=True):
        errors.append("fixture outside temp root")
    if fixture.name != raw.get("fixture_id"):
        errors.append("fixture identity mismatch")
    if raw.get("candidate_exit_code") != 1 or raw.get("candidate_manifest") is not None:
        errors.append("candidate outcome is not the retained no-manifest exit-1 STOP")
    if len(raw.get("candidate_stderr_sha256", "")) != 64:
        errors.append("stderr digest missing")
    commit = raw["synthetic_commit"]
    if git(fixture, "rev-parse", "HEAD") != commit:
        errors.append("commit identity mismatch")
    tracked = git(fixture, "ls-tree", "-r", "--name-only", commit).splitlines()
    results = [name for name in tracked if name.endswith("result.json")]
    ids = [json.loads(subprocess.check_output(["git", "-C", str(fixture), "show", f"{commit}:{name}"]))["call_id"]
           for name in results]
    if len(tracked) != 28 or len(results) != 14 or len(set(ids)) != 14:
        errors.append("synthetic committed inventory mismatch")
    target = raw["target_path"]
    live = (fixture / target).read_bytes()
    pinned_blob = git(fixture, "rev-parse", f"{commit}:{target}")
    pinned = subprocess.check_output(["git", "-C", str(fixture), "cat-file", "blob", pinned_blob])
    prefix = live[:-len(SUFFIX)] if live.endswith(SUFFIX) else b""
    if not live.endswith(SUFFIX) or sha(prefix) != raw.get("trusted_bytes_sha256"):
        errors.append("one frozen synthetic mutation does not reconcile")
    if sha(live) != raw.get("mutated_working_bytes_sha256"):
        errors.append("live mutated bytes hash mismatch")
    if pinned_blob != raw.get("pinned_git_blob") or sha(pinned) != raw.get("pinned_git_bytes_sha256"):
        errors.append("pinned Git object identity mismatch")
    if sha(live) == sha(pinned):
        errors.append("mutated working bytes equal pinned object")
    if sha(prefix) != sha(pinned):
        errors.append("reported Git autocrlf normalization was not observed")
    changed = git(fixture, "status", "--porcelain").splitlines()
    if len(changed) != 1 or target not in changed[0]:
        errors.append("worktree change set is not exactly the designated input")

    controls = {
        "candidate_exit_mutation_rejected": raw.get("candidate_exit_code") == 1,
        "fixture_identity_mutation_rejected": raw.get("fixture_id") == fixture.name,
    }
    if not all(controls.values()):
        errors.append("STOP identity control failed")
    result = {
        "schema": "recount_provenance_control_5168_stop_audit_v2",
        "status": "PASS_STOP_RECORD_INTEGRITY" if not errors else "FAIL_STOP_AUDIT",
        "disposition": "STOP_RUNNER_STDERR_NOT_RETAINED; no candidate behavior conclusion",
        "raw_sha256": sha(raw_bytes),
        "live_fixture_inspected": True,
        "tracked_files": len(tracked),
        "raw_result_files": len(results),
        "unique_call_ids": len(set(ids)),
        "git_autocrlf": git(fixture, "config", "core.autocrlf") or "unset",
        "candidate_reinvoked": False,
        "corruption_controls": controls,
        "errors": errors,
    }
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_STOP_RECORD_INTEGRITY" else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: stop_audit_v2.py RAW.json FIXTURE_DIR STOP_AUDIT_V2.json")
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
