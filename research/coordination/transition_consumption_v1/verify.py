import json
from pathlib import Path

ROOT = Path(__file__).parent


def load(name):
    return json.loads((ROOT / name).read_text())


result = load("result.json")
reusable = load("canonical_reusable.json")
one_use = load("canonical_one_use.json")
fresh = load("canonical_fresh.json")

assert result["decision"] == "PASS_ONE_USE_CONFIRMATION_TRANSITION_SCOPED"
assert reusable["active_generation"] == 3
assert reusable["confirmation_revision"] == 1
assert result["reusable_baseline"]["same_identity_transition_count"] == 2

assert one_use["active_generation"] == 2
assert one_use["confirmation_revision"] == 1
assert one_use["confirmation_consumed"] is True
assert one_use["consumed_for_generation"] == 2
assert result["one_use_candidate"]["second_decision"] == "HOLD_CONFIRMATION_CONSUMED"
assert result["one_use_candidate"]["second_generation_write"] is False

assert fresh["active_generation"] == 3
assert fresh["confirmation_revision"] == 2
assert fresh["confirmation_consumed"] is True
assert fresh["consumed_for_generation"] == 3
assert fresh["confirmation_content_id"] == one_use["confirmation_content_id"]

assert result["totals"]["same_identity_reuse_advances_baseline"] == 1
assert result["totals"]["same_identity_reuse_advances_candidate"] == 0
assert result["totals"]["candidate_second_use_writes"] == 0
assert result["totals"]["retries"] == 0

print("PASS_VERIFY")
