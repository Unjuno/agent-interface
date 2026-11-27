"""Bounded independent same-target input-neutral observation.

This is runner-side evidence only. It does not certify application-queue
quiescence or task success; those require separate receipts/oracles.
"""
from __future__ import annotations

import time


def observe_neutral_horizon(*, read_input_state, read_identity,
                            read_generation, expected_identity,
                            expected_generation, horizon_ns=2_000_000_000,
                            max_sample_gap_ns=100_000_000,
                            max_read_bracket_ns=20_000_000,
                            total_budget_ns=3_000_000_000,
                            clock_ns=time.perf_counter_ns,
                            sleep_ns=time.sleep):
    """Verify continuous mouse-left/W-up reads for a bounded horizon.

    The neutral interval begins at the return of its first fully read sample.
    Any down sample restarts that interval. A generation/identity change,
    malformed sample, read error, oversized bracket/gap, or exhausted total
    budget returns UNKNOWN. The function never sends input or closes a target.
    """
    if (not callable(read_input_state) or not callable(read_identity)
            or not callable(read_generation) or not callable(clock_ns)
            or not callable(sleep_ns)):
        raise ValueError("readers, clock, and sleep must be callable")
    for name, value in (("horizon_ns", horizon_ns),
                        ("max_sample_gap_ns", max_sample_gap_ns),
                        ("max_read_bracket_ns", max_read_bracket_ns),
                        ("total_budget_ns", total_budget_ns)):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if total_budget_ns < horizon_ns:
        raise ValueError("total budget must cover the requested horizon")

    started = clock_ns()
    neutral_since = None
    prior_after = None
    samples = []
    max_gap = 0

    def result(status, reason, **extra):
        return {"status": status, "reason": reason,
                "started_ns": started, "ended_ns": clock_ns(),
                "horizon_ns": horizon_ns, "sample_count": len(samples),
                "max_sample_gap_ns": max_gap,
                "samples": samples, **extra}

    try:
        identity_before = read_identity()
        generation_before = read_generation()
        if (identity_before != expected_identity
                or generation_before != expected_generation):
            return result("UNKNOWN", "initial_identity_or_generation_mismatch",
                          identity_before=identity_before,
                          generation_before=generation_before)
        while clock_ns() - started <= total_budget_ns:
            identity_sample = read_identity()
            generation_sample = read_generation()
            if (identity_sample != expected_identity
                    or generation_sample != expected_generation):
                return result("UNKNOWN", "identity_or_generation_changed_during_horizon",
                              identity_sample=identity_sample,
                              generation_sample=generation_sample)
            before = clock_ns()
            state = read_input_state()
            after = clock_ns()
            if type(state) is not dict or any(type(state.get(key)) is not bool
                    for key in ("LEFT_BUTTON_down", "W_key_down")):
                return result("UNKNOWN", "malformed_input_state")
            bracket = after - before
            if bracket < 0 or bracket > max_read_bracket_ns:
                return result("UNKNOWN", "read_bracket_out_of_bounds",
                              last_bracket_ns=bracket)
            gap = after - prior_after if prior_after is not None else 0
            max_gap = max(max_gap, gap)
            if gap > max_sample_gap_ns:
                return result("UNKNOWN", "sample_gap_exceeded",
                              last_gap_ns=gap)
            down = state["LEFT_BUTTON_down"] or state["W_key_down"]
            samples.append({"before_ns": before, "after_ns": after,
                            "gap_from_previous_ns": gap,
                            "identity": identity_sample,
                            "generation": generation_sample,
                            "LEFT_BUTTON_down": state["LEFT_BUTTON_down"],
                            "W_key_down": state["W_key_down"]})
            prior_after = after
            if down:
                neutral_since = None
            elif neutral_since is None:
                neutral_since = after
            elif after - neutral_since >= horizon_ns:
                identity_after = read_identity()
                generation_after = read_generation()
                if (identity_after != expected_identity
                        or generation_after != expected_generation):
                    return result("UNKNOWN", "final_identity_or_generation_mismatch",
                                  neutral_since_ns=neutral_since,
                                  identity_after=identity_after,
                                  generation_after=generation_after)
                return result("VERIFIED", "continuous_neutral_horizon",
                              neutral_since_ns=neutral_since,
                              identity_before=identity_before,
                              identity_after=identity_after,
                              generation_before=generation_before,
                              generation_after=generation_after)
            remaining = total_budget_ns - (clock_ns() - started)
            if remaining <= 0:
                break
            sleep_ns(min(10_000_000, remaining) / 1_000_000_000)
    except Exception as error:
        return result("UNKNOWN", "observation_error",
                      error_type=type(error).__name__)
    return result("UNKNOWN", "total_observation_budget_exhausted",
                  neutral_since_ns=neutral_since)
