"""Trusted provider-lifecycle latch. No task score, action choice or grant.

Caller must serialize observe and submit with the SAME Executor RLock. Epochs
are local immutable session identities; a new epoch needs a new gate object.
This class does not authenticate an untrusted provider or infer visual meaning.
"""
from __future__ import annotations
import time

class TerminalGate:
    def __init__(self, epoch: str):
        if type(epoch) is not str or not epoch: raise ValueError('nonempty epoch required')
        self.epoch, self.sequence, self.observed_ns = epoch, -1, -1
        self.ended, self.first_end_ns = False, None
        self._last_flag = None

    def observe(self, *, epoch: str, sequence: int, ended: bool, observed_ns: int) -> bool:
        if type(epoch) is not str or not epoch: raise ValueError('nonempty epoch required')
        if type(ended) is not bool: raise TypeError('exact boolean terminal flag required')
        if any(type(x) is not int or x<0 for x in (sequence, observed_ns)):
            raise ValueError('nonnegative integer sequence/clock required')
        if epoch != self.epoch or sequence < self.sequence: return False
        if sequence == self.sequence:
            if ended != self._last_flag or observed_ns != self.observed_ns:
                raise ValueError('conflicting lifecycle duplicate')
            return False
        if observed_ns < self.observed_ns: raise ValueError('lifecycle clock regression')
        if self.ended and not ended: raise ValueError('terminal epoch cannot return to running')
        first = ended and not self.ended
        self.sequence, self.observed_ns, self._last_flag = sequence, observed_ns, ended
        if first: self.ended, self.first_end_ns = True, observed_ns
        return first

    def require_open(self, epoch: str) -> None:
        if epoch != self.epoch: raise ValueError('provider epoch mismatch')
        if self.ended: raise ValueError('provider epoch ended; new session required')


def observe_and_cancel(executor, gate, *, epoch, sequence, ended, observed_ns,
                       clock_ns=time.perf_counter_ns):
    """Latch before revoke, scoped to the active intent under its existing lock."""
    with executor.lock:
        first=gate.observe(epoch=epoch,sequence=sequence,ended=ended,observed_ns=observed_ns)
        if not first or executor.active is None: return {}
        identifier,lease,_=executor.active
        record={'revoked_intent':lease.intent_token,'cancel_called_ns':clock_ns()}
        record['cancel_matched']=executor.cancel(identifier)
        return record
