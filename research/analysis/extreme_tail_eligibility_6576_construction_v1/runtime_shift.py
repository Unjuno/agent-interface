"""Deterministic runtime-envelope shift monitor boundary for Issue #6576.

This is a synthetic contract probe, not a calibrated statistical detector.
It makes pre-alarm misses and deadline adequacy explicit instead of treating
eventual detection as protection.
"""

from __future__ import annotations

import math


def assess_shift(
    reference: list[float],
    deployed: list[float],
    *,
    safety_deadline: float,
    alarm_run: int,
    threshold: float,
) -> dict:
    """Assess a frozen simple shift rule on an already ordered trace.

    A run of ``alarm_run`` consecutive above-threshold observations alarms at
    the last observation in the run. All preceding above-deadline outcomes are
    counted as pre-alarm misses. No adaptive threshold fitting occurs here.
    """
    if (
        not reference
        or not deployed
        or any(not math.isfinite(value) or value < 0 for value in reference + deployed)
        or safety_deadline <= 0
        or alarm_run < 1
        or threshold <= 0
    ):
        raise ValueError("invalid trace or frozen shift-gate configuration")

    reference_exceedances = sum(value > threshold for value in reference)
    alarm_index = None
    run = 0
    for index, value in enumerate(deployed):
        run = run + 1 if value > threshold else 0
        if run >= alarm_run:
            alarm_index = index
            break

    pre_alarm = deployed if alarm_index is None else deployed[:alarm_index]
    misses = sum(value > safety_deadline for value in pre_alarm)
    return {
        "reference_false_alarms": reference_exceedances,
        "alarm_index": alarm_index,
        "detection_delay_observations": None if alarm_index is None else alarm_index + 1,
        "pre_alarm_deadline_misses": misses,
        "protection_adequate": alarm_index is not None and misses == 0,
        "post_shift_decision": "NOT_ESTIMABLE_NEW_MODE" if alarm_index is not None else "NOT_ESTIMABLE_ALARM_NOT_TRIGGERED",
    }
