from __future__ import annotations


def _normalize_closed_interval(start: int, end: int, period: int):
    if period <= 0:
        raise ValueError('period must be positive')
    start %= period
    end %= period
    if start <= end:
        return [(start, end)]
    return [(0, end), (start, period - 1)]


def _intersect(a, b):
    out = []
    for a0, a1 in a:
        for b0, b1 in b:
            lo = max(a0, b0)
            hi = min(a1, b1)
            if lo <= hi:
                out.append((lo, hi))
    if not out:
        return []
    out.sort()
    merged = [list(out[0])]
    for lo, hi in out[1:]:
        if lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return [tuple(x) for x in merged]


def failure_phase_intervals(period: int, span: int, attempts: int):
    """Exact integer starting phases for which every immediate attempt crosses a tic.

    Phase is an integer in [0, period-1]. Attempt j starts at
    (phase + j*span) mod period. For 0 < span <= period, an attempt fails iff
    its start phase is in [period-span, period-1], a set of exactly span phases.
    """
    if period <= 0:
        raise ValueError('period must be positive')
    if attempts <= 0:
        raise ValueError('attempts must be positive')
    if span <= 0:
        raise ValueError('span must be positive')
    if span >= period:
        return [(0, period - 1)]

    current = [(0, period - 1)]
    for j in range(attempts):
        lo = period - span - j * span
        hi = period - 1 - j * span
        failed_j = _normalize_closed_interval(lo, hi, period)
        current = _intersect(current, failed_j)
        if not current:
            break
    return current


def interval_cardinality(intervals) -> int:
    return sum(hi - lo + 1 for lo, hi in intervals)


def brute_failure_phases(period: int, span: int, attempts: int):
    if period <= 0 or span <= 0 or attempts <= 0:
        raise ValueError('positive inputs required')
    failed = []
    for phase in range(period):
        all_fail = True
        for j in range(attempts):
            start = (phase + j * span) % period
            if span < period and start + span < period:
                all_fail = False
                break
        if all_fail:
            failed.append(phase)
    return failed
