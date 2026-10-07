"""Corrective raw-driven audit; preserves the original audit receipt unchanged."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_IDS = {"not_run", "pending", "success", "success_then_revert", "failed_action"}
OBSERVATION_KINDS = {"effect_observation", "external_change_observation"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def disposition(events):
    dispatched = [e for e in events if e["kind"] == "action_dispatch"]
    observed = [e["value"] for e in events if e["kind"] in OBSERVATION_KINDS]
    if not dispatched:
        return "NOT_RUN"
    if not observed:
        return "PENDING"
    if observed[-1] == "saved":
        return "SUCCESS"
    if observed[-1] == "unsaved" and "saved" in observed[:-1]:
        return "SUCCESS_THEN_REVERTED"
    return "FAILED"


def validate(raw, result):
    require(raw["schema"] == "event-memory-t0-v1", "raw schema mismatch")
    cases = raw["cases"]
    ids = [c["case_id"] for c in cases]
    require(len(ids) == 5 and len(set(ids)) == 5 and set(ids) == EXPECTED_IDS,
            "raw case identity mismatch")
    require({c["final_visual_state"] for c in cases} == {"dialog_closed"},
            "final visual states are not identical")
    signatures = [json.dumps(c["events"], sort_keys=True, separators=(",", ":"))
                  for c in cases]
    require(len(set(signatures)) == 5, "raw histories are not distinct")

    raw_by_id = {c["case_id"]: c for c in cases}
    require(result["schema"] == "event-memory-result-v1", "result schema mismatch")
    outputs = result["outputs"]
    output_ids = [o["case_id"] for o in outputs]
    require(len(output_ids) == 5 and len(set(output_ids)) == 5 and set(output_ids) == EXPECTED_IDS,
            "candidate output identity mismatch")
    output_by_id = {o["case_id"]: o for o in outputs}
    seen_dispositions = set()
    for case_id, case in raw_by_id.items():
        events = case["events"]
        event_ids = []
        for event in events:
            if event["kind"] in OBSERVATION_KINDS:
                require(event["source"] in {"ui-receipt-1", "ui-receipt-2"},
                        "observation lacks recognized receipt provenance")
                event_ids.append(event["source"])
            elif event["kind"] == "effect_prediction":
                require(event["source"] == "model", "prediction source mismatch")
            else:
                require(event["kind"] == "action_dispatch", "unknown event kind")
        require(len(event_ids) == len(set(event_ids)), "duplicate observation receipt")

        expected_state = disposition(events)
        seen_dispositions.add(expected_state)
        output = output_by_id[case_id]
        require(output["state"] == expected_state, "disposition differs from raw history")
        expected_observed = [e["value"] for e in events if e["kind"] in OBSERVATION_KINDS]
        expected_predictions = [e["value"] for e in events if e["kind"] == "effect_prediction"]
        require(output["observed_values"] == expected_observed,
                "observed values differ from raw receipts")
        require(output["prediction_values"] == expected_predictions,
                "prediction values differ from raw predictions")
        require(type(output["input_authority"]) is bool and output["input_authority"] is False,
                "retrieval/projection acquired input authority")
    require(seen_dispositions == {"NOT_RUN", "PENDING", "SUCCESS",
                                  "SUCCESS_THEN_REVERTED", "FAILED"},
            "required disposition coverage missing")


def rejected(raw, result):
    try:
        validate(raw, result)
    except (AssertionError, KeyError, TypeError, ValueError):
        return True
    return False


raw_bytes = (HERE / "INPUT.json").read_bytes()
result_bytes = (HERE / "CANDIDATE.json").read_bytes()
raw = json.loads(raw_bytes)
result = json.loads(result_bytes)
validate(raw, result)

mutations = []
for name in ("wrong_state", "wrong_observation", "drop_prediction", "grant_authority",
             "change_visual", "duplicate_history", "drop_output", "duplicate_output"):
    bad_raw, bad_result = copy.deepcopy(raw), copy.deepcopy(result)
    by_id = {x["case_id"]: x for x in bad_result["outputs"]}
    if name == "wrong_state":
        by_id["success_then_revert"]["state"] = "SUCCESS"
    elif name == "wrong_observation":
        by_id["failed_action"]["observed_values"] = []
    elif name == "drop_prediction":
        by_id["pending"]["prediction_values"] = []
    elif name == "grant_authority":
        by_id["success"]["input_authority"] = True
    elif name == "change_visual":
        bad_raw["cases"][0]["final_visual_state"] = "different"
    elif name == "duplicate_history":
        bad_raw["cases"][1]["events"] = copy.deepcopy(bad_raw["cases"][0]["events"])
    elif name == "drop_output":
        bad_result["outputs"].pop()
    else:
        bad_result["outputs"].append(copy.deepcopy(bad_result["outputs"][0]))
    require(rejected(bad_raw, bad_result), f"mutation accepted: {name}")
    mutations.append(name)

audit = {
    "status": "PASS_METHOD_SCOPED",
    "scope": "corrective raw-driven audit of the retained candidate; candidate not rerun",
    "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "candidate_sha256": hashlib.sha256(result_bytes).hexdigest(),
    "cases_verified": 5,
    "distinct_final_visual_states": 1,
    "distinct_raw_histories": 5,
    "mutations_rejected": mutations,
    "mutation_controls": len(mutations),
    "candidate_invocation_count_in_this_supplement": 0,
}
(HERE / "AUDIT_V2.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps(audit, sort_keys=True, separators=(",", ":")))
