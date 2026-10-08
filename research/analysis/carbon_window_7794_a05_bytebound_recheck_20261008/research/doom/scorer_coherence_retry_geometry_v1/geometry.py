"""Timing geometry for immediate coherence retries; standard library only."""
from __future__ import annotations

T_NS = round(1_000_000_000 / 35.0)
GRID_STEP_NS = 1_000
ATTEMPTS = 3


def validate_span(span_ns: int) -> None:
    if type(span_ns) is not int or span_ns <= 0:
        raise ValueError("span_ns must be a positive integer")


def attempt_fails(phase_ns: int, span_ns: int, period_ns: int = T_NS) -> bool:
    validate_span(span_ns)
    if not (0 <= phase_ns < period_ns):
        raise ValueError("phase outside one period")
    if span_ns >= period_ns:
        return True
    return phase_ns + span_ns >= period_ns


def all_attempts_fail(phase_ns: int, span_ns: int, attempts: int = ATTEMPTS, period_ns: int = T_NS) -> bool:
    validate_span(span_ns)
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts must be positive integer")
    phase = phase_ns
    for _ in range(attempts):
        if not attempt_fails(phase, span_ns, period_ns):
            return False
        phase = (phase + span_ns) % period_ns
    return True


def grid_failure_phases(span_ns: int, attempts: int = ATTEMPTS, period_ns: int = T_NS, step_ns: int = GRID_STEP_NS) -> list[int]:
    validate_span(span_ns)
    if type(step_ns) is not int or step_ns <= 0:
        raise ValueError("step_ns must be positive integer")
    return [p for p in range(0, period_ns, step_ns) if all_attempts_fail(p, span_ns, attempts, period_ns)]


def _circular_failure_intervals(span_ns: int, shift_ns: int, period_ns: int) -> list[tuple[int, int]]:
    """Independent interval representation for one attempt's failing start phases.

    Returns half-open integer intervals [lo, hi) over [0, period_ns). Endpoint
    conventions affect only measure-zero phases; the frozen boundary cases are
    also checked by the discrete simulator.
    """
    validate_span(span_ns)
    if span_ns >= period_ns:
        return [(0, period_ns)]
    length = span_ns
    start = (period_ns - span_ns - (shift_ns % period_ns)) % period_ns
    end = start + length
    if end <= period_ns:
        return [(start, end)]
    return [(start, period_ns), (0, end - period_ns)]


def _intersect(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for alo, ahi in a:
        for blo, bhi in b:
            lo, hi = max(alo, blo), min(ahi, bhi)
            if lo < hi:
                out.append((lo, hi))
    out.sort()
    merged: list[tuple[int, int]] = []
    for lo, hi in out:
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def continuous_all_failure_intervals(span_ns: int, attempts: int = ATTEMPTS, period_ns: int = T_NS) -> list[tuple[int, int]]:
    validate_span(span_ns)
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts must be positive integer")
    current = [(0, period_ns)]
    for k in range(attempts):
        current = _intersect(current, _circular_failure_intervals(span_ns, k * span_ns, period_ns))
        if not current:
            break
    return current


def interval_measure(intervals: list[tuple[int, int]]) -> int:
    return sum(hi - lo for lo, hi in intervals)


def guaranteed(span_ns: int, attempts: int = ATTEMPTS, period_ns: int = T_NS) -> bool:
    return not continuous_all_failure_intervals(span_ns, attempts, period_ns)
