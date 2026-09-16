import json
from pathlib import Path

result = json.loads(Path(__file__).with_name("result.json").read_text())
assert result["decision"] == "PASS_CANONICAL_MEMBERSHIP_GENERATION_CAS_SCOPED"

split = result["cases"]["split_race"]
assert split["pre_validation_decision"] == "ALL_CONFIRMED"
assert split["final_membership_epoch"] == 2
assert split["final_members"] == ["A", "B", "C"]
assert split["final_active_generation"] == 2
assert split["outcome"] == "STALE_ADVANCE_EXPOSED"

race = result["cases"]["canonical_race"]
assert race["pre_validation_decision"] == "ALL_CONFIRMED"
assert race["stale_generation_attempts"] == 1
assert race["stale_sha_409s"] == 1
assert race["post_409_gets"] == 1
assert race["fresh_sha_retries"] == 0
assert race["readback_decision"] == "HOLD_MEMBERSHIP_CHANGED"
assert race["final_membership_epoch"] == 2
assert race["final_members"] == ["A", "B", "C"]
assert race["final_active_generation"] == 1

stable = result["cases"]["canonical_stable"]
assert stable["pre_validation_decision"] == "ALL_CONFIRMED"
assert stable["final_membership_epoch"] == 1
assert stable["final_members"] == ["A", "B"]
assert stable["final_active_generation"] == 2
assert stable["outcome"] == "ADVANCE"

print("PASS_CANONICAL_MEMBERSHIP_GENERATION_CAS_SCOPED")
