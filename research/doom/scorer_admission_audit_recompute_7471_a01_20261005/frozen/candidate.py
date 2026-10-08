"""Fail-closed scorer progress attribution for an admitted recovery interval."""


def classify_progress(samples, admitted_ns, first_input_ns, *, max_gap_ns, missed_periods=0):
    """Classify whether a positive score sample is admission-bracketed.

    This is a policy oracle for construction only. It does not estimate the
    exact event time; it only requires a baseline after admission and before
    the first input, then bounds the time to the positive sample.
    """
    if type(admitted_ns) is not int or type(first_input_ns) is not int:
        raise TypeError("admission and first-input timestamps must be integers")
    if type(max_gap_ns) is not int or max_gap_ns <= 0:
        raise ValueError("max_gap_ns must be a positive integer")
    if type(missed_periods) is not int or missed_periods < 0:
        raise ValueError("missed_periods must be a non-negative integer")
    if admitted_ns >= first_input_ns:
        return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "invalid_admission_bracket"}
    if missed_periods != 0:
        return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "missed_sample_periods"}
    if not samples or any(
        type(ns) is not int or type(score) is not int or score < 0
        for ns, score in samples
    ):
        return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "invalid_samples"}
    if any(right[0] <= left[0] for left, right in zip(samples, samples[1:])):
        return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "sample_clock_invalid"}

    baseline = next(
        ((ns, score) for ns, score in samples if admitted_ns < ns < first_input_ns),
        None,
    )
    if baseline is None:
        return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "no_post_admission_pre_input_baseline"}

    for ns, score in samples:
        if ns <= first_input_ns:
            continue
        if ns - baseline[0] > max_gap_ns:
            return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "positive_sample_gap_exceeded"}
        if score > baseline[1]:
            return {
                "decision": "ADMISSION_BRACKETED_PROGRESS",
                "baseline_ns": baseline[0],
                "positive_sample_ns": ns,
                "gap_ns": ns - baseline[0],
            }
    return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "no_bounded_positive_sample"}
