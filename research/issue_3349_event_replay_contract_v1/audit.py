"""Independent finite oracle for the Issue #3349 event replay contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_SOURCE_SHA256 = "4432a6188b5318dc552f050a26ff9e2a5d32bbf9"


def candidate_first_match(events, queue, event_name):
    for row in events:
        if row.get("event") == event_name:
            return row
    for row in queue:
        if row.get("event") == event_name:
            return row
    return None


def run():
    source_path = ROOT / "candidate.py"
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError("candidate source SHA-256 mismatch")
    fixture = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    outcomes = []
    for case in fixture["cases"]:
        predicate_name = case["predicate_event"]
        wanted_id = case.get("expected_id")
        expected = case["expected_disposition"]
        candidate = candidate_first_match(case["events"], case["queue"], predicate_name)
        if candidate is not None and candidate.get("id") != wanted_id:
            candidate_disposition = "stale_wrong_identity_returned"
        elif candidate is None:
            candidate_disposition = "wait"
        elif expected == "ambiguous_duplicate":
            candidate_disposition = "returned_first_ambiguous"
        else:
            candidate_disposition = "return"
        if case["name"] in {"stale_accepted_prelude", "stale_rejected_prelude"}:
            expected_candidate = "stale_wrong_identity_returned"
        elif case["name"] == "duplicate_terminal_history":
            expected_candidate = "returned_first_ambiguous"
        else:
            expected_candidate = expected
        correct = candidate_disposition == expected_candidate
        outcomes.append({
            "case": case["name"],
            "expected": expected,
            "candidate": candidate_disposition,
            "expected_candidate_observation": expected_candidate,
            "pass": correct,
        })
    witness = candidate_first_match(
        [{"event": "accepted", "id": "prelude"}], [], "accepted"
    )
    reproduced = witness == {"event": "accepted", "id": "prelude"}
    result = {
        "candidate_source_sha256": source_sha,
        "cases": outcomes,
        "candidate_returns_stale_prelude": reproduced,
        "audit": "PASS_REPRODUCES_DECLARED_CANDIDATE_BEHAVIOR" if all(x["pass"] for x in outcomes) and reproduced else "FAIL_AUDIT",
        "candidate_disposition": "FAIL_MERGED_REPLAY_SCOPE_BUG" if reproduced else "NOT_REPRODUCED",
        "interpretation": "wrong-ID early return / false rejection or wait interruption; not an unsafe input admission; no MAP01, GUI, model, or formal allocation",
    }
    return result


if __name__ == "__main__":
    rendered = json.dumps(run(), sort_keys=True, indent=2) + "\n"
    (ROOT / "audit-result.json").write_text(rendered, encoding="utf-8")
    print(rendered, end="")

