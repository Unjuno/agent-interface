#!/usr/bin/env python3
"""Independent truth-oracle reconstruction for Issue #6558 candidate output."""
import hashlib
import json
import pathlib
import sys

CHANGING = {"sort-rebind", "virtual-reuse", "app-update"}


def main():
    fixture_path, truth_path, raw_path, oracle_path = map(pathlib.Path, sys.argv[1:5])
    fixture = json.loads(fixture_path.read_text())
    truth = json.loads(truth_path.read_text())["intended_object"]
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    if len(fixture["cases"]) != 9 or len(raw.get("rows", [])) != 9:
        errors.append("ROW_COUNT")
    by_id = {r.get("case_id"): r for r in raw.get("rows", [])}
    if set(by_id) != set(truth):
        errors.append("CASE_SET")
    scores = {k:{"correct":0,"unsafe":0,"asks":0,"unknown":0} for k in ("raw_coordinate","fresh_machine_rebind","initial_clarification_only","scoped_restatement")}
    for case in fixture["cases"]:
        row = by_id.get(case["id"], {})
        initial = next(x for x in case["initial_items"] if x["object"] == case["initial_ack_object"])
        current_by_node = {x["node"]: x for x in case["current_items"]}
        expected_raw = case["current_items"][case["initial_slot"]]["object"]
        expected_bound = current_by_node[initial["node"]]["object"]
        if row.get("raw_coordinate") != {"object":expected_raw,"asks":0}:
            errors.append("RAW_RECONSTRUCTION:" + case["id"])
        for arm in ("fresh_machine_rebind", "initial_clarification_only"):
            expected_arm = {"object":expected_bound,"asks":0}
            if arm == "initial_clarification_only" and case["id"] == "ambiguous-initial-clarified":
                expected_arm["asks"] = 1
            if row.get(arm) != expected_arm:
                errors.append("BASELINE_RECONSTRUCTION:" + arm + ":" + case["id"])
        changing = case["event"] in CHANGING
        matches = [x["object"] for x in case["current_items"] if case["response_property"] in x["properties"]]
        valid_response = bool(case["response_property"]) and case["response_generation"] == case["current_generation"] and len(matches) == 1
        expected_scoped = ({"object":matches[0],"asks":1,"reason":"REGROUNDED"} if valid_response else {"object":None,"asks":0,"reason":"UNKNOWN_INVALID_RESTATEMENT"}) if changing else {"object":case["initial_ack_object"],"asks":0,"reason":"UNCHANGED_REFERENT" if case["current_generation"] == case["initial_generation"] else "BENIGN_TRANSFORM"}
        if row.get("scoped_restatement") != expected_scoped:
            errors.append("SCOPED_RECONSTRUCTION:" + case["id"])
        for arm in scores:
            result = row.get(arm, {})
            obj = result.get("object")
            if obj is None:
                scores[arm]["unknown"] += 1
            elif obj == truth[case["id"]]:
                scores[arm]["correct"] += 1
            else:
                scores[arm]["unsafe"] += 1
            scores[arm]["asks"] += int(result.get("asks", 0))
        scoped = row.get("scoped_restatement", {})
        if case["event"] in CHANGING:
            if case["id"] in {"missing-distinguishing-property","stale-restatement-generation"}:
                if scoped.get("object") is not None or scoped.get("reason") != "UNKNOWN_INVALID_RESTATEMENT":
                    errors.append("INVALID_RESTATEMENT_NOT_UNKNOWN:" + case["id"])
            elif scoped.get("object") != truth[case["id"]] or scoped.get("reason") != "REGROUNDED":
                errors.append("REGROUND_FAILURE:" + case["id"])
        if row.get("authority_granted_by_cue") is not False:
            errors.append("AUTHORITY_LAUNDERING:" + case["id"])
    # Independent comparisons; initial clarification asks once only on initial ambiguity.
    expected_asks = sum(1 for c in fixture["cases"] if c["id"] == "ambiguous-initial-clarified")
    if scores["initial_clarification_only"]["asks"] != expected_asks:
        errors.append("CLARIFICATION_COST")
    report = {
        "status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "errors":errors,"rows":len(by_id),"scores":scores,
        "reconstructed_truth":truth,
        "raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),
        "scope":"authored finite method fixture only; no participant, GUI, app, model, OS input, or effect",
    }
    oracle_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status":report["status"],"errors":len(errors),"rows":len(by_id)}))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
