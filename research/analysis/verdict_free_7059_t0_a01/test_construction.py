#!/usr/bin/env python3
"""Development-only checks using authored records before the formal freeze."""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import audit
import build_fixture
import candidate

fixture = build_fixture.make_fixture()
projected = candidate.run({"cases": fixture["cases"]})
assert projected["attempt_count"] == 10
assert all(len(a["reviewers"]) == 2 for a in projected["attempts"])
groups = {}
for attempt in fixture["cases"]:
    groups.setdefault(attempt["case_id"], []).append(attempt)
truth = {x["case_id"]: x for x in fixture["auditor_truth"]}
observed = {key: audit.classify(rows, truth[key]["effect_truth"]) for key, rows in groups.items()}
expected = {x["case_id"]: x["expected_ledger_class"] for x in fixture["auditor_truth"]}
assert observed == expected, (observed, expected)
assert audit.check_attempt(fixture["cases"][-1]) == "HOLD_MISSING_TOOL_LOG"
early = fixture["cases"][0].copy()
early["reviewers"] = [dict(r) for r in early["reviewers"]]
early["reviewers"][0]["first_peer_content_seq"] = early["reviewers"][0]["commit_seq"]
assert audit.check_attempt(early) == "HOLD_PEER_CONTENT_PRECOMMIT"
cap = fixture["cases"][0].copy()
cap["reviewers"] = [dict(r) for r in cap["reviewers"]]
cap["per_reviewer_cap"] = 0
assert audit.check_attempt(cap) == "HOLD_CAP_EXCEEDED"
print(f"construction PASS: {len(observed)} authored case patterns; {projected['attempt_count']} condition opportunities")
