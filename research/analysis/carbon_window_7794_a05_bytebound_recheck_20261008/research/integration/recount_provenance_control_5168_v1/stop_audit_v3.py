"""Final STOP-only integrity audit; separates working bytes from Git blobs."""
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


def audit(raw: dict, raw_bytes: bytes, fixture: Path) -> dict:
    errors = []
    if fixture.parent != Path(tempfile.gettempdir()).resolve(strict=True):
        errors.append("fixture outside temp root")
    if fixture.name != raw.get("fixture_id"):
        errors.append("fixture identity mismatch")
    if raw.get("candidate_exit_code") != 1 or raw.get("candidate_manifest") is not None:
        errors.append("not the retained no-manifest exit-1 outcome")
    if len(raw.get("candidate_stderr_sha256", "")) != 64:
        errors.append("stderr digest missing")
    commit = raw["synthetic_commit"]
    if git(fixture, "rev-parse", "HEAD") != commit:
        errors.append("commit identity mismatch")
    tracked = git(fixture, "ls-tree", "-r", "--name-only", commit).splitlines()
    results = [name for name in tracked if name.endswith("result.json")]
    call_ids = [json.loads(subprocess.check_output(["git", "-C", str(fixture), "show", f"{commit}:{name}"]))["call_id"]
                for name in results]
    if len(tracked) != 28 or len(results) != 14 or len(set(call_ids)) != 14:
        errors.append("committed synthetic inventory mismatch")
    target = raw["target_path"]
    live = (fixture / target).read_bytes()
    prefix = live[:-len(SUFFIX)] if live.endswith(SUFFIX) else b""
    blob = git(fixture, "rev-parse", f"{commit}:{target}")
    pinned = subprocess.check_output(["git", "-C", str(fixture), "cat-file", "blob", blob])
    live_status = git(fixture, "status", "--porcelain").splitlines()
    if not live.endswith(SUFFIX) or sha(prefix) != raw.get("trusted_bytes_sha256"):
        errors.append("frozen working-tree mutation mismatch")
    if sha(live) != raw.get("mutated_working_bytes_sha256"):
        errors.append("mutated working bytes hash mismatch")
    if blob != raw.get("pinned_git_blob") or sha(pinned) != raw.get("pinned_git_bytes_sha256"):
        errors.append("pinned object mismatch")
    if sha(live) == sha(pinned):
        errors.append("mutated live bytes unexpectedly equal pinned object")
    if len(live_status) != 1 or target not in live_status[0]:
        errors.append("unexpected synthetic worktree changes")
    autocrlf = git(fixture, "config", "core.autocrlf") or "unset"
    controls = {
        "nonzero_candidate_exit_preserved": raw.get("candidate_exit_code") == 1,
        "fixture_id_matches_live_tree": fixture.name == raw.get("fixture_id"),
    }
    if not all(controls.values()):
        errors.append("STOP identity control failed")
    return {
        "schema": "recount_provenance_control_5168_stop_audit_v3",
        "status": "PASS_STOP_RECORD_INTEGRITY" if not errors else "FAIL_STOP_AUDIT",
        "disposition": "STOP_RUNNER_STDERR_NOT_RETAINED; no candidate behavior conclusion",
        "raw_sha256": sha(raw_bytes), "live_fixture_inspected": True,
        "tracked_files": len(tracked), "raw_result_files": len(results),
        "unique_call_ids": len(set(call_ids)), "core_autocrlf": autocrlf,
        "pre_mutation_worktree_bytes_equal_git_blob": sha(prefix) == sha(pinned),
        "candidate_reinvoked": False, "corruption_controls": controls,
        "errors": errors,
    }


def main(raw_path: Path, fixture: Path, output: Path) -> int:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    result = audit(raw, raw_bytes, fixture.resolve(strict=True))
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_STOP_RECORD_INTEGRITY" else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: stop_audit_v3.py RAW.json FIXTURE_DIR STOP_AUDIT_V3.json")
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
