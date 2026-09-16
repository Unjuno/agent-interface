import json
from pathlib import Path

ROOT = Path(__file__).parent

with open(ROOT / "result.json", "r", encoding="utf-8") as f:
    result = json.load(f)

assert result["decision"] == "PASS_CONTENT_BOUND_CONSUMED_TRANSITION_READBACK_SCOPED"
assert result["cases"]["naive_reissue"]["duplicate_advance"] is True
assert result["cases"]["naive_reissue"]["final_generation"] == 3
assert result["cases"]["exact_readback"]["recovery_decision"] == "ALREADY_COMMITTED_SELF"
assert result["cases"]["exact_readback"]["refresh_writes"] == 0
assert result["cases"]["exact_readback"]["replay_writes"] == 0
assert result["cases"]["exact_readback"]["final_generation"] == 2
assert result["cases"]["readback_unavailable"]["recovery_decision"] == "UNKNOWN_COMMIT"
assert result["cases"]["readback_unavailable"]["refresh_writes"] == 0
assert result["cases"]["readback_unavailable"]["replay_writes"] == 0
assert result["cases"]["readback_unavailable"]["final_generation"] == 2
assert result["totals"]["candidate_duplicate_advances"] == 0
assert result["totals"]["fresh_sha_retries"] == 0

naive = json.loads((ROOT / "canonical_naive.json").read_text())
exact = json.loads((ROOT / "canonical_exact.json").read_text())
unavailable = json.loads((ROOT / "canonical_unavailable.json").read_text())
assert naive["active_generation"] == 3
assert exact["active_generation"] == 2 and exact["confirmation_consumed"] is True
assert unavailable["active_generation"] == 2 and unavailable["confirmation_consumed"] is True

print("PASS_VERIFY")
