def select_action(case_input, policy, arm):
    if policy not in {"REFERENCE", "STOPPING_DEFECT", "ACTION_SELECTION_DEFECT", "RECOGNITION_DEFECT", "EVIDENCE_USE_DEFECT"}:
        raise ValueError("unknown policy")
    if arm not in {"PRESCRIBED", "AVAILABLE", "NO_EPISTEMIC_ACTION"}:
        raise ValueError("unknown arm")

    allowed = set(case_input["allowed_actions"])
    evidence = case_input["evidence"]
    if arm == "PRESCRIBED":
        prescribed = case_input.get("prescribed_action")
        return prescribed if prescribed in allowed else "YIELD"
    if arm == "NO_EPISTEMIC_ACTION":
        allowed.intersection_update({"COMMIT", "YIELD"})

    if not evidence["decision_set"]:
        return "YIELD"
    if evidence["complete"] and evidence["representation_usable"] and len(evidence["decision_set"]) == 1:
        if policy == "STOPPING_DEFECT" and "PROBE" in allowed and "PROBE" in case_input["safe_actions"]:
            return "PROBE"
        return "COMMIT" if "COMMIT" in allowed else "YIELD"

    for action in ("ACQUIRE", "TRANSFORM", "PROBE"):
        if action in allowed and action in case_input["safe_actions"]:
            if policy == "ACTION_SELECTION_DEFECT" and arm == "AVAILABLE":
                return "YIELD"
            return action
    return "YIELD"
