"""Adapter from windowed any-key occupancy v1 to the matched-runner schema.

This module deliberately treats missing or ambiguous release evidence as invalid,
never as zero retained input. Simultaneous keys are unioned by the retained
container_interruption_v1 occupancy implementation.
"""
from __future__ import annotations


def fallback_input_bounds(events, identifier, planner_window):
    from container_interruption_v1.occupancy import analyze_program, EvidenceError

    try:
        result = analyze_program(
            events,
            identifier,
            planner_window.start_ns,
            planner_window.end_ns,
        )
    except EvidenceError as exc:
        return {
            "intent_token": None,
            "valid": False,
            "invalid": [str(exc)],
            "planner_wait_ns": planner_window.duration_ns,
            "retained_input_lower_bound_ns": None,
            "retained_input_upper_bound_ns": None,
            "no_retained_input_lower_bound_ns": None,
            "no_retained_input_upper_bound_ns": None,
            "admission_count": None,
            "release_count": None,
            "measurement_class": "INVALID_EVIDENCE",
        }

    return {
        "intent_token": result["intent_token"],
        "valid": True,
        "invalid": [],
        "planner_wait_ns": result["window_ns"],
        "retained_input_lower_bound_ns": result["retained_lower_ns"],
        "retained_input_upper_bound_ns": result["retained_upper_ns"],
        "no_retained_input_lower_bound_ns": result["no_input_lower_ns"],
        "no_retained_input_upper_bound_ns": result["no_input_upper_ns"],
        "admission_count": result["admission_count"],
        "release_count": result["explicit_release_count"],
        "measurement_class": result["measurement_class"],
    }
