"""Run fixed cross-session, same-session and endpoint-tie A03 comparisons."""
from __future__ import annotations

import json
import sys
from pathlib import Path

DOOM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DOOM / "scorer_feedback_attribution_59_t0_a03_20261004"))
from scorer_feedback_attribution_v2 import attribute_positive_events as attribute_a03
from attribution_v3 import attribute_positive_events as attribute_v3


def sample(time_ns: int, session_id: str) -> dict:
    return {"schema": "independent-progress-sample-v2", "sample_ns": time_ns, "session_id": session_id}


def event(session_id: str) -> dict:
    return {
        "schema": "independent-progress-event-v2", "event_sequence": 1,
        "observed_ns": 200, "kind": "KILL_COUNT_INCREASE", "polarity": "positive",
        "useful": True, "controller_visible": False, "session_id": session_id,
    }


def interval(end: int, session_id: str) -> dict:
    return {
        "intent_token": "intent-a", "key": "ATTACK", "admitted_ns": 90,
        "release_sync_ns": end, "release_verified": True, "session_id": session_id,
    }


def main() -> None:
    scorer_samples = [sample(100, "run-b"), sample(200, "run-b")]
    scorer_events = [event("run-b")]
    foreign = [interval(210, "run-a")]
    a03_cross = attribute_a03(scorer_samples, scorer_events, foreign)[0]
    try:
        attribute_v3(scorer_samples, scorer_events, foreign)
    except ValueError as exc:
        v3_cross = {"disposition": "REJECTED", "reason": str(exc)}
    else:
        raise AssertionError("session-bound A03 wrapper accepted mixed sessions")

    same = attribute_v3(scorer_samples, scorer_events, [interval(210, "run-b")])[0]
    tied = attribute_v3(scorer_samples, scorer_events, [interval(200, "run-b")])[0]
    try:
        attribute_v3(scorer_samples, scorer_events, [dict(interval(210, "run-b"), session_id=None)])
    except ValueError as exc:
        missing = {"disposition": "REJECTED", "reason": str(exc)}
    else:
        raise AssertionError("session-bound A03 wrapper accepted missing identity")

    print(json.dumps({
        "schema": "scorer-feedback-session-bound-a03-v1",
        "parent_head": "58102e6c12719ed5f4c4bb9616331d86b39ffa90",
        "a03_unguarded_cross_session": {
            "status": a03_cross["status"],
            "possible_intent_tokens": a03_cross["possible_intent_tokens"],
            "intent_token": a03_cross["intent_token"],
            "causal_attribution": a03_cross["causal_attribution"],
        },
        "v3_cross_session": v3_cross,
        "v3_same_session": {
            "status": same["status"],
            "possible_intent_tokens": same["possible_intent_tokens"],
            "intent_token": same["intent_token"],
            "causal_attribution": same["causal_attribution"],
        },
        "v3_endpoint_tie": {"status": tied["status"], "intent_token": tied["intent_token"]},
        "v3_missing_identity": missing,
        "status": "PASS_SESSION_BOUND_A03",
        "scope": "fixed synthetic API-boundary construction only",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
