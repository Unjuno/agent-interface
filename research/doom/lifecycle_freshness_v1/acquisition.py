"""Acquire once, then validate the real measurement envelope before persistence.

All timestamps are nonnegative integer ns from one monotonic clock. This proves
acquisition ordering, NOT source freshness, atomicity, or the time of an effect.
"""
from __future__ import annotations
import time
from typing import Any, Callable


def payload_dict(payload: Any) -> dict:
    value = payload.as_dict() if hasattr(payload, 'as_dict') else payload
    if not isinstance(value, dict):
        raise TypeError('payload must expose a dictionary')
    return value


def validate_receipt(receipt: dict) -> None:
    if not isinstance(receipt, dict):
        raise TypeError('receipt must be a dictionary')
    payload = payload_dict(receipt['payload'])
    values = [receipt[k] for k in ('scheduled_ns', 'sample_started_ns', 'sample_finished_ns')]
    values.append(payload['sample_ns'])
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError('timestamps must be nonnegative integer ns')
    scheduled, started, finished, observed = values
    if not scheduled <= started <= observed <= finished:
        raise ValueError('payload outside real acquisition bracket or reversed clock')
    for key in ('start_lateness_ns', 'missed_periods_before'):
        if type(receipt[key]) is not int or receipt[key] < 0:
            raise ValueError('invalid scheduler accounting')
    if receipt['start_lateness_ns'] != started - scheduled:
        raise ValueError('inconsistent start lateness')
    if hasattr(receipt['payload'], 'validate'):
        receipt['payload'].validate()


def acquire(sample_fn: Callable[[], Any], clock_ns: Callable[[], int] = time.perf_counter_ns) -> dict:
    """Include all provider work in the bracket, without a duplicate sample."""
    started = clock_ns()
    payload = sample_fn()
    finished = clock_ns()
    receipt = dict(scheduled_ns=started, sample_started_ns=started,
                   sample_finished_ns=finished, start_lateness_ns=0,
                   missed_periods_before=0, payload=payload)
    validate_receipt(receipt)
    return receipt


class FinalAcquirer:
    """One local finalization attempt; failure never authorizes a silent retry."""
    def __init__(self, sample_fn, sink, clock_ns=time.perf_counter_ns):
        self.sample_fn, self.sink, self.clock_ns = sample_fn, sink, clock_ns
        self.attempted = False

    def __call__(self):
        if self.attempted:
            raise RuntimeError('final acquisition already attempted')
        self.attempted = True
        receipt = acquire(self.sample_fn, self.clock_ns)
        receipt['direct_final_sample'] = True
        self.sink(receipt)
        return receipt
