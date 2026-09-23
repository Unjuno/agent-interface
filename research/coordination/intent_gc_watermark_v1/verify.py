import json
from pathlib import Path

r = json.loads(Path("result.json").read_text(encoding="utf-8"))
assert r["decision"] == "PASS_SCALAR_INTENT_RETIREMENT_WATERMARK_SCOPED"
assert r["formal_reruns"] == 0
assert all(r["gates"].values())
assert r["cases"]["id_only_after_gc"]["old_exact_A_seq1"] == "NEW_INTENT_ALLOWED"
assert r["cases"]["id_only_after_gc"]["same_instance_changed_content_apply"] == "APPLIED"
assert r["cases"]["watermark_expired_replay"]["old_exact_A_seq1"] == "EXPIRED_INTENT"
assert r["cases"]["watermark_expired_replay"]["transition_writes_after_replay_attempt"] == 0
assert r["cases"]["watermark_fresh_reuse"]["fresh_label_A_seq4"] == "NEW_INTENT_ALLOWED"
assert r["cases"]["watermark_fresh_reuse"]["fresh_apply"] == "APPLIED"
assert r["cases"]["watermark_retained_conflict"]["B_seq2_changed_content"] == "CONFLICT_INTENT_CONTENT"
assert len(r["cases"]["watermark_fresh_reuse"]["snapshot"]["history"]) == 2
assert r["cases"]["watermark_fresh_reuse"]["snapshot"]["retirement_state_shape"] == "scalar"
print("PASS_VERIFY")
