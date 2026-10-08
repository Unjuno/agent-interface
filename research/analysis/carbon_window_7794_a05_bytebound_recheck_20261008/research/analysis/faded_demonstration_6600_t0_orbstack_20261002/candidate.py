#!/usr/bin/env python3
"""Model-free T0 candidate for safe, optional faded-demonstration eligibility."""
import json
import pathlib
import sys


def evaluate(case):
    receipt = case["receipt"]
    fresh = receipt["source_generation"] == case["current_generation"] == case["source_generation"]
    target_match = case["target_unambiguous"] and case["task_target"] != "UNKNOWN" and receipt["target"] == case["task_target"]
    effect = receipt["effect_status"] == "verified" and target_match and fresh
    safe = effect and receipt["released"] and case["reversible"]
    eligible = safe and case["practice_opt_in"]
    if effect:
        statement = "VERIFIED_OBSERVED_EFFECT"
    else:
        statement = "UNKNOWN_NOT_DEMONSTRATED"
    return {
        "case_id":case["id"],
        "effect_for_task":effect,
        "safe_completion":safe,
        "teaching_step_offered":eligible,
        "statement":statement,
        "coordinate_reused":False,
        "fresh_target_rebind_required":not fresh,
        "skip_available":True,
        "stop_available":True,
        "action_authority_granted":False,
    }


def main():
    fixture=json.loads(pathlib.Path(sys.argv[1]).read_text())
    rows=[evaluate(c) for c in fixture["cases"]]
    pathlib.Path(sys.argv[2]).write_text(json.dumps({"schema":"faded-demo-candidate-v1","rows":rows},sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":"CANDIDATE_COMPLETE","rows":len(rows)}))


if __name__=="__main__":
    main()
