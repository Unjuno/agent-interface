"""Re-audit the alias result against its archived candidate source."""
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
archived_candidate = ROOT / "candidate" / "input_owner_v12.py"
checks = {
    "baseline_source_hash": sha_bytes(baseline) == FREEZE["baseline_source_sha256"],
    "archived_candidate_source_hash": (
        sha(archived_candidate) == FREEZE["candidate_source_sha256"]),
    "test_hash": sha(REPO / FREEZE["test_path"]) == FREEZE["test_sha256"],
    "ordered_runner_hash": (
        sha(ROOT / "run_ordered_suite.py")
        == FREEZE["ordered_runner_sha256"]),
    "baseline_expected_failure": (
        (ROOT / "baseline.exit.txt").read_text().strip() == "1"
        and "Items in the second set but not the first:"
        in (ROOT / "baseline.stdout.txt").read_text()
        and "87" in (ROOT / "baseline.stdout.txt").read_text()),
    "candidate_pass": (
        (ROOT / "candidate.exit.txt").read_text().strip() == "0"
        and "Ran 1 test" in (ROOT / "candidate.stdout.txt").read_text()
        and "OK" in (ROOT / "candidate.stdout.txt").read_text()),
    "ordered_suite_pass": (
        (ROOT / "ordered.exit.txt").read_text().strip() == "0"
        and "Ran 22 tests" in (ROOT / "ordered.stdout.txt").read_text()
        and "OK" in (ROOT / "ordered.stdout.txt").read_text()),
    "result_matches_freeze": (
        RESULT["candidate_source_sha256"] == FREEZE["candidate_source_sha256"]),
    "original_audit_unchanged": (
        sha(ROOT / "audit.py") == FREEZE["audit_script_sha256"]
        and sha(ROOT / "AUDIT.json") == FREEZE["audit_result_sha256"]),
}
out = {"schema": "unmatched-keyup-alias-audit-v2",
       "checks": checks, "pass": all(checks.values())}
print(json.dumps(out, indent=2, sort_keys=True))
if not out["pass"]:
    raise SystemExit(1)
