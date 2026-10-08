"""Issue #4544 enriched monitor receipt translation, offline only."""
from copy import deepcopy

from research.doom.map01_policy_invalidation_clock_4536_v1.policy_clock import (
    translate_policy_invalidation,
)


MAX_UNCERTAINTY_NS = 1_000_000_000
MAX_AGE_NS = 5_000_000_000
MONITOR_FIELDS = {
    "sequence", "signal", "outcome", "monitor_received_ns",
    "signal_extracted_ns", "outcome_evaluated_ns",
    "signal_extraction_ms", "outcome_evaluation_ms",
}


def _integer(value):
    return type(value) is int and value >= 0


def translate_enriched_receipt(receipt, calibration_record, session_id,
                               controller_decided_host_ns):
    """Translate a source-shaped monitor event, preserving its full envelope."""
    if type(receipt) is not dict or not MONITOR_FIELDS <= set(receipt):
        raise ValueError("production monitor receipt fields required")
    if (type(receipt["signal"]) is not dict or
            type(receipt["outcome"]) is not dict or
            receipt["outcome"].get("status") not in
            ("HARD_INVALIDATED", "UNKNOWN") or
            receipt["outcome"].get("requires_new_decision") is not True or
            receipt["outcome"].get("grants_input_authority") is not False):
        raise ValueError("authority-reducing invalidation required")
    times = [receipt[name] for name in
             ("monitor_received_ns", "signal_extracted_ns", "outcome_evaluated_ns")]
    if not all(_integer(value) for value in times) or times != sorted(times):
        raise ValueError("ordered host monotonic monitor timestamps required")
    if (not _integer(controller_decided_host_ns) or
            receipt["outcome_evaluated_ns"] > controller_decided_host_ns):
        raise ValueError("invalidation must precede host controller decision")
    if type(calibration_record) is not dict:
        raise ValueError("clock calibration record required")
    if calibration_record.get("session_id") != session_id:
        raise ValueError("clock probe session binding mismatch")
    samples = calibration_record.get("samples")
    if type(samples) is not list or len(samples) != 3:
        raise ValueError("exactly three clock probes required")
    lows, highs, endpoints = [], [], []
    for sample in samples:
        if type(sample) is not dict:
            raise ValueError("clock probe object required")
        host_receive = sample.get("host_receive_ns")
        host_send = sample.get("host_send_ns")
        lower = sample.get("offset_lower_ns")
        upper = sample.get("offset_upper_ns")
        runtime = sample.get("runtime_ns")
        if (not all(_integer(x) for x in (host_receive, host_send, runtime)) or
                type(lower) is not int or type(upper) is not int or
                host_send > host_receive or lower > upper):
            raise ValueError("malformed clock probe")
        lows.append(lower)
        highs.append(upper)
        endpoints.append(host_receive)
    lower, upper = min(lows), max(highs)
    if upper - lower > MAX_UNCERTAINTY_NS:
        raise ValueError("clock uncertainty exceeds one second")
    if abs(receipt["outcome_evaluated_ns"] - max(endpoints)) > MAX_AGE_NS:
        raise ValueError("clock probe is stale for receipt")
    calibration = {
        "clock_domain": "same_session_host_runtime_monotonic",
        "session_id": session_id,
        "offset_lower_ns": lower,
        "offset_upper_ns": upper,
    }
    translated = translate_policy_invalidation(receipt, calibration, session_id)
    # Keep explicit provenance; the helper also retains every unknown field.
    translated["receipt_origin"] = "synthetic_monitor_event_missing_from_predecessor"
    return deepcopy(translated)
