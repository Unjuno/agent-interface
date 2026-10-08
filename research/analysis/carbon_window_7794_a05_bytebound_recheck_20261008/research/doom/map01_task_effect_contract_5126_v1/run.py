"""One fixed offline corpus for Issue #5126; no external calls or input."""
import json
from pathlib import Path
from contract import classify
from oracle import oracle

HERE = Path(__file__).resolve().parent


def positive():
    return {"session_id": "s1", "plan_id": "p1", "actuation_id": "a1", "clock_axis_attested": True,
            "physical": {"owner_id": "o1", "empty_release_verified": True,
                         "down": {"session_id": "s1", "plan_id": "p1", "actuation_id": "a1", "owner_id": "o1",
                                  "key": "space", "source_event_id": "edge-down-1", "lower_ns": 100, "upper_ns": 110},
                         "up": {"session_id": "s1", "plan_id": "p1", "actuation_id": "a1", "owner_id": "o1",
                                "key": "space", "source_event_id": "edge-up-1", "lower_ns": 200, "upper_ns": 210}},
            "state_feedback": [], "task_effects": []}


def effect():
    return {"effect_id": "effect-1", "source_event_id": "scorer-event-1", "session_id": "s1", "plan_id": "p1",
            "actuation_id": "a1", "observed_ns": 220, "scorer_source": "independent_progress_clock_v2",
            "scored": True, "scorer_independent": True, "controller_visible": False,
            "kind": "KILL_COUNT_INCREASE", "polarity": "useful"}


def cases():
    rows = []
    x = positive(); x["task_effects"] = [effect()]
    rows.append(("valid_positive", x, "TASK_EFFECT_SCOPED"))
    x = positive(); x["state_feedback"] = [{"session_id": "s1", "observed_ns": 150, "signal": "health", "before": 90, "after": 80}]
    rows.append(("state_only", x, "UNRESOLVED_NO_TASK_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["physical"]["down"]["source_event_id"] = " "
    rows.append(("blank_down_event_id", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["physical"]["up"]["source_event_id"] = "edge-down-1"
    rows.append(("duplicate_edge_event_id", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["task_effects"][0]["source_event_id"] = " "
    rows.append(("blank_scorer_event_id", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["task_effects"].append(dict(x["task_effects"][0]))
    rows.append(("duplicate_scorer_event", x, "UNRESOLVED_DUPLICATE_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["session_id"] = " "
    rows.append(("blank_session", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["physical"]["owner_id"] = 42
    rows.append(("nonstring_owner", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["task_effects"][0]["effect_id"] = "effect-1 "
    rows.append(("noncanonical_effect_id", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["task_effects"][0]["source_event_id"] = x["physical"]["down"]["source_event_id"]
    rows.append(("cross_plane_event_id_collision", x, "TASK_EFFECT_SCOPED"))
    x = positive(); x["task_effects"] = [effect()]; x["task_effects"][0]["plan_id"] = "foreign"
    rows.append(("foreign_plan", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["task_effects"][0]["observed_ns"] = 109
    rows.append(("effect_before_down_bound", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x = positive(); x["task_effects"] = [effect()]; x["task_effects"][0]["scorer_independent"] = False
    rows.append(("nonindependent_scorer", x, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    return rows


def main():
    output = []
    for case_id, raw, expected in cases():
        output.append({"case_id": case_id, "raw": raw, "expected_task_effect": expected,
                       "candidate": classify(raw), "oracle": oracle(raw)})
    doc = {"schema": "map01-task-effect-contract-result-v2", "issue": 5126,
           "input_authority": False, "live_calls": 0, "cases": output}
    path = HERE / "result.json"
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"result": str(path), "cases": len(output),
                      "candidate_oracle_mismatches": sum(r["candidate"] != r["oracle"] for r in output),
                      "expected_mismatches": sum(r["candidate"]["task_effect"] != r["expected_task_effect"] for r in output)}, sort_keys=True))


if __name__ == "__main__":
    main()
