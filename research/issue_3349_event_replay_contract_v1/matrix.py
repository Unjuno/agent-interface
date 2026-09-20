"""Finite behavioral contract for Issue #3349's retained-event replay defect.

This is a standalone oracle model, not the frozen candidate implementation.
The container entrypoint also checks the candidate source blob digest.
"""
from __future__ import annotations

import json

SOURCE_SHA256 = "4432a6188b5318dc552f050a26ff9e2a5d32bbf9"


def replay_first(events, queue, predicate):
    """Model current main: scan the full retained event history, then queue."""
    for row in events:
        if predicate(row):
            return row
    while queue:
        row = queue.pop(0)
        if predicate(row):
            return row
    return None


def scoped_replay(events, queue, predicate, *, allowed_event, identifier):
    """Independent expected policy: role and operation identity both bind."""
    def admissible(row):
        return (
            isinstance(row, dict)
            and row.get("event") == allowed_event
            and row.get("id") == identifier
            and predicate(row)
        )

    matches = [row for row in events if admissible(row)]
    if len(matches) > 1:
        return {"disposition": "ambiguous_duplicate", "count": len(matches)}
    if matches:
        return matches[0]
    while queue:
        row = queue.pop(0)
        if admissible(row):
            return row
    return None


def run_matrix():
    rows = []
    cases = [
        ("matching_retained_terminal", [{"event": "terminal", "id": "A"}], [],
         "terminal", "A", "return"),
        ("stale_accepted_prelude", [{"event": "accepted", "id": "prelude"}], [],
         "accepted", "fallback", "wait"),
        ("stale_rejected_prelude", [{"event": "rejected", "id": "prelude"}], [],
         "rejected", "fallback", "wait"),
        ("duplicate_terminal_history", [
            {"event": "terminal", "id": "A"}, {"event": "terminal", "id": "A"}], [],
         "terminal", "A", "ambiguous_duplicate"),
        ("wrong_terminal_identifier", [{"event": "terminal", "id": "other"}], [],
         "terminal", "A", "wait"),
        ("unrelated_retained_then_queued_response", [{"event": "observation", "sequence": 5}],
         [{"event": "accepted", "id": "fallback"}],
         "accepted", "fallback", "return"),
    ]
    cases.insert(1, ("matching_queued_fallback_response", [], [
        {"event": "accepted", "id": "fallback"}], "accepted", "fallback", "return"))
    for name, events, queued, wanted_event, wanted_id, disposition in cases:
        predicate = lambda row, e=wanted_event, i=wanted_id: (
            isinstance(row, dict) and row.get("event") == e and row.get("id") == i
        )
        result = scoped_replay(list(events), list(queued), predicate,
                               allowed_event=wanted_event, identifier=wanted_id)
        passed = (
            result is not None and result.get("disposition") == "ambiguous_duplicate"
            if disposition == "ambiguous_duplicate"
            else (result is not None and result.get("event") == wanted_event and result.get("id") == wanted_id)
            if disposition == "return"
            else result is None
        )
        rows.append({
            "case": name,
            "expected_disposition": disposition,
            "expected_event": wanted_event,
            "expected_id": wanted_id,
            "returned": result,
            "pass": passed,
        })
    # Candidate-specific witnesses: model the current unconditional history scan.
    stale = replay_first(
        [{"event": "accepted", "id": "prelude"}],
        [],
        lambda row: row.get("event") == "accepted",
    )
    rows.append({
        "case": "candidate_accepts_stale_prelude_witness",
        "returned": stale,
        "pass": stale is not None and stale.get("id") == "prelude",
    })
    return rows


if __name__ == "__main__":
    result = run_matrix()
    print(json.dumps({"cases": result, "all_contract_cases_pass": all(
        row["pass"] for row in result if row["case"] != "candidate_accepts_stale_prelude_witness"
    ), "candidate_defect_reproduced": next(
        row["pass"] for row in result if row["case"] == "candidate_accepts_stale_prelude_witness"
    )}, sort_keys=True, indent=2))

