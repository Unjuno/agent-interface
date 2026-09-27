"""Observation-only age at a recorded validation-completion sample, not authority."""
from __future__ import annotations

def finalize(status: str, meta: dict | None, received_ns: int, sampled_ns: int,
             budget_ns: int = 20_000_000) -> str:
    """Preserve the earlier refusal; never restamp old capture time as current."""
    if any(type(x) is not int or x < 0 for x in (received_ns, sampled_ns, budget_ns)):
        return 'YIELD_INVALID'
    if sampled_ns < received_ns:
        return 'YIELD_INVALID'
    if status not in ('FRAME_FRESH', 'YIELD_STALE', 'YIELD_INVALID'):
        return 'YIELD_INVALID'
    if status != 'FRAME_FRESH':
        return status
    if type(meta) is not dict:
        return 'YIELD_INVALID'
    first, last = meta.get('capture_start_ns'), meta.get('capture_end_ns')
    if any(type(x) is not int or x < 0 for x in (first, last)):
        return 'YIELD_INVALID'
    if not first <= last <= received_ns:
        return 'YIELD_INVALID'
    return ('FRESH_AT_VALIDATION_SAMPLE' if sampled_ns-first <= budget_ns
            else 'YIELD_STALE_AT_VALIDATION')
