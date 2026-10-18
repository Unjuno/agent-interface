def generate_cases(seed):
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    scenarios = (
        ({"complete": False, "decision_set": ["APPROVE", "DENY"], "representation_usable": True}, ["ACQUIRE", "COMMIT", "YIELD"], ["ACQUIRE"], "APPROVE", "ACQUIRE"),
        ({"complete": True, "decision_set": ["EXPORT", "BLOCK"], "representation_usable": False}, ["TRANSFORM", "COMMIT", "YIELD"], ["TRANSFORM"], "EXPORT", "TRANSFORM"),
        ({"complete": False, "decision_set": ["KEEP", "DISCARD"], "representation_usable": True}, ["PROBE", "COMMIT", "YIELD"], ["PROBE"], "KEEP", "PROBE"),
        ({"complete": True, "decision_set": ["KEEP"], "representation_usable": True}, ["COMMIT", "PROBE", "YIELD"], ["PROBE"], "KEEP", "COMMIT"),
        ({"complete": False, "decision_set": ["ALLOW", "DENY"], "representation_usable": True}, ["PROBE", "YIELD"], [], "UNKNOWN", "YIELD"),
        ({"complete": False, "decision_set": [], "representation_usable": False}, ["COMMIT", "YIELD"], [], "UNKNOWN", "YIELD"),
    )
    cases = []
    for index in range(12):
        family = index // 2
        evidence, actions, safe_actions, decision, epistemic_action = scenarios[family]
        receipt = f"receipt-{seed}-{index:02d}"
        initial_evidence = {
            **evidence,
            "provenance": [receipt] if evidence["decision_set"] else [],
        }
        action_responses = {}
        action_by_family = ("ACQUIRE", "TRANSFORM", "PROBE", "PROBE", "PROBE", None)[family]
        if action_by_family:
            after = dict(initial_evidence)
            after["provenance"] = list(initial_evidence["provenance"])
            if family == 0:
                after.update(complete=True, decision_set=["APPROVE"])
            elif family == 1:
                after.update(representation_usable=True, decision_set=["EXPORT"])
            elif family == 2:
                after.update(complete=True, decision_set=["KEEP"])
            if family in {0, 1, 2}:
                receipt_kind = {"ACQUIRE": "acquired", "TRANSFORM": "transformed", "PROBE": "probed"}[action_by_family]
                after["provenance"].append(f"{receipt_kind}-{seed}-{index:02d}")
            action_responses[action_by_family] = {
                "safe": family != 4,
                "evidence": after,
            }
        cases.append(
            {
                "case_id": f"S{seed}-C{index:02d}",
                "input": {
                    "allowed_actions": list(actions),
                    "safe_actions": list(safe_actions),
                    "evidence": initial_evidence,
                    "action_responses": action_responses,
                },
                "truth": {
                    "decision": decision,
                    "epistemic_action": epistemic_action,
                    "need": ("NEEDS_ACQUISITION", "NEEDS_TRANSFORM", "NEEDS_PROBE", "SUFFICIENT", "BLOCKED_EVIDENCE", "UNKNOWN")[family],
                },
            }
        )
    return cases
