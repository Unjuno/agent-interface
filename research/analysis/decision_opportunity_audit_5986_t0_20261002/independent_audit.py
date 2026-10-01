import hashlib
import json
import sys
from pathlib import Path


def expected(case, cue, oracle):
    delivered = case["delivery_time"] is not None and case["received_by_all_arms"]
    if case["required_safety"]:
        label = "MANDATORY_SAFETY_CUE_INELIGIBLE_FOR_WITHHOLDING"
    elif not delivered and case["capture_time"] <= case["decision_deadline"]:
        label = "EARLY_BUT_NOT_DELIVERED"
    elif delivered and case["delivery_time"] > case["decision_deadline"]:
        label = "DELIVERED_BUT_NO_DECISION_WINDOW"
    elif delivered and (case["source_generation"] != case["current_generation"] or not case["truthful"]):
        label = "STALE_OR_MISLEADING_YIELD"
    elif not delivered:
        label = "NOT_DELIVERED"
    elif not case["relevant"] or case["action_without_cue"] == case["action_with_cue"]:
        label = "NOOP_OR_REDUNDANT"
    else:
        label = "DECISION_RELEVANT_CANDIDATE"
    payload = case.get("content", cue).encode()
    return {
        "id": case["id"], "classification": label, "event_id": case["event_id"],
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "source_generation": case["source_generation"], "current_generation": case["current_generation"],
        "arrival_only": "CAPTURE_BEFORE_DEADLINE" if case["capture_time"] <= case["decision_deadline"] else "LATE_CAPTURE",
        "relevance_only": "RELEVANT" if case["relevant"] else "IRRELEVANT",
        "decision_changed": case["action_without_cue"] != case["action_with_cue"],
        "simulated_effect_delta": int(oracle[case["action_with_cue"]])-int(oracle[case["action_without_cue"]]),
        "source_to_capture": case["capture_time"]-case["source_time"],
        "source_to_delivery": None if case["delivery_time"] is None else case["delivery_time"]-case["source_time"],
        "decision_slack": None if case["delivery_time"] is None else case["decision_deadline"]-case["delivery_time"],
        "accounted_cost_ms": case["observation_cost_ms"]+case["delivery_cost_ms"]+case["processing_cost_ms"],
        "verified_value_claim": False,
        "withholding_refused": bool(case["required_safety"] and case["withholding_requested"]),
    }


def reconstruct(fixture):
    expected_rows = []
    for case in fixture["cases"]:
        if case["action_with_cue"] not in case["eligible_actions"] or case["action_without_cue"] not in case["eligible_actions"]:
            raise ValueError("fixture action outside eligible action set")
        oracle = fixture["oracle_action_effects"]
        if case["effect_with_cue"] != oracle[case["action_with_cue"]] or case["effect_without_cue"] != oracle[case["action_without_cue"]]:
            raise ValueError("fixture effect does not match the independently declared action oracle")
        expected_rows.append(expected(case, fixture["cue_content"], oracle))
    return expected_rows


def audit(fixture, raw):
    expected_rows = reconstruct(fixture)
    actual = raw["rows"]
    if actual != expected_rows:
        raise ValueError("frozen candidate raw differs from independent reconstruction")
    mandatory = next(r for r in expected_rows if r["id"] == "mandatory_safety_cue_never_withheld")
    if mandatory["withholding_refused"] is not True:
        raise ValueError("mandatory safety withholding was not refused")
    if any(r["verified_value_claim"] for r in expected_rows):
        raise ValueError("synthetic effect delta was promoted to verified value")
    mutants = []
    for field, value, row in [
        ("classification", "DECISION_VALUE_VERIFIED_SCOPED", 0),
        ("classification", "DECISION_RELEVANT_CANDIDATE", 1),
        ("decision_slack", 1, 1),
        ("classification", "DECISION_RELEVANT_CANDIDATE", 2),
        ("classification", "DECISION_RELEVANT_CANDIDATE", 4),
        ("withholding_refused", False, 5),
    ]:
        mutant = [dict(r) for r in actual]
        mutant[row][field] = value
        mutants.append(mutant != expected_rows)
    if not all(mutants):
        raise ValueError("independent corruption control accepted")
    return {"schema":"decision-opportunity-independent-audit-v1","cases":len(actual),"reconstructed":len(expected_rows),"errors":[],"mutations_rejected":len(mutants),"mutation_count":len(mutants),"labels":{r["id"]:r["classification"] for r in expected_rows},"scope":"independent audit-only reproduction of frozen synthetic raw; no new candidate allocation or empirical value claim"}


def main():
    fixture_path, raw_path, out_path = map(Path, sys.argv[1:4])
    fixture = json.loads(fixture_path.read_text())
    raw = json.loads(raw_path.read_text())
    result = audit(fixture, raw)
    out_path.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"exit":0,"cases":result["cases"],"mutations_rejected":result["mutations_rejected"],"errors":[]}))


if __name__ == "__main__":
    main()
