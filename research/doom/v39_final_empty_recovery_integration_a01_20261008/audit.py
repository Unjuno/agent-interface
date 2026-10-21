"""Independent checks for the frozen source identities and recorded result."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

for role, commit_key in (("baseline", "baseline_commit"),
                         ("candidate", "candidate_commit")):
    commit = FREEZE[commit_key]
    for path, expected in FREEZE["sources"][role].items():
        blob = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", f"{commit}:{path}"], text=True
        ).strip()
        data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
        assert blob == expected["blob"], (role, path, blob)
        assert hashlib.sha256(data).hexdigest() == expected["sha256"], (role, path)

assert RESULT["baseline_commit"] == FREEZE["baseline_commit"]
assert RESULT["candidate_commit"] == FREEZE["candidate_commit"]
assert RESULT["scenario"] == {
    "drained_latest_sequence": 11,
    "pending_events_reported": False,
    "late_sequence_left_queued": 12,
}
assert RESULT["candidate"]["recovered_latest_sequence"] == 12
assert RESULT["candidate"]["controller_recovery_and_discard_wiring_verified"] is True
assert RESULT["candidate"]["queued_late_event_consumed"] is True
assert RESULT["candidate"]["stale_candidate_authority"] is False
assert RESULT["candidate"]["fresh_decision_required"] is True
assert RESULT["candidate"]["retry_or_input_emitted"] is False
assert "at the helper boundary" in RESULT["decision"]
print("audit: PASS (frozen baseline/candidate source identities and bounded recovery result)")
