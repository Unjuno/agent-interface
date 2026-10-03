"""Generate acquisition from closed cue intervals; all times/effects are simulated."""
import argparse
import json
from pathlib import Path

FIELDS = {"case_id", "opportunity", "capture_schedule_ms", "observation_horizon_ms",
          "clock_synchronized", "delivery_latency_ms", "decision_latency_ms",
          "effect_latency_ms", "effect_enabled", "safe_stop"}


def integer(value):
    return type(value) is int and value >= 0


def validate(case):
    if type(case) is not dict or set(case) != FIELDS:
        raise ValueError("only source intervals and protocol fields are allowed")
    if type(case["case_id"]) is not str or not case["case_id"]:
        raise ValueError("case_id must be a nonempty string")
    for key in ("observation_horizon_ms", "delivery_latency_ms", "decision_latency_ms", "effect_latency_ms"):
        if not integer(case[key]):
            raise ValueError("nonnegative exact integer required: " + key)
    for key in ("clock_synchronized", "effect_enabled", "safe_stop"):
        if type(case[key]) is not bool:
            raise ValueError("boolean required: " + key)
    schedule = case["capture_schedule_ms"]
    if type(schedule) is not list or not all(integer(t) for t in schedule) or schedule != sorted(set(schedule)):
        raise ValueError("sorted unique integer schedule required")
    cue = case["opportunity"]
    if cue is not None and (type(cue) is not dict or set(cue) != {"onset_ms", "expiry_ms"}
                            or not all(integer(t) for t in cue.values())
                            or cue["onset_ms"] > cue["expiry_ms"]):
        raise ValueError("ordered closed integer interval required")


def evaluate(case):
    validate(case)
    cue, horizon = case["opportunity"], case["observation_horizon_ms"]
    sampled = []
    stages = dict.fromkeys(("delivery", "decision", "effect", "safe_stop"))
    if cue is not None and case["clock_synchronized"]:
        sampled = [t for t in case["capture_schedule_ms"]
                   if cue["onset_ms"] <= t <= min(cue["expiry_ms"], horizon)]
        if sampled:
            delivery = sampled[0] + case["delivery_latency_ms"]
            if delivery <= horizon:
                stages["delivery"] = delivery
                if delivery <= cue["expiry_ms"]:
                    decision = delivery + case["decision_latency_ms"]
                    if decision <= horizon:
                        stages["decision"] = decision
                        if decision <= cue["expiry_ms"]:
                            if case["safe_stop"]:
                                stages["safe_stop"] = decision
                            elif case["effect_enabled"]:
                                effect = decision + case["effect_latency_ms"]
                                if effect <= horizon:
                                    stages["effect"] = effect
    if cue is None:
        boundary, reason = "NOT_APPLICABLE", "no_exogenous_opportunity"
    elif not case["clock_synchronized"]:
        boundary, reason = "UNKNOWN", "clock_unsynced"
    elif horizon < cue["expiry_ms"] and stages["effect"] is None and stages["safe_stop"] is None:
        boundary, reason = "UNKNOWN", "right_censored"
    elif not sampled:
        boundary, reason = "not_acquired", "no_capture_in_closed_interval"
    elif stages["delivery"] is None or stages["delivery"] > cue["expiry_ms"]:
        boundary, reason = "acquired_not_delivered", "no_timely_delivery_observed"
    elif stages["decision"] is None or stages["decision"] > cue["expiry_ms"]:
        boundary, reason = "delivered_no_decision", "no_timely_decision_observed"
    elif stages["safe_stop"] is not None:
        boundary, reason = "decision_no_effect", "safe_stop"
    elif stages["effect"] is not None:
        boundary, reason = "eligible_effect_in_model", "simulated_effect_observed"
    else:
        boundary, reason = "decision_no_effect", "no_simulated_effect_observed"
    return {"case_id": case["case_id"], "opportunity": cue,
            "capture_schedule_ms": list(case["capture_schedule_ms"]),
            "observation_horizon_ms": horizon, "sampled_capture_ms": sampled,
            "stages_ms": stages, "boundary": boundary, "reason": reason,
            "simulated_effect_token": "simulated:" + case["case_id"] if stages["effect"] is not None else None}


def run(fixture):
    if set(fixture) != {"schema", "fixture_id", "cases"} or fixture["schema"] != "derived-capture-input-v1":
        raise ValueError("invalid source-only fixture")
    rows = [evaluate(case) for case in fixture["cases"]]
    if len({r["case_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate case ids")
    return {"schema": "derived-capture-raw-v1", "fixture_id": fixture["fixture_id"],
            "authority_events": 0, "live_effect_events": 0, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = run(json.loads(Path(args.fixture).read_text()))
    with Path(args.out).open("x") as target:
        json.dump(raw, target, sort_keys=True, indent=2)
        target.write("\n")
    print("CANDIDATE_COMPLETE rows=" + str(len(raw["rows"])))
