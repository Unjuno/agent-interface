import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
result = json.loads((ROOT / "result.json").read_text())

assert result["decision"] == "PASS_DURABLE_TRANSITION_INTENT_READBACK_SCOPED"
exact = result["cases"]["exact_bytes_metadata_changed"]
intent = result["cases"]["intent_bound_metadata_changed"]
conflict = result["cases"]["intent_content_conflict"]

assert exact["classification"] == "UNKNOWN_CONTENT_MISMATCH"
assert exact["expected_after_blob"] != exact["observed_blob"]
assert exact["active_generation"] == 2
assert exact["recovery_writes"] == 0

assert intent["classification"] == "ALREADY_COMMITTED_SELF"
assert intent["applied_transition_matches_requested"] is True
assert intent["active_generation"] == 2
assert intent["recovery_writes"] == 0

assert conflict["classification"] == "CONFLICT_INTENT_CONTENT"
assert conflict["same_intent_id"] is True
assert conflict["applied_transition_matches_requested"] is False
assert conflict["recovery_writes"] == 0

counts = result["counts"]
assert counts["successful_measured_writes"] == 5
assert counts["classifier_gets"] == 3
assert counts["recovery_refresh_writes"] == 0
assert counts["recovery_replay_writes"] == 0
assert counts["retries"] == 0

print("PASS_VERIFY")
