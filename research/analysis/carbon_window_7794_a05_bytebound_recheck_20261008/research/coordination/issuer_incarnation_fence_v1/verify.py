import json
from pathlib import Path

r = json.loads(Path("result.json").read_text())
assert r["decision"] == "PASS_ISSUER_INCARNATION_FENCE_SCOPED"
assert r["formal_reruns"] == 0
assert all(r["gates"].values())
assert r["cases"]["seq_reset_baseline_old_replay"]["classification"] == "NEW_INTENT_ALLOWED"
assert r["cases"]["seq_reset_baseline_old_replay"]["apply"] == "APPLIED"
assert r["cases"]["incarnation_old_replay"]["classification"] == "STALE_ISSUER_INCARNATION"
assert r["cases"]["incarnation_old_replay"]["transition_writes_after_replay_attempt"] == 0
assert r["cases"]["incarnation_fresh_restart"]["classification"] == "NEW_INTENT_ALLOWED"
assert r["cases"]["incarnation_fresh_restart"]["apply"] == "APPLIED"
assert r["cases"]["incarnation_retained_conflict"]["classification"] == "CONFLICT_INTENT_CONTENT"
print("PASS_VERIFY")
