import argparse
import copy
import hashlib
import json
from pathlib import Path


def expected_row(c, oracle, cue_content):
    delivered = c["delivery_time"] is not None and c["received_by_all_arms"]
    if c["required_safety"]:
        if not c["received_by_all_arms"]:
            raise AssertionError("mandatory safety cue was not delivered to every arm")
        label = "MANDATORY_SAFETY_CUE_INELIGIBLE_FOR_WITHHOLDING"
    elif not delivered and c["capture_time"] <= c["decision_deadline"]:
        label = "EARLY_BUT_NOT_DELIVERED"
    elif delivered and c["delivery_time"] > c["decision_deadline"]:
        label = "DELIVERED_BUT_NO_DECISION_WINDOW"
    elif delivered and (c["source_generation"] != c["current_generation"] or not c["truthful"]):
        if c["action_with_cue"] != "YIELD":
            raise AssertionError("invalid evidence was used for a non-YIELD action")
        label = "STALE_OR_MISLEADING_YIELD"
    elif not delivered:
        label = "NOT_DELIVERED"
    elif not c["relevant"] or c["action_without_cue"] == c["action_with_cue"]:
        label = "NOOP_OR_REDUNDANT"
    elif c["delivery_time"] < c["decision_deadline"] and c["action_with_cue"] in c["eligible_actions"]:
        label = "DECISION_RELEVANT_CANDIDATE"
    else:
        label = "NO_DECISION_VALUE"
    return {"id":c["id"],"classification":label,"event_id":c["event_id"],
            "content_sha256":hashlib.sha256(c.get("content", cue_content).encode("utf-8")).hexdigest(),
            "source_generation":c["source_generation"],"current_generation":c["current_generation"],
            "arrival_only":"CAPTURE_BEFORE_DEADLINE" if c["capture_time"] <= c["decision_deadline"] else "LATE_CAPTURE",
            "relevance_only":"RELEVANT" if c["relevant"] else "IRRELEVANT",
            "decision_changed":c["action_without_cue"] != c["action_with_cue"],
            "simulated_effect_delta":int(oracle[c["action_with_cue"]])-int(oracle[c["action_without_cue"]]),
            "source_to_capture":c["capture_time"]-c["source_time"],
            "source_to_delivery":None if c["delivery_time"] is None else c["delivery_time"]-c["source_time"],
            "decision_slack":None if c["delivery_time"] is None else c["decision_deadline"]-c["delivery_time"],
            "accounted_cost_ms":c["observation_cost_ms"]+c["delivery_cost_ms"]+c["processing_cost_ms"],
            "verified_value_claim":False,
            "withholding_refused":bool(c["required_safety"] and c["withholding_requested"])}


def mutations_rejected(actual, expected):
    controls = {}
    mutations = {}
    m = copy.deepcopy(actual); m[0]["classification"] = "DECISION_VALUE_VERIFIED_SCOPED"; mutations["promote_synthetic_candidate"] = m
    m = copy.deepcopy(actual); m[1]["decision_slack"] = 1.0; mutations["invent_postdeadline_window"] = m
    m = copy.deepcopy(actual); m[2]["classification"] = "DECISION_RELEVANT_CANDIDATE"; mutations["promote_undelivered"] = m
    m = copy.deepcopy(actual); m[4]["classification"] = "DECISION_RELEVANT_CANDIDATE"; mutations["accept_stale_generation"] = m
    m = copy.deepcopy(actual); m[5]["withholding_refused"] = False; mutations["erase_mandatory_safety_refusal"] = m
    for name, rows in mutations.items():
        controls[name] = rows != expected
    return controls


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("fixture",type=Path); ap.add_argument("candidate",type=Path); ap.add_argument("output",type=Path); a=ap.parse_args()
    fixture=json.loads(a.fixture.read_text(encoding="utf-8")); candidate=json.loads(a.candidate.read_text(encoding="utf-8"))
    optional=fixture["cases"][:5]
    if any(c.get("content",fixture["cue_content"])!=fixture["cue_content"] or c["event_id"]!="event-017" for c in optional):
        raise AssertionError("optional timing arms do not share the frozen source event and bytes")
    for c in fixture["cases"]:
        oracle=fixture["oracle_action_effects"]
        if c["action_with_cue"] not in c["eligible_actions"] or c["action_without_cue"] not in c["eligible_actions"]:
            raise AssertionError("fixture action is outside the frozen eligible set")
        if c["effect_with_cue"]!=oracle[c["action_with_cue"]] or c["effect_without_cue"]!=oracle[c["action_without_cue"]]:
            raise AssertionError("fixture effect fails independent action oracle")
    expected=[expected_row(c,fixture["oracle_action_effects"],fixture["cue_content"]) for c in fixture["cases"]]; actual=candidate["rows"]
    if actual != expected: raise AssertionError("raw-only independent reconstruction mismatch")
    labels={r["id"]:r["classification"] for r in expected}
    required={"early_delivered_choice_changes":"DECISION_RELEVANT_CANDIDATE","delivered_after_last_decision":"DELIVERED_BUT_NO_DECISION_WINDOW","captured_early_but_undelivered":"EARLY_BUT_NOT_DELIVERED","delivered_redundant_noop":"NOOP_OR_REDUNDANT","stale_generation_must_yield":"STALE_OR_MISLEADING_YIELD","mandatory_safety_cue_never_withheld":"MANDATORY_SAFETY_CUE_INELIGIBLE_FOR_WITHHOLDING"}
    if labels != required: raise AssertionError("frozen case disposition mismatch")
    if any(r["verified_value_claim"] for r in expected): raise AssertionError("synthetic fixture promoted to empirical value")
    controls=mutations_rejected(actual,expected)
    if len(controls)!=5 or not all(controls.values()): raise AssertionError("effective corruption control accepted")
    result={"schema":"decision-opportunity-audit-v1","cases":len(actual),"reconstructed":len(actual),"errors":[],"corruption_controls":controls,"labels":labels,"scope":"finite synthetic measurement-method fixture only; no empirical feedback-value result"}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"exit":0,"cases":len(actual),"errors":[],"corruptions_rejected":sum(controls.values())}))


if __name__=="__main__": main()
