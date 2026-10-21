"""Verify frozen identities and the cover-reuse decision table."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

for role in ("baseline", "candidate"):
    commit = FREEZE[f"{role}_commit"]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{commit}:{FREEZE['source']}"],
        text=True).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert blob == FREEZE[role]["blob"]
    assert hashlib.sha256(data).hexdigest() == FREEZE[role]["sha256"]

assert RESULT["baseline_commit"] == FREEZE["baseline_commit"]
assert RESULT["candidate_commit"] == FREEZE["candidate_commit"]
assert RESULT["partial_stale_action"] == {
    "baseline_reuses_cover": True, "candidate_reuses_cover": False}
assert RESULT["completed_action_control"]["candidate_reuses_cover"] is True
assert RESULT["legacy_record_control"]["candidate_reuses_cover"] is True
print("audit: PASS (frozen sources and stale/valid/legacy cover reuse outcomes)")
