"""Independent, read-only integrity and claim-scope audit for A03."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text())
result = json.loads((ROOT / "RESULT.json").read_text())
assert lock["main_base"] == "e2c58048bbaa9653f10e003bceb2e1c60e74a9da"
assert lock["candidate_commit"] == "70c76483c46108bdd70bf2fb90679d948a5f156f"
for rel, expected in lock["candidate_files"].items():
    blob = subprocess.check_output(["git", "show", f'{lock["candidate_commit"]}:{rel}'], cwd=REPO)
    assert sha(blob) == expected, (rel, sha(blob), expected)
for rel, expected in lock["shared_harness_main_files"].items():
    blob = subprocess.check_output(["git", "show", f'{lock["main_base"]}:{rel}'], cwd=REPO)
    assert sha(blob) == expected, (rel, sha(blob), expected)
assert result["status"] == "PASS_SYNTHETIC_HARNESS_ONLY"
assert result["container_tests"] == {"passed": 3, "failed": 0, "elapsed_seconds": 0.065}
assert result["authority_claimed"] is False
assert result["application_consumption_observed"] is False
assert result["live_input_tested"] is False
assert result["issue_59_exit_condition_met"] is False
assert "test-only release barrier" in result["limitations"]
print("AUDIT PASS: pinned Git objects match; result claims remain within synthetic-only scope")
