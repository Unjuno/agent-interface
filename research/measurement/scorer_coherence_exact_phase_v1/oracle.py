from __future__ import annotations


def closed_form_failure_count(period: int, span: int, attempts: int) -> int:
    """Independent equal-span immediate-retry count, without interval construction."""
    if period <= 0:
        raise ValueError('period must be positive')
    if span <= 0:
        raise ValueError('span must be positive')
    if attempts <= 0:
        raise ValueError('attempts must be positive')
    excess = attempts * span - (attempts - 1) * period
    if excess <= 0:
        return 0
    return period if excess >= period else excess


def guaranteed_boundary(period: int, attempts: int) -> int:
    if period <= 0 or attempts <= 0:
        raise ValueError('positive inputs required')
    return ((attempts - 1) * period) // attempts
