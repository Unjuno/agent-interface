"""Deterministic protocol validator; not a human-comprehension detector."""


REQUIRED = ("last_verified_effect", "delivery_state", "authority_state",
            "release_state", "forbidden_action")


def scenario_action(prompt):
    if prompt["delivery_state"] == "UNKNOWN":
        return "INSPECT_DELIVERY_RECEIPT"
    if prompt["effect_state"] == "PARTIAL":
        return "INSPECT_UNVERIFIED_FIELD"
    if prompt["effect_state"] == "NO_EFFECT":
        return "REFRESH_TARGET_BEFORE_ANY_RETRY"
    if prompt["effect_state"] == "VERIFIED_COMPLETE":
        return "REPORT_VERIFIED_COMPLETION_ONLY"
    return None


def evaluate(prompt, response):
    # Emergency release is a bypass, not an acceptance/readback prerequisite.
    if prompt.get("emergency_release_required"):
        return "SAFE_STOP_RELEASE_BYPASS"
    fields = response.get("synthesis", {})
    if any(name not in fields for name in REQUIRED):
        return "HOLD_MISSING_CRITICAL_FIELD"
    for name in REQUIRED:
        if fields[name] != prompt[name]:
            return "HOLD_CONTRADICTORY_OR_UNSUPPORTED_FIELD"
    if response.get("next_action") is None:
        return "HOLD_NO_SCENARIO_APPLICATION"
    if response["next_action"] != scenario_action(prompt):
        return "HOLD_UNSAFE_OR_UNSUPPORTED_NEXT_ACTION"
    # This is protocol consistency only; it does not activate authority or certify cognition.
    return "READY_FOR_SEPARATE_ACTIVATION_REVIEW"


def correction_fields(prompt, response):
    """Name fields to re-check against the visible packet; never supplies authority."""
    if prompt.get("emergency_release_required"):
        return []
    fields = response.get("synthesis", {})
    needs_review = [name for name in REQUIRED
                    if name not in fields or fields[name] != prompt[name]]
    if response.get("next_action") != scenario_action(prompt):
        needs_review.append("next_action")
    return needs_review
