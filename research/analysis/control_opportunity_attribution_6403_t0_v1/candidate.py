"""No-participant T0: derive intervention opportunity from source-bound facts."""
import json
import sys


def assess(trace):
    if trace["delivery_status"]=="AMBIGUOUS":
        return "UNKNOWN"
    if trace["delivery_status"]=="NOT_DELIVERED":
        return "NO_OPPORTUNITY"
    delivery=trace["delivered_at"]
    effect=trace["effect_at"]
    if delivery is None or effect is None:
        return "UNKNOWN"
    if trace["agent_action_at"] is not None and trace["agent_action_at"] < effect and trace["sent_at"] is not None and trace["sent_at"] >= effect:
        return "NO_OPPORTUNITY"
    if delivery>=effect:
        return "NO_OPPORTUNITY"
    accepted=trace["accepted_at"]
    if accepted is None:
        return "UNKNOWN"
    if accepted>=effect:
        return "NO_OPPORTUNITY"
    required=(trace["safe_override_available"],trace["override_authorized"],trace["ui_current"])
    if any(value is None for value in required):
        return "UNKNOWN"
    if not all(required):
        return "NO_OPPORTUNITY"
    ready=max(delivery,accepted)
    remaining=effect-ready
    if remaining<trace["override_duration"]:
        return "NO_OPPORTUNITY"
    correction=trace["correction_at"]
    if trace["correction_verified"] is True and correction is not None and ready<=correction<effect:
        return "OPPORTUNITY_USED"
    return "OPPORTUNITY"


def timeline(trace):
    events=[{"event":"agent_action","at":trace["agent_action_at"],"authority_holder":trace["authority_holder"]},
            {"event":"notification_sent","at":trace["sent_at"]}]
    if trace["delivered_at"] is not None:
        events.append({"event":"notification_delivery","status":trace["delivery_status"],"at":trace["delivered_at"]})
    if trace["accepted_at"] is not None:
        events.append({"event":"handoff_accepted","at":trace["accepted_at"]})
    events.append({"event":"agent_effect","at":trace["effect_at"],"effect":trace["effect"]})
    if trace["correction_at"] is not None:
        events.append({"event":"human_correction","at":trace["correction_at"],"verified":trace["correction_verified"]})
    return sorted(events, key=lambda event: event["at"])


def run(path):
    fixture=json.load(open(path,encoding="utf-8"))
    records=[]
    for trace in fixture["traces"]:
        result=assess(trace)
        common={"raw_evidence":trace["raw_record"],"accessible_fact_ids":fixture["presentation_fact_ids"]}
        actor_outcome={**common,"format":"ACTOR_OUTCOME","actor":trace["actor"],
                       "agent_action":trace["agent_action"],"effect":trace["effect"],"outcome":trace["outcome"]}
        control_timeline={**common,"format":"CONTROL_OPPORTUNITY_TIMELINE","events":timeline(trace),
                          "assessment":result,"safe_override_available":trace["safe_override_available"],
                          "override_authorized":trace["override_authorized"],"override_duration":trace["override_duration"],
                          "ui_current":trace["ui_current"]}
        records.append({"trace":trace["id"],"assessment":result,"actor_outcome_summary":actor_outcome,
                        "control_timeline_summary":control_timeline})
    return {"schema":"issue6403-t0-candidate-v1","records":records,
            "non_authoritative_negative_controls":fixture["negative_controls"]}


if __name__=="__main__":
    print(json.dumps(run(sys.argv[1]),sort_keys=True,separators=(",",":")))
