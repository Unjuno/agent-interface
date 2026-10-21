def run_trial(case, policy, arm):
    task_input = dict(case["input"])
    if arm == "PRESCRIBED":
        task_input["prescribed_action"] = case["prescription"]

    action = select_action(task_input, policy, arm)
    before = task_input["evidence"]
    after = before
    response = task_input["action_responses"].get(action)
    if action in {"ACQUIRE", "TRANSFORM", "PROBE"} and response and response["safe"]:
        after = response["evidence"]

    if policy == "EVIDENCE_USE_DEFECT" and after != before and action in {"ACQUIRE", "TRANSFORM", "PROBE"}:
        decision = "UNKNOWN"
    elif action == "COMMIT" and before["complete"] and before["representation_usable"] and len(before["decision_set"]) == 1:
        decision = before["decision_set"][0]
    elif after["complete"] and after["representation_usable"] and len(after["decision_set"]) == 1:
        decision = after["decision_set"][0]
    else:
        decision = "UNKNOWN"

    recognition = "UNKNOWN" if policy == "RECOGNITION_DEFECT" else recognize_need(task_input)
    unnecessary = action in {"ACQUIRE", "TRANSFORM", "PROBE"} and before == after
    violation = action in {"ACQUIRE", "TRANSFORM", "PROBE"} and action not in task_input["safe_actions"]
    return {
        "case_id": case["case_id"],
        "policy": policy,
        "arm": arm,
        "recognized_need": recognition,
        "selected_action": action,
        "evidence_before": before,
        "evidence_after": after,
        "action_response": response,
        "final_decision": decision,
        "unnecessary_action": unnecessary,
        "hard_gate_violation": violation,
    }


def run_trials(cases):
    return [
        run_trial(case, policy, arm)
        for case in cases
        for policy in ("REFERENCE", "RECOGNITION_DEFECT", "ACTION_SELECTION_DEFECT", "EVIDENCE_USE_DEFECT", "STOPPING_DEFECT")
        for arm in ("PRESCRIBED", "AVAILABLE", "NO_EPISTEMIC_ACTION")
    ]


def main():
    import json
    import sys
    from pathlib import Path

    cases = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["cases"]
    print(json.dumps({"schema": "epistemic-action-8629-candidate-v1", "rows": run_trials(cases)}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()


def recognize_need(task_input):
    evidence = task_input["evidence"]
    if not evidence["decision_set"]:
        return "UNKNOWN"
    if evidence["complete"] and evidence["representation_usable"] and len(evidence["decision_set"]) == 1:
        return "SUFFICIENT"
    if not evidence["complete"] and "ACQUIRE" in task_input["safe_actions"]:
        return "NEEDS_ACQUISITION"
    if evidence["complete"] and not evidence["representation_usable"] and "TRANSFORM" in task_input["safe_actions"]:
        return "NEEDS_TRANSFORM"
    if not evidence["complete"] and "PROBE" in task_input["safe_actions"]:
        return "NEEDS_PROBE"
    return "BLOCKED_EVIDENCE"


def select_action(case_input, policy, arm):
    if arm == "PRESCRIBED":
        action = case_input["prescribed_action"]
        return action if action in case_input["allowed_actions"] else "YIELD"

    if __package__:
        from .policies import select_action as select
    else:
        from policies import select_action as select

    return select(case_input, policy, arm)
