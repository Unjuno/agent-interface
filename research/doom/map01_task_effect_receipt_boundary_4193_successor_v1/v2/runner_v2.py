import json
from contract import classify


def base():
    return {
        "mode": "ATTACK", "session_id": "s1", "plan_id": "p1",
        "actuation_id": "a1", "source_event_id": "e1", "event_kind": "TASK_EFFECT",
        "clock_domain": "m1", "down_ns": 100, "terminal_ns": 200,
        "scorer_event_id": "sc1", "scorer_effect_kind": "KILL_COUNT_INCREASE",
        "scorer_session_id": "s1", "scorer_plan_id": "p1",
        "scorer_actuation_id": "a1", "scorer_source_event_id": "e1",
        "scorer_monotonic_ns": 150, "scorer_clock_domain": "m1",
        "scorer_authority": False, "physical_down": True, "physical_up": True,
        "terminal_neutral": True, "duplicate_scorer_events": 0,
    }


CASES = [
    ("unique_positive", {}, "BOUND_TASK_EFFECT"),
    ("missing_source", {"source_event_id": None}, "HOLD_SOURCE_IDENTITY_INSUFFICIENT"),
    ("wrong_session", {"scorer_session_id": "s2"}, "HOLD_SOURCE_IDENTITY_INSUFFICIENT"),
    ("wrong_plan", {"scorer_plan_id": "p2"}, "HOLD_SOURCE_IDENTITY_INSUFFICIENT"),
    ("wrong_actuation", {"scorer_actuation_id": "a2"}, "HOLD_SOURCE_IDENTITY_INSUFFICIENT"),
    ("wrong_source_event", {"scorer_source_event_id": "e2"}, "HOLD_SOURCE_IDENTITY_INSUFFICIENT"),
    ("clock_mismatch", {"scorer_clock_domain": "m2"}, "HOLD_CLOCK_DOMAIN_UNCOMPARABLE"),
    ("score_before_down", {"scorer_monotonic_ns": 99}, "HOLD_CLOCK_DOMAIN_UNCOMPARABLE"),
    ("duplicate_score", {"duplicate_scorer_events": 2}, "FAIL_AMBIGUOUS_EVENT_BINDING"),
    ("no_input_positive", {"mode": "NO_INPUT"}, "FAIL_AUTHORITY_OR_ATTRIBUTION_LAUNDERING"),
    ("unsupported_event", {"event_kind": "HUD_STATE"}, "HOLD_UNSUPPORTED_EVENT_KIND"),
    ("unsupported_effect", {"scorer_effect_kind": "HUD_CHANGE"}, "HOLD_UNSUPPORTED_EFFECT_KIND"),
    ("missing_up", {"physical_up": False}, "HOLD_PHYSICAL_EDGE_INCOMPLETE"),
    ("nonneutral_terminal", {"terminal_neutral": False}, "HOLD_TERMINAL_NOT_NEUTRAL"),
]
def run():
    rows=[]
    for case_id, changes, expected in CASES:
        row=base(); row.update(changes)
        rows.append({"case_id":case_id,"input":row,"expected":expected,"observed":classify(row)})
    return {"schema":"task-effect-receipt-boundary-t0-raw-v1","rows":rows}

if __name__ == "__main__":
    print(json.dumps(run(),sort_keys=True,separators=(",",":")))
