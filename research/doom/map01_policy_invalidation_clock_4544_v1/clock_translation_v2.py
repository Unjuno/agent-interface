"""Fail-closed clock translation preserving enriched monitor receipts."""

from copy import deepcopy

SCHEMA = "policy-invalidation-clock-translation-v2"
MAX_UNCERTAINTY_NS = 1_000_000_000
MAX_SAMPLE_AGE_NS = 5_000_000_000
RECEIPT_FIELDS = {"timestamp_domain", "outcome_evaluated_ns", "outcome"}


def translate_invalidation(receipt, calibration):
    """Translate one host event while retaining every monitor-supplied field."""
    if type(receipt) is not dict or not RECEIPT_FIELDS.issubset(receipt):
        raise ValueError("host invalidation receipt fields required")
    if receipt["timestamp_domain"] != "host_monotonic_ns":
        raise ValueError("invalidation timestamp is not host monotonic time")
    host_ns = receipt["outcome_evaluated_ns"]
    if type(host_ns) is not int or host_ns < 0:
        raise ValueError("host invalidation timestamp must be a nonnegative integer")
    outcome = receipt["outcome"]
    if (type(outcome) is not dict or outcome.get("status") in
            (None, "UNCHANGED", "VALID", "SOFT_CHANGED") or
            outcome.get("requires_new_decision") is not True or
            outcome.get("grants_input_authority") is not False):
        raise ValueError("authority-reducing invalidation receipt required")
    if (type(calibration) is not dict or
            calibration.get("schema") != SCHEMA or
            calibration.get("same_session") is not True or
            calibration.get("host_domain") != "host_monotonic_ns" or
            calibration.get("runtime_domain") != "runtime_monotonic_ns"):
        raise ValueError("same-session host/runtime calibration required")
    samples = calibration.get("samples")
    if type(samples) is not list or len(samples) != 3:
        raise ValueError("exactly three clock-offset samples required")
    lowers, uppers, receives = [], [], []
    for sample in samples:
        if type(sample) is not dict:
            raise ValueError("malformed clock-offset sample")
        send, receive, runtime = (sample.get("host_send_ns"),
                                  sample.get("host_receive_ns"),
                                  sample.get("runtime_ns"))
        if any(type(x) is not int or x < 0 for x in (send, receive, runtime)):
            raise ValueError("clock-offset sample timestamps must be integers")
        if send > receive:
            raise ValueError("clock sample host interval is reversed")
        lowers.append(runtime - receive)
        uppers.append(runtime - send)
        receives.append(receive)
    lower, upper = min(lowers), max(uppers)
    if upper - lower > MAX_UNCERTAINTY_NS:
        raise ValueError("HOLD: clock-offset uncertainty exceeds one second")
    calibrated_host_ns = max(receives)
    age = calibrated_host_ns - host_ns
    if age < 0 or age > MAX_SAMPLE_AGE_NS:
        raise ValueError("HOLD: invalidation timestamp outside calibration age")

    runtime_receipt = deepcopy(receipt)
    runtime_receipt["timestamp_domain"] = "runtime_monotonic_ns"
    runtime_receipt["outcome_evaluated_ns"] = host_ns + lower
    record = {
        "schema": SCHEMA,
        "source_receipt": deepcopy(receipt),
        "runtime_receipt": deepcopy(runtime_receipt),
        "host_timestamp_ns": host_ns,
        "runtime_timestamp_ns": host_ns + lower,
        "offset_lower_ns": lower,
        "offset_upper_ns": upper,
        "calibrated_host_ns": calibrated_host_ns,
        "calibration_age_ns": age,
        "calibration_samples": deepcopy(samples),
        "same_session": True,
        "input_authority_admitted": False,
    }
    return record, runtime_receipt
