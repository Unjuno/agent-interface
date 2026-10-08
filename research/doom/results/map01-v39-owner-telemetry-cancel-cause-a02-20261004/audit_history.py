"""Verify A01/A02 frozen artifacts after the parent owner source was renamed."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
A01 = HERE.parent / "map01-v39-owner-telemetry-cancel-cause-a01-20261004"
CANDIDATE_COMMIT = "f5847058846755c5622631758edc7cdfd9bc2b77"
BASE_COMMIT = "0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2"
CURRENT_PARENT = "28bfa088c05d8a28ebe040c481e14e23f1aa5b2b"


def sha(data): return hashlib.sha256(data).hexdigest()


def git_bytes(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"])


def verify_manifest(manifest, candidate_commit):
    checked = 0
    for line in manifest.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        if relative == "research/live_control/input_owner_v12.py":
            data = git_bytes(candidate_commit, relative)
        else:
            data = (ROOT / relative).read_bytes()
        assert sha(data) == expected, relative
        checked += 1
    return checked


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    raw = json.loads((HERE / "RAW.json").read_text())
    audit = json.loads((HERE / "AUDIT.json").read_text())
    parent = git_bytes(BASE_COMMIT, "research/live_control/input_owner_v12.py")
    candidate = git_bytes(CANDIDATE_COMMIT, "research/live_control/input_owner_v12.py")
    current = git_bytes(CURRENT_PARENT, "research/live_control/input_owner_v13.py")
    assert sha(parent) == freeze["parent_owner_sha256"] == raw["base_owner_sha256"]
    assert sha(candidate) == freeze["candidate_owner_sha256"] == raw["candidate_owner_sha256"]
    assert audit["status"] == "PASS_AUDIT" and audit["checks"] == 24
    assert "active.cancel.is_set()" in current.decode()
    assert "input_owner_v11 import InputOwner as Previous" in current.decode()
    a01_count = verify_manifest(A01 / "SHA256SUMS.txt", CANDIDATE_COMMIT)
    a02_count = verify_manifest(HERE / "SHA256SUMS.txt", CANDIDATE_COMMIT)
    result = {"status": "PASS_HISTORY_AUDIT", "a01_manifest_entries": a01_count,
              "a02_manifest_entries": a02_count,
              "historical_candidate_sha256": sha(candidate),
              "latest_parent_owner_sha256": sha(current),
              "candidate_rerun": False}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
