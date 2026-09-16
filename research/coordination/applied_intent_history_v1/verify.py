import json
from pathlib import Path

r = json.loads(Path("result.json").read_text(encoding="utf-8"))
assert r["decision"] == "PASS_BOUNDED_APPLIED_INTENT_HISTORY_SCOPED"
assert all(r["gates"].values())
assert r["cases"]["single_slot_overwrite"]["recovery_A"] == "UNKNOWN_INTENT_NOT_RETAINED"
assert r["cases"]["bounded_history_two"]["recovery_A"] == "ALREADY_COMMITTED_SELF"
assert r["cases"]["bounded_history_conflict"]["recovery_A_changed_content"] == "CONFLICT_INTENT_CONTENT"
assert r["cases"]["bounded_history_eviction"]["recovery_A"] == "UNKNOWN_INTENT_EVICTED"
assert r["cases"]["bounded_history_eviction"]["recovery_B"] == "ALREADY_COMMITTED_SELF"
print("PASS_VERIFY")
