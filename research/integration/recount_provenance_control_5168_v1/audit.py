"""Independent live Git-object and candidate-manifest auditor."""
from __future__ import annotations

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


def evaluate(raw: dict, fixture: Path) -> bool:
    if raw.get("candidate_exit_code") != 0 or raw.get("status") != "CONFIRM_DEFECT":
        return False
    if fixture.name != raw.get("fixture_id") or not fixture.name.startswith("recount-provenance-control-5168-01-"):
        return False
    commit = raw["synthetic_commit"]
    if git(fixture, "rev-parse", "HEAD") != commit:
        return False
    target_rel = raw["target_path"]
    entry = next((item for item in raw["candidate_manifest"]["files"]
                  if item["path"] == target_rel), None)
    if entry is None or len(raw["candidate_manifest"].get("files", [])) != 28:
        return False
    live = (fixture / target_rel).read_bytes()
    pinned_blob = git(fixture, "rev-parse", f"{commit}:{target_rel}")
    pinned = subprocess.check_output(["git", "-C", str(fixture), "cat-file", "blob", pinned_blob])
    return (entry == raw.get("candidate_target_entry") and
            entry["git_blob"] == pinned_blob == raw["pinned_git_blob"] and
            entry["sha256"] == sha(live) == raw["mutated_working_bytes_sha256"] and
            sha(pinned) == raw["pinned_git_bytes_sha256"] == raw["trusted_bytes_sha256"] and
            sha(live) != sha(pinned))


def main(raw_path: Path, fixture: Path, output: Path) -> int:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    fixture = fixture.resolve(strict=True)
    if fixture.parent != Path(tempfile.gettempdir()).resolve(strict=True):
        raise ValueError("fixture is outside the system temp root")
    passed = evaluate(raw, fixture)
    mutated_entry = json.loads(json.dumps(raw))
    target_entry = next(item for item in mutated_entry["candidate_manifest"]["files"]
                        if item["path"] == raw["target_path"])
    target_entry["sha256"] = "0" * 64
    entry_control = not evaluate(mutated_entry, fixture)
    mutated_blob = json.loads(json.dumps(raw))
    mutated_blob["candidate_target_entry"]["git_blob"] = "0" * 40
    target = next(item for item in mutated_blob["candidate_manifest"]["files"]
                  if item["path"] == raw["target_path"])
    target["git_blob"] = "0" * 40
    blob_control = not evaluate(mutated_blob, fixture)
    result = {
        "schema": "recount_provenance_control_5168_audit_v1",
        "status": "PASS_PROVENANCE_MISMATCH_REPRODUCED" if passed and entry_control and blob_control else "FAIL_AUDIT",
        "candidate_emitted_mismatched_binding": passed,
        "fixture_inspected_live": True,
        "corruption_controls": {"mutated_manifest_sha256_rejected": entry_control,
                                "mutated_git_blob_rejected": blob_control},
        "errors": [] if passed and entry_control and blob_control else ["raw/live synthetic evidence failed independent reconstruction"],
        "scope": "synthetic Git repository only; exact PR #5168 freezer copy; no historical recount",
    }
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_PROVENANCE_MISMATCH_REPRODUCED" else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py RAW.json FIXTURE_DIR AUDIT.json")
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
