"""Conservative host-to-runtime translation for a policy invalidation receipt."""
from copy import deepcopy


MAX_UNCERTAINTY_NS = 1_000_000_000


def translate_policy_invalidation(receipt, calibration, session_id):
    """Return a receipt with its boundary translated, retaining provenance.

    `offset_lower_ns`/`offset_upper_ns` bound runtime_monotonic - host_monotonic.
    The upper offset yields the latest possible runtime time, so a subsequent
    ordering check cannot pass merely because the lower bound understated age.
    """
    required = {"outcome_evaluated_ns", "outcome"}
    if type(receipt) is not dict or not required <= set(receipt):
        raise ValueError("exact policy-invalidation receipt required")
    host_ns = receipt["outcome_evaluated_ns"]
    if type(host_ns) is not int or host_ns < 0:
        raise ValueError("host invalidation timestamp must be a monotonic integer")
    if (type(calibration) is not dict or
            calibration.get("clock_domain") != "same_session_host_runtime_monotonic" or
            calibration.get("session_id") != session_id or
            type(calibration.get("offset_lower_ns")) is not int or
            type(calibration.get("offset_upper_ns")) is not int or
            calibration["offset_lower_ns"] > calibration["offset_upper_ns"]):
        raise ValueError("same-session bounded clock calibration required")
    width = calibration["offset_upper_ns"] - calibration["offset_lower_ns"]
    if width > MAX_UNCERTAINTY_NS:
        raise ValueError("clock calibration uncertainty exceeds 1 second")
    converted = host_ns + calibration["offset_upper_ns"]
    if converted < 0:
        raise ValueError("translated runtime timestamp is invalid")

    result = deepcopy(receipt)
    result["outcome_evaluated_ns"] = converted
    result["outcome_evaluated_host_ns"] = host_ns
    result["outcome_clock_domain"] = "runtime_monotonic"
    result["clock_translation"] = {
        "session_id": session_id,
        "host_clock_domain": "host_monotonic",
        "runtime_clock_domain": "runtime_monotonic",
        "offset_lower_ns": calibration["offset_lower_ns"],
        "offset_upper_ns": calibration["offset_upper_ns"],
        "uncertainty_width_ns": width,
        "mapping_bound": "latest_possible_runtime_time",
    }
    return result
