#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parent
result = json.loads((root / "result.json").read_text())
assert result["decision"] == "PASS_EVIDENCE_BOUND_RECLAIM_SCOPED"
cases = result["cases"]
assert cases["elapsed_only"]["policy"] == "HOLD_UNKNOWN"
assert cases["elapsed_only"]["github_updates"] == 0
assert cases["owner_relinquish_exact"]["policy"] == "ALLOW_RECLAIM"
assert cases["owner_relinquish_exact"]["late_generation_one_status"] == 409
assert cases["owner_relinquish_exact"]["late_writer_policy"] == "FENCED_STALE"
assert cases["owner_relinquish_exact"]["fresh_sha_retries"] == 0
assert cases["supervisor_terminal_exact"]["policy"] == "ALLOW_RECLAIM"
assert cases["supervisor_terminal_exact"]["late_generation_one_status"] == 409
assert cases["supervisor_terminal_exact"]["late_writer_policy"] == "FENCED_STALE"
assert cases["supervisor_terminal_exact"]["fresh_sha_retries"] == 0
assert cases["stale_relinquish_generation"]["policy"] == "HOLD_UNKNOWN"
assert cases["stale_relinquish_generation"]["github_updates"] == 0
assert cases["unbound_terminal"]["policy"] == "HOLD_UNKNOWN"
assert cases["unbound_terminal"]["github_updates"] == 0
assert result["totals"] == {
    "positive_reclaim_commits": 2,
    "negative_case_writes": 0,
    "late_generation_one_attempts": 2,
    "stale_sha_409s": 2,
    "fresh_sha_retries": 0,
}
print("PASS_EVIDENCE_BOUND_RECLAIM_SCOPED")
