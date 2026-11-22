"""Lease-bound wait for an independently recorded input-owner interruption."""
import copy
import threading

from lease_cause_v2 import Lease as Previous


class Lease(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interruption_ready = threading.Event()

    def record_interruption(self, record):
        super().record_interruption(record)
        if self.interruption_snapshot() is not None:
            self._interruption_ready.set()

    def wait_interruption(self, timeout_seconds):
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds < 0:
            raise ValueError("nonnegative interruption wait required")
        self._interruption_ready.wait(timeout_seconds)
        return copy.deepcopy(self.interruption_snapshot())
