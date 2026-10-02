import argparse
import hashlib
import json
import sys
from pathlib import Path


def classify(row):
    if row["required_safety"]:
        if not row["received_by_all_arms"]:
            raise ValueError("mandatory safety cue missing from an arm")
        return "MANDATORY_SAFETY_CUE_INELIGIBLE_FOR_WITHHOLDING"
    delivered = row["delivery_time"] is not None and row["received_by_all_arms"]
    if not delivered and row["capture_time"] <= row["decision_deadline"]:
        return "EARLY_BUT_NOT_DELIVERED"
    if delivered and row["delivery_time"] > row["decision_deadline"]:
        return "DELIVERED_BUT_NO_DECISION_WINDOW"
    if delivered and (row["source_generation"] != row["current_generation"] or not row["truthful"]):
        if row["action_with_cue"] != "YIELD":
            raise ValueError("stale or misleading cue must YIELD")
        return "STALE_OR_MISLEADING_YIELD"
    if not delivered:
        return "NOT_DELIVERED"
    if not row["relevant"] or row["action_without_cue"] == row["action_with_cue"]:
        return "NOOP_OR_REDUNDANT"
    if row["delivery_time"] < row["decision_deadline"] and row["action_with_cue"] in row["eligible_actions"]:
        return "DECISION_RELEVANT_CANDIDATE"
    return "NO_DECISION_VALUE"


def analyze(fixture):
    optional = fixture["cases"][:5]
    if any(c.get("content", fixture["cue_content"]) != fixture["cue_content"] or c["event_id"] != "event-017" for c in optional):
        raise ValueError("optional timing arms must retain identical event identity and cue bytes")
    rows = []
    for case in fixture["cases"]:
        if case["action_with_cue"] not in case["eligible_actions"] or case["action_without_cue"] not in case["eligible_actions"]:
            raise ValueError("chosen action is outside the frozen eligible action set")
        oracle = fixture["oracle_action_effects"]
        if case["effect_with_cue"] != oracle[case["action_with_cue"]] or case["effect_without_cue"] != oracle[case["action_without_cue"]]:
            raise ValueError("synthetic effect does not match independent action oracle")
        label = classify(case)
        rows.append({
            "id": case["id"], "classification": label,
            "event_id": case["event_id"],
            "content_sha256": hashlib.sha256(case.get("content", fixture["cue_content"]).encode("utf-8")).hexdigest(),
            "source_generation": case["source_generation"], "current_generation": case["current_generation"],
            "arrival_only": "CAPTURE_BEFORE_DEADLINE" if case["capture_time"] <= case["decision_deadline"] else "LATE_CAPTURE",
            "relevance_only": "RELEVANT" if case["relevant"] else "IRRELEVANT",
            "decision_changed": case["action_without_cue"] != case["action_with_cue"],
            "simulated_effect_delta": int(oracle[case["action_with_cue"]]) - int(oracle[case["action_without_cue"]]),
            "source_to_capture": case["capture_time"] - case["source_time"],
            "source_to_delivery": None if case["delivery_time"] is None else case["delivery_time"] - case["source_time"],
            "decision_slack": None if case["delivery_time"] is None else case["decision_deadline"] - case["delivery_time"],
            "accounted_cost_ms": case["observation_cost_ms"] + case["delivery_cost_ms"] + case["processing_cost_ms"],
            "verified_value_claim": False,
            "withholding_refused": bool(case["required_safety"] and case["withholding_requested"])
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fixture", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    rows = analyze(fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema":"decision-opportunity-result-v1","rows":rows}, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"exit":0,"cases":len(rows),"labels":{r["id"]:r["classification"] for r in rows}}))


if __name__ == "__main__":
    main()
