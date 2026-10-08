"""Independent source-identity and result audit for the race construction."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
for path, identity in freeze["sources"].items():
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{freeze['base_commit']}:{path}"],
        text=True,
    ).strip()
    assert blob == identity["blob"], (path, blob)
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert hashlib.sha256(data).hexdigest() == identity["sha256"], path
assert result["main_commit"] == freeze["base_commit"]
assert result["scenario"] == {
    "queue_observation_before_final_empty": 11,
    "observation_enqueued_after_empty_return": 12,
    "drain_latest_sequence": 11,
    "drain_pending_events": False,
    "queued_after_return": 1,
    "executor_backend_sequence": 12,
    "executor_expected_sequence": 11,
}
assert result["executor"] == {
    "rejected": True,
    "reason": "latest observation sequence required before input",
    "admission_or_input_events": 0,
}
assert result["controller"]["submit_attempts"] == 1
assert result["controller"]["retry_or_accept_event_count"] == 0
assert result["controller"]["submitted_expected_sequence"] == 11
assert "SESSION_CONTINUITY_NOT_ESTABLISHED" in result["decision"]
print("audit: PASS (4 pinned source identities, final-empty miss, fail-closed executor, one controller attempt)")
