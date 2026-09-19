"""Epoch-scoped lifecycle latch plus stale-evidence admission guard.

Silence never means terminal: stale evidence can refuse NEW authority only. Active
input is left to the existing owner deadline unless a trusted terminal receipt
actually arrives. This module grants no authority and chooses no action.
"""
from __future__ import annotations
import time

class LifecycleGate:
    def __init__(self, epoch: str, freshness_ns: int | None = None):
        if type(epoch) is not str or not epoch:
            raise ValueError('nonempty epoch required')
        if freshness_ns is not None and (type(freshness_ns) is not int or freshness_ns <= 0):
            raise ValueError('positive integer freshness_ns required')
        self.epoch=epoch; self.freshness_ns=freshness_ns
        self.sequence=-1; self.observed_ns=-1; self.ended=False; self.first_end_ns=None
        self._last_flag=None

    def observe(self, *, epoch: str, sequence: int, ended: bool, observed_ns: int) -> bool:
        if type(epoch) is not str or not epoch: raise ValueError('nonempty epoch required')
        if type(ended) is not bool: raise TypeError('exact boolean terminal flag required')
        if any(type(x) is not int or x < 0 for x in (sequence, observed_ns)):
            raise ValueError('nonnegative integer sequence/clock required')
        if epoch != self.epoch or sequence < self.sequence:
            return False
        if sequence == self.sequence:
            if ended != self._last_flag or observed_ns != self.observed_ns:
                raise ValueError('conflicting lifecycle duplicate')
            return False
        if observed_ns < self.observed_ns:
            raise ValueError('lifecycle clock regression')
        if self.ended and not ended:
            raise ValueError('terminal epoch cannot return to running')
        first=ended and not self.ended
        self.sequence=sequence; self.observed_ns=observed_ns; self._last_flag=ended
        if first:
            self.ended=True; self.first_end_ns=observed_ns
        return first

    def require_open(self, epoch: str, *, now_ns: int | None = None) -> None:
        if epoch != self.epoch:
            raise ValueError('provider epoch mismatch')
        if self.ended:
            raise ValueError('provider epoch ended; new session required')
        if self.freshness_ns is None:
            return
        if self.sequence < 0:
            raise ValueError('provider lifecycle evidence unavailable')
        now=time.perf_counter_ns() if now_ns is None else now_ns
        if type(now) is not int or now < 0:
            raise ValueError('nonnegative integer now_ns required')
        if now < self.observed_ns:
            raise ValueError('lifecycle admission clock regression')
        age=now-self.observed_ns
        if age > self.freshness_ns:
            raise ValueError(f'provider lifecycle evidence stale: age_ns={age} limit_ns={self.freshness_ns}')


def observe_and_cancel(executor, gate, *, epoch, sequence, ended, observed_ns,
                       delivered_ns=None, clock_ns=time.perf_counter_ns):
    """Latch trusted receipt, then revoke only the matching active intent."""
    with executor.lock:
        first=gate.observe(epoch=epoch,sequence=sequence,ended=ended,observed_ns=observed_ns)
        if not first or executor.active is None:
            return {'lifecycle_first_terminal': bool(first), 'lifecycle_delivered_ns': delivered_ns}
        identifier,lease,_=executor.active
        record={'lifecycle_first_terminal': True,'revoked_intent':lease.intent_token,
                'cancel_called_ns':clock_ns(),'lifecycle_delivered_ns':delivered_ns}
        record['cancel_matched']=executor.cancel(identifier)
        return record
