"""Cooperative wake on recorded interruption; cannot preempt capture or X calls."""
import threading
from lease import Expired
from lease_cause_v1 import Lease as Previous
from executor_v3 import Cancelled, DecisionRequired


class Lease(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wake = threading.Event()

    def record_interruption(self, record):
        super().record_interruption(record)
        if self.interruption_snapshot() is not None:
            self._wake.set()

    def check(self):
        cause = self.interruption_snapshot()
        if cause is not None:
            reason = cause['record']['reason']
            if reason == 'expired':
                raise Expired()
            if reason in ('cancelled', 'stop_requested'):
                raise Cancelled()
            raise DecisionRequired(reason)
        super().check()

    def set(self):
        super().set()
        self._wake.set()

    def wait(self, timeout):
        self.check()
        if self.cancel.is_set():
            return True
        self._wake.wait(min(timeout, max(0, (self.deadline - self.clock()) / 1e9)))
        self.check()
        return self.cancel.is_set()
