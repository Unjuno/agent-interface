"""Run one fixed adversarial session-mismatch control and v2 candidate."""
from __future__ import annotations

import json

from attribution_v2 import attribute_positive_events
from scorer_feedback_attribution_v1 import attribute_positive_events as attribute_v1


def sample(time_ns: int, session_id: str) -> dict:
    return {"schema": "independent-progress-sample-v2", "sample_ns": time_ns, "session_id": session_id}


def event(session_id: str) -> dict:
    return {
        "schema": "independent-progress-event-v2",
        "event_sequence": 1,
        "observed_ns": 200,
        "kind": "KILL_COUNT_INCREASE",
        "polarity": "positive",
        "useful": True,
        "controller_visible": False,
        "session_id": session_id,
    }


def interval(session_id: str) -> dict:
    return {
        "intent_token": "intent-a",
        "key": "ATTACK",
        "admitted_ns": 90,
        "release_sync_ns": 210,
        "release_verified": True,
        "session_id": session_id,
    }


def main() -> None:
    samples = [sample(100, "run-b"), sample(200, "run-b")]
    cross_event = [event("run-b")]
    cross_interval = [interval("run-a")]
    v1 = attribute_v1(samples, cross_event, cross_interval)[0]
    try:
        attribute_positive_events(samples, cross_event, cross_interval)
    except ValueError as exc:
        cross_session_v2 = {"disposition": "REJECTED", "reason": str(exc)}
    else:
        raise AssertionError("v2 accepted cross-session records")

    same = attribute_positive_events(
        samples, [event("run-b")], [interval("run-b")]
    )[0]
    try:
        no_id = [dict(samples[0])]
        del no_id[0]["session_id"]
        attribute_positive_events(no_id + [samples[1]], [event("run-b")], [interval("run-b")])
    except ValueError as exc:
        missing_session_v2 = {"disposition": "REJECTED", "reason": str(exc)}
    else:
        raise AssertionError("v2 accepted a missing session identity")

    print(json.dumps({
        "schema": "scorer-feedback-session-bound-t0-v2",
        "parent_head": "b076890cbcd28f2889184055453f2868fd87c629",
        "v1_cross_session_control": {
            "status": v1["status"],
            "intent_token": v1["intent_token"],
            "causal_attribution": v1["causal_attribution"],
        },
        "v2_cross_session": cross_session_v2,
        "v2_same_session": {
            "status": same["status"],
            "intent_token": same["intent_token"],
            "causal_attribution": same["causal_attribution"],
        },
        "v2_missing_session": missing_session_v2,
        "status": "PASS_SESSION_BOUND",
        "scope": "fixed synthetic API-boundary construction only",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
