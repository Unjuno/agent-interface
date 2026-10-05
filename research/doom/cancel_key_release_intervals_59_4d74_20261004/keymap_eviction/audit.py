"""Audit the pinned keyup-after-keysym-removal construction result."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())
RESULT = json.loads((ROOT / "RESULT.json").read_text())

def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()

def sha(path):
    return sha_bytes(path.read_bytes())

baseline = subprocess.check_output([
    "git", "show", f"{FREEZE['baseline_commit']}:{FREEZE['source_path']}"])
checks = {
    "result_file_hash": sha(ROOT / "RESULT.json") == FREEZE["result_sha256"],
    "baseline_source_commit_hash": (
        sha_bytes(baseline) == FREEZE["baseline_source_sha256"]),
    "baseline_source_copy_hash": (
        sha(ROOT / "baseline" / "input_owner_v12.py")
        == FREEZE["baseline_source_sha256"]),
    "candidate_source_copy_hash": (
        sha(ROOT / "candidate" / "input_owner_v12.py")
        == FREEZE["candidate_source_sha256"]),
    "candidate_source_current_hash": (
        sha(REPO / FREEZE["source_path"]) == FREEZE["candidate_source_sha256"]),
    "test_copy_hash": (
        sha(ROOT / "test_input_owner_v12_keyup_after_keysym_removal.py")
        == FREEZE["test_sha256"]),
    "test_current_hash": (
        sha(REPO / FREEZE["test_path"]) == FREEZE["test_sha256"]),
    "runner_hash": sha(ROOT / "run_case.py") == FREEZE["runner_sha256"],
    "ordered_runner_hash": (
        sha(ROOT / "run_ordered_suite.py") == FREEZE["ordered_runner_sha256"]),
    "audit_script_hash": sha(ROOT / "audit.py") == FREEZE["audit_script_sha256"],
    "baseline_preserves_held_key_and_fails": (
        (ROOT / "baseline.exit.txt").read_text().strip() == "1"
        and "ValueError('key unavailable on input owner')"
            in (ROOT / "baseline.stdout.txt").read_text()
        and "'keys_down': [87]" in (ROOT / "baseline.stdout.txt").read_text()),
    "candidate_regression_pass": (
        (ROOT / "candidate.exit.txt").read_text().strip() == "0"
        and "Ran 1 test" in (ROOT / "candidate.stdout.txt").read_text()
        and "OK" in (ROOT / "candidate.stdout.txt").read_text()),
    "ordered_adjacent_suite_pass": (
        (ROOT / "ordered.exit.txt").read_text().strip() == "0"
        and "Ran 24 tests" in (ROOT / "ordered.stdout.txt").read_text()
        and "OK" in (ROOT / "ordered.stdout.txt").read_text()),
    "baseline_and_candidate_result_match_freeze": (
        RESULT["baseline_source_sha256"] == FREEZE["baseline_source_sha256"]
        and RESULT["candidate_source_sha256"] == FREEZE["candidate_source_sha256"]
        and RESULT["test_sha256"] == FREEZE["test_sha256"]),
    "raw_output_hashes": (
        sha(ROOT / "baseline.stdout.txt") == FREEZE["baseline_output_sha256"]
        and sha(ROOT / "candidate.stdout.txt") == FREEZE["candidate_output_sha256"]
        and sha(ROOT / "ordered.stdout.txt") == FREEZE["ordered_output_sha256"]),
}
out = {"schema": "keyup-after-keysym-removal-audit-v1",
       "checks": checks, "pass": all(checks.values())}
print(json.dumps(out, indent=2, sort_keys=True))
if not out["pass"]:
    raise SystemExit(1)
