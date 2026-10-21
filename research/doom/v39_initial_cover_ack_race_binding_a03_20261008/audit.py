"""Verify source pins and each recorded initial-cover recovery decision gate."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
for role, key in (("baseline", "baseline_commit"), ("candidate", "candidate_commit")):
    commit = FREEZE[key]
    path, expected = next(iter(FREEZE["sources"][role].items()))
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{commit}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert blob == expected["blob"]
    assert hashlib.sha256(data).hexdigest() == expected["sha256"]

assert RESULT["baseline_commit"] == FREEZE["baseline_commit"]
assert RESULT["candidate_commit"] == FREEZE["candidate_commit"]
assert RESULT["baseline"] == {
    "latest_sequence": 11, "pending_events": False, "queued_late_sequence": 12,
}
assert RESULT["candidate"]["wrapper_wired_into_main"] is True
assert RESULT["candidate"]["sequence_bound_before_submit"] == 11
assert RESULT["candidate"]["fresh_sequence_after_rejection"] == 12
assert RESULT["candidate"]["late_hard_crossing"] == "health:below_hard_minimum"
assert RESULT["candidate"]["old_cover_policy"] == "discarded_until_fresh_plan"
assert RESULT["candidate"]["queue_empty"] is True
assert RESULT["candidate"]["cover_retried"] is False
print("audit: PASS (baseline/candidate source identities and ACK sequence-binding gates)")
