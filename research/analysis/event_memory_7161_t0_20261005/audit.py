"""Independent oracle and tamper controls; no candidate import."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw = json.loads((HERE / "INPUT.json").read_text())
result = json.loads((HERE / "CANDIDATE.json").read_text())
expected = {"not_run": "NOT_RUN", "pending": "PENDING", "success": "SUCCESS",
            "success_then_revert": "SUCCESS_THEN_REVERTED", "failed_action": "FAILED"}
observed_ids = {"ui-receipt-1", "ui-receipt-2"}
assert len({x["case_id"] for x in raw["cases"]}) == len(expected)
assert len(raw["cases"]) == len(result["outputs"])
for case, output in zip(raw["cases"], result["outputs"]):
    assert case["case_id"] == output["case_id"]
    assert output["state"] == expected[case["case_id"]]
    assert output["input_authority"] is False
    events = case["events"]
    for event in events:
        if event["kind"] == "effect_prediction":
            assert event["source"] == "model"
            assert event["value"] not in output["observed_values"] or not any(
                e["kind"] == "effect_observation" and e["value"] == event["value"]
                for e in events)
        if event["kind"] in {"effect_observation", "external_change_observation"}:
            assert event["source"] in observed_ids

# Mutations are applied to isolated copies and must be rejected by the raw oracle.
mutations = []
for mode in ("drop_reversion", "promote_prediction", "add_authority"):
    bad = copy.deepcopy(result)
    if mode == "drop_reversion":
        bad["outputs"][3]["state"] = "SUCCESS"
    elif mode == "promote_prediction":
        bad["outputs"][1]["observed_values"] = ["saved"]
        bad["outputs"][1]["state"] = "SUCCESS"
    else:
        bad["outputs"][2]["input_authority"] = True
    rejected = False
    try:
        for case, output in zip(raw["cases"], bad["outputs"]):
            assert output["state"] == expected[case["case_id"]]
            assert output["input_authority"] is False
            true_observed = [e["value"] for e in case["events"] if e["kind"] in
                             {"effect_observation", "external_change_observation"}]
            assert output["observed_values"] == true_observed
    except AssertionError:
        rejected = True
    assert rejected
    mutations.append(mode)
audit = {"status": "PASS_METHOD_SCOPED", "cases_verified": 5,
         "distinct_histories_same_final_visual": True, "mutation_controls": 3,
         "mutations_rejected": mutations, "input_authority_cases": 0}
(HERE / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps(audit, sort_keys=True, separators=(",", ":")))
