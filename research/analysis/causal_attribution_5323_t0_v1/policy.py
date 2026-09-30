POLICIES = ("POSTHOC_ASSOCIATION", "TEMPORAL_LINEAGE", "CONTROL_BASELINE", "CAUSAL_MODEL", "UNKNOWN_ON_CONFOUNDING")


def classify(case, policy):
    if not case["observed_effect"]:
        return "NO_EFFECT"
    if policy == "POSTHOC_ASSOCIATION":
        return "CAUSAL_EFFECT_IDENTIFIED" if case["attempted"] else "NO_EFFECT"
    if policy == "TEMPORAL_LINEAGE":
        if case["attempted"] and case["receipt_before_observation"] and not case["competing_cause_known"] and not case["interference"]:
            return "CAUSAL_EFFECT_IDENTIFIED"
        return "ATTRIBUTION_UNKNOWN"
    if policy == "CONTROL_BASELINE":
        if not case["control_known"]:
            return "ATTRIBUTION_UNKNOWN"
        if case["attempted"] and case["action_succeeded"] and not case["control_effect"] and not case["interference"]:
            return "EFFECT_LINKED_UNDER_CONTROL_ASSUMPTIONS"
        return "ATTRIBUTION_UNKNOWN"
    if policy == "CAUSAL_MODEL":
        if not case["graph_complete"]:
            return "ATTRIBUTION_UNKNOWN"
        return "CAUSAL_EFFECT_IDENTIFIED" if case["ground_truth"] == "action" else "ATTRIBUTION_UNKNOWN"
    if policy == "UNKNOWN_ON_CONFOUNDING":
        if case["competing_cause_known"] or case["interference"] or not case["graph_complete"] or not case["control_known"]:
            return "ATTRIBUTION_UNKNOWN"
        if case["attempted"] and case["action_succeeded"] and not case["control_effect"]:
            return "CAUSAL_EFFECT_IDENTIFIED"
        return "ATTRIBUTION_UNKNOWN"
    raise ValueError(f"unknown policy: {policy}")
