"""Scoring contract for future human observations; T0 vectors are scripted only."""
from __future__ import annotations


def score_one(truth: dict, response: dict) -> dict:
    event_true = bool(truth["anomaly_present"])
    visible = truth["visibility"] == "visible"
    hard_stop = bool(truth["mandatory_stop"])
    t = response.get("response_ms")
    no_response = t is None
    onset = truth.get("onset_ms")
    expiry = truth.get("expiry_ms")
    delay = (t - onset) if t is not None and onset is not None and t >= onset else None
    in_window = t is not None and (onset is None or t >= onset) and (expiry is None or t <= expiry)
    reported = bool(response.get("reported_anomaly", False))
    prompted = bool(response.get("prompted_by_hard_alert", False))

    if hard_stop:
        signal = "prompted_hard_stop" if prompted else "mandatory_stop_unprompted_channel"
    elif event_true and not visible:
        signal = "unobservable_anomaly"
    elif event_true:
        signal = "hit" if reported and in_window else "miss"
    else:
        signal = "false_alarm" if reported and in_window else "correct_rejection"

    return {
        "opportunity_id": response["opportunity_id"],
        "policy": response["policy"],
        "signal_outcome": signal,
        "no_response": no_response,
        "late_response": bool(t is not None and expiry is not None and t > expiry),
        "response_delay_ms": delay,
        "correct_safe_next_step": None if no_response else response.get("safe_action") == truth["required_safe_action"],
        "active_time_ms": response.get("active_time_ms"),
        "response_provenance": response.get("provenance"),
    }


def score_all(rows: list[dict], truth_by_id: dict, scoring_vectors: dict) -> list[dict]:
    overrides = scoring_vectors["overrides"]
    default = scoring_vectors["default"]
    scored = []
    for row in rows:
        key = f"{row['opportunity_id']}/{row['policy'][0]}"
        response = dict(overrides.get(key, default))
        response.update({"opportunity_id": row["opportunity_id"], "policy": row["policy"]})
        scored.append(score_one(truth_by_id[row["opportunity_id"]], response))
    return scored
