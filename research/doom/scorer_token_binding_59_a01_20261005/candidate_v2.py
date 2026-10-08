"""Fail closed when current intent identity is absent or conflicts."""
from __future__ import annotations

import sys
from pathlib import Path

PARENT = Path(__file__).resolve().parents[1] / "scorer_eventlog_join_t0_v1"
sys.path.insert(0, str(PARENT))
from candidate import classify_intent as classify_intent_v1  # noqa: E402


def _reject(reason: str) -> dict:
    return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": reason,
            "causal_attribution": False}


def classify_intent(events, samples, intent_id, *, max_gap_ns):
    accepted = [row for row in events
                if row.get("event") == "accepted" and row.get("id") == intent_id]
    if len(accepted) != 1:
        return classify_intent_v1(events, samples, intent_id, max_gap_ns=max_gap_ns)

    accepted_token = accepted[0].get("intent_token")
    if type(accepted_token) is not str or not accepted_token:
        return _reject("missing_acceptance_intent_token")

    admissions = [row for row in events
                  if row.get("event") == "input_admission" and row.get("id") == intent_id]
    if not admissions:
        return classify_intent_v1(events, samples, intent_id, max_gap_ns=max_gap_ns)
    for row in admissions:
        token = row.get("intent_token")
        if type(token) is not str or not token:
            return _reject("missing_input_intent_token")
        if token != accepted_token:
            return _reject("intent_token_mismatch")

    return classify_intent_v1(events, samples, intent_id, max_gap_ns=max_gap_ns)
