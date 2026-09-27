"""Translate a production-shaped host monitor receipt without dropping metadata."""
from copy import deepcopy
import math


MAX_UNCERTAINTY_NS = 1_000_000_000
MAX_CALIBRATION_AGE_NS = 5_000_000_000
ENVELOPE_FIELDS = {
    "sequence", "signal", "outcome", "monitor_received_ns",
    "signal_extracted_ns", "outcome_evaluated_ns",
    "signal_extraction_ms", "outcome_evaluation_ms",
}
OUTCOME_FIELDS = {
    "format", "guard_id", "signal_id", "status", "reason",
    "source_value", "current_value", "hard_minimum", "source_age_ms",
    "keep_existing_policy", "requires_new_decision", "grants_input_authority",
    "may_only_preserve_or_reduce_existing_authority",
    "semantic_change_identified", "task_success_verified",
}


def _positive_int(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f"positive integer {name} required")


def translate_monitor_receipt(receipt, calibration, session_id, *,
                              source_clock_domain, now_host_ns):
    """Translate just outcome_evaluated_ns; retain the complete source envelope.

    The monitor API stamps all three stage timestamps with host
    time.perf_counter_ns(). `source_clock_domain` is therefore an explicit
    caller assertion, not inferred from timestamp magnitudes.
    """
    if source_clock_domain != "host_monotonic":
        raise ValueError("host_monotonic source clock domain required")
    if type(receipt) is not dict or not ENVELOPE_FIELDS <= set(receipt):
        raise ValueError("production monitor receipt envelope required")
    _positive_int(receipt.get("sequence"), "sequence")
    for field in ("monitor_received_ns", "signal_extracted_ns",
                  "outcome_evaluated_ns"):
        _positive_int(receipt.get(field), field)
    if not (receipt["monitor_received_ns"] <= receipt["signal_extracted_ns"]
            <= receipt["outcome_evaluated_ns"]):
        raise ValueError("monitor stage timestamps must be ordered")
    for field in ("signal_extraction_ms", "outcome_evaluation_ms"):
        value = receipt.get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("nonnegative monitor stage durations required")
    if type(receipt.get("signal")) is not dict:
        raise ValueError("monitor signal mapping required")
    outcome = receipt.get("outcome")
    if type(outcome) is not dict or not OUTCOME_FIELDS <= set(outcome):
        raise ValueError("monitor outcome semantic fields required")
    if outcome["format"] != "observable-signal-guard-outcome-v1":
        raise ValueError("supported monitor outcome format required")
    if outcome["status"] not in {"HARD_INVALIDATED", "UNKNOWN"}:
        raise ValueError("policy-invalidating monitor outcome required")
    if (outcome["requires_new_decision"] is not True or
            outcome["keep_existing_policy"] is not False or
            outcome["grants_input_authority"] is not False or
            outcome["may_only_preserve_or_reduce_existing_authority"] is not True or
            outcome["task_success_verified"] is not False):
        raise ValueError("one-way invalidation semantics required")

    if (type(calibration) is not dict or
            calibration.get("clock_domain") != "same_session_host_runtime_monotonic" or
            calibration.get("session_id") != session_id or
            calibration.get("probe_count") != 3 or
            calibration.get("host_clock_domain") != "host_monotonic" or
            calibration.get("runtime_clock_domain") != "runtime_monotonic" or
            type(calibration.get("samples")) is not list or
            len(calibration["samples"]) != 3 or
            type(calibration.get("offset_lower_ns")) is not int or
            type(calibration.get("offset_upper_ns")) is not int or
            type(calibration.get("sampled_host_ns")) is not int):
        raise ValueError("fresh same-session three-probe calibration required")
    _positive_int(now_host_ns, "current host monotonic time")
    sample_lowers = []
    sample_uppers = []
    previous_send_ns = 0
    for sample in calibration["samples"]:
        if (type(sample) is not dict or
                type(sample.get("host_send_ns")) is not int or
                type(sample.get("runtime_ns")) is not int or
                type(sample.get("host_receive_ns")) is not int):
            raise ValueError("three complete clock probe samples required")
        host_send_ns = sample["host_send_ns"]
        runtime_ns = sample["runtime_ns"]
        host_receive_ns = sample["host_receive_ns"]
        if (host_send_ns <= previous_send_ns or runtime_ns <= 0 or
                host_receive_ns < host_send_ns):
            raise ValueError("ordered same-session clock probe samples required")
        previous_send_ns = host_send_ns
        sample_lowers.append(runtime_ns - host_receive_ns)
        sample_uppers.append(runtime_ns - host_send_ns)
    if (calibration["offset_lower_ns"] != min(sample_lowers) or
            calibration["offset_upper_ns"] != max(sample_uppers) or
            calibration["sampled_host_ns"] != calibration["samples"][-1]["host_receive_ns"]):
        raise ValueError("calibration bounds must match all three retained probes")
    lower = calibration["offset_lower_ns"]
    upper = calibration["offset_upper_ns"]
    if lower > upper:
        raise ValueError("ordered offset interval required")
    if upper - lower > MAX_UNCERTAINTY_NS:
        raise ValueError("clock calibration uncertainty exceeds 1 second")
    age_ns = now_host_ns - calibration["sampled_host_ns"]
    if age_ns < 0 or age_ns > MAX_CALIBRATION_AGE_NS:
        raise ValueError("clock calibration is future-dated or older than 5 seconds")

    host_ns = receipt["outcome_evaluated_ns"]
    converted_ns = host_ns + upper  # latest possible runtime-domain boundary
    if converted_ns <= 0:
        raise ValueError("translated runtime timestamp must be positive")

    result = deepcopy(receipt)
    result["outcome_evaluated_ns"] = converted_ns
    result["outcome_evaluated_host_ns"] = host_ns
    result["outcome_clock_domain"] = "runtime_monotonic"
    result["monitor_received_clock_domain"] = "host_monotonic"
    result["signal_extracted_clock_domain"] = "host_monotonic"
    result["signal_capture_clock_domain"] = "runtime_monotonic"
    result["clock_translation"] = {
        "session_id": session_id,
        "source_clock_domain": "host_monotonic",
        "target_clock_domain": "runtime_monotonic",
        "translated_field": "outcome_evaluated_ns",
        "preserved_host_timestamp_field": "outcome_evaluated_host_ns",
        "untouched_host_timestamp_fields": [
            "monitor_received_ns", "signal_extracted_ns"],
        "untouched_runtime_timestamp_fields": ["signal.capture_ns"],
        "probe_count": 3,
        "sampled_host_ns": calibration["sampled_host_ns"],
        "calibration_age_ns": age_ns,
        "offset_lower_ns": lower,
        "offset_upper_ns": upper,
        "uncertainty_width_ns": upper - lower,
        "samples": deepcopy(calibration["samples"]),
        "mapping_bound": "latest_possible_runtime_time",
    }
    return result
