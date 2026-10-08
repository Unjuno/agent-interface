"""Epoch-scoped lifecycle admission with separate delivery and source freshness.

Fresh delivery timestamps do not prove fresh underlying state.  Stalled source
progress may refuse NEW authority only.  Silence/stall never cancels active input;
the existing owner deadline remains the backstop unless a trusted terminal receipt
actually arrives.
"""
from __future__ import annotations
import time

class LifecycleGate:
    def __init__(self, epoch: str, delivery_freshness_ns: int | None = None,
                 source_progress_freshness_ns: int | None = None):
        if type(epoch) is not str or not epoch: raise ValueError('nonempty epoch required')
        for name,value in [('delivery_freshness_ns',delivery_freshness_ns),('source_progress_freshness_ns',source_progress_freshness_ns)]:
            if value is not None and (type(value) is not int or value <= 0):
                raise ValueError('positive integer '+name+' required')
        self.epoch=epoch; self.delivery_freshness_ns=delivery_freshness_ns
        self.source_progress_freshness_ns=source_progress_freshness_ns
        self.sequence=-1; self.observed_ns=-1; self.ended=False; self.first_end_ns=None
        self.source_generation=-1; self.source_advanced_ns=-1; self._last_flag=None

    def observe(self, *, epoch: str, sequence: int, ended: bool, observed_ns: int,
                source_generation: int) -> bool:
        if type(epoch) is not str or not epoch: raise ValueError('nonempty epoch required')
        if type(ended) is not bool: raise TypeError('exact boolean terminal flag required')
        if any(type(x) is not int or x < 0 for x in (sequence,observed_ns,source_generation)):
            raise ValueError('nonnegative integer sequence/clock/source generation required')
        if epoch != self.epoch or sequence < self.sequence:return False
        if sequence == self.sequence:
            if (ended != self._last_flag or observed_ns != self.observed_ns or
                source_generation != self.source_generation):
                raise ValueError('conflicting lifecycle duplicate')
            return False
        if observed_ns < self.observed_ns: raise ValueError('lifecycle clock regression')
        if self.ended and not ended: raise ValueError('terminal epoch cannot return to running')
        if source_generation < self.source_generation: raise ValueError('source generation regression')
        if source_generation > self.source_generation:
            self.source_generation=source_generation; self.source_advanced_ns=observed_ns
        first=ended and not self.ended
        self.sequence=sequence; self.observed_ns=observed_ns; self._last_flag=ended
        if first:self.ended=True;self.first_end_ns=observed_ns
        return first

    def require_open(self, epoch: str, *, now_ns: int | None = None) -> None:
        if epoch != self.epoch: raise ValueError('provider epoch mismatch')
        if self.ended: raise ValueError('provider epoch ended; new session required')
        if self.sequence < 0: raise ValueError('provider lifecycle evidence unavailable')
        now=time.perf_counter_ns() if now_ns is None else now_ns
        if type(now) is not int or now < 0: raise ValueError('nonnegative integer now_ns required')
        if now < self.observed_ns: raise ValueError('lifecycle admission clock regression')
        if self.delivery_freshness_ns is not None:
            age=now-self.observed_ns
            if age > self.delivery_freshness_ns:
                raise ValueError(f'provider lifecycle delivery stale: age_ns={age} limit_ns={self.delivery_freshness_ns}')
        if self.source_progress_freshness_ns is not None:
            if self.source_advanced_ns < 0: raise ValueError('provider source generation unavailable')
            if now < self.source_advanced_ns: raise ValueError('source progress admission clock regression')
            age=now-self.source_advanced_ns
            if age > self.source_progress_freshness_ns:
                raise ValueError(f'provider source generation stale: age_ns={age} limit_ns={self.source_progress_freshness_ns}')

def observe_and_cancel(executor, gate, *, epoch, sequence, ended, observed_ns,
                       source_generation, delivered_ns=None, clock_ns=time.perf_counter_ns):
    with executor.lock:
        first=gate.observe(epoch=epoch,sequence=sequence,ended=ended,observed_ns=observed_ns,
                           source_generation=source_generation)
        if not first or executor.active is None:
            return {'lifecycle_first_terminal':bool(first),'lifecycle_delivered_ns':delivered_ns}
        identifier,lease,_=executor.active
        record={'lifecycle_first_terminal':True,'revoked_intent':lease.intent_token,
                'cancel_called_ns':clock_ns(),'lifecycle_delivered_ns':delivered_ns}
        record['cancel_matched']=executor.cancel(identifier)
        return record
