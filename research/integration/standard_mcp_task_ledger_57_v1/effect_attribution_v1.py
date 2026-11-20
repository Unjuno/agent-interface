"""Separate factual task effects from effects eligible as authorized success."""


def adjudicate_effect(*, task_success, effect_observed_ns, authority_expiry_ns,
                      release_received_ns, horizon_end_ns):
    """Classify an independently observed effect against frozen time bounds.

    ``task_success`` remains the factual final-state score. The separate
    ``eligible_task_success`` is true only when that score is true and the
    effect was observed no later than authority expiry. A verified release or
    a finite neutral horizon does not extend input authority.
    """
    if task_success not in (True, False, None) or type(task_success) not in (
            bool, type(None)):
        raise ValueError("task_success must be true, false, or unknown")
    bounds = (authority_expiry_ns, release_received_ns, horizon_end_ns)
    if any(type(value) is not int or value < 0 for value in bounds):
        raise ValueError("authority, release, and horizon times must be nonnegative integers")
    if not authority_expiry_ns <= release_received_ns <= horizon_end_ns:
        raise ValueError("time bounds must satisfy expiry <= release <= horizon")
    if effect_observed_ns is not None and (
            type(effect_observed_ns) is not int or effect_observed_ns < 0):
        raise ValueError("effect time must be a nonnegative integer or unknown")

    if effect_observed_ns is None:
        timing = "unknown"
    elif effect_observed_ns <= authority_expiry_ns:
        timing = "within_authority"
    elif effect_observed_ns <= release_received_ns:
        timing = "after_authority_before_release"
    elif effect_observed_ns <= horizon_end_ns:
        timing = "after_release_within_horizon"
    else:
        timing = "after_release_horizon"

    if task_success is not True:
        eligible = task_success
    elif timing == "within_authority":
        eligible = True
    elif timing == "unknown":
        eligible = None
    else:
        eligible = False

    return {
        "factual_task_success": task_success,
        "effect_timing": timing,
        "eligible_task_success": eligible,
    }
