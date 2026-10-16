"""Opt-in read-only Linux/XRes process evidence, separate from input custody."""
from pathlib import Path
import sys
import time
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.guarded_x11_v1.target_queries import TargetQueryWorker, X11TargetQueries


def valid_source(source):
    return (type(source) is tuple and len(source) == 4 and
            all(type(source[i]) is int and source[i] > 0 for i in (0, 1, 3)) and
            type(source[2]) is str and len(source[2]) == 64 and
            all(c in '0123456789abcdef' for c in source[2]))


class IdentityReader:
    def __init__(self, display_name):
        if type(display_name) is not str or not display_name:
            raise ValueError('explicit display required for process identity')
        self.worker = TargetQueryWorker(lambda: X11TargetQueries(display_name))
        self._window_gate = threading.Lock()

    def close(self):
        return self.worker.close()

    def _query(self, operation, xid, perf_deadline_ns, cancelled):
        if type(xid) is not int or xid <= 0 or type(perf_deadline_ns) is not int:
            raise ValueError('explicit surface and original perf-counter deadline required')
        monotonic_origin = time.monotonic_ns()
        remaining = perf_deadline_ns - time.perf_counter_ns()
        if remaining <= 0:
            raise RuntimeError('identity source expired')
        value = self.worker.read(operation, xid,
            deadline_ns=monotonic_origin + remaining, cancelled=cancelled)
        if cancelled() or time.perf_counter_ns() >= perf_deadline_ns:
            self.close()
            raise RuntimeError('late identity reply')
        return value

    def read_focus(self, xid, *, perf_deadline_ns, cancelled=lambda: False):
        value = self._query('focus_id', xid, perf_deadline_ns, cancelled)
        if type(value) is not int or value < 0:
            self.close()
            raise RuntimeError('focus proof unavailable')
        return value

    def read(self, xid, *, perf_deadline_ns, cancelled=lambda: False):
        value = self._query('process_identity', xid, perf_deadline_ns, cancelled)
        if (type(value) is not str or len(value) != 64 or
                any(c not in '0123456789abcdef' for c in value)):
            self.close()
            raise RuntimeError('identity proof unavailable')
        return value

    def read_window(self, xid, *, perf_deadline_ns, cancelled=lambda: False):
        if type(perf_deadline_ns) is not int:
            raise ValueError('original window-query deadline required')
        # Capture and pre-press checks share this observer epoch. Waiting for
        # its one request slot must never outlive the caller's own lease/cancel.
        while not self._window_gate.acquire(blocking=False):
            if cancelled() or time.perf_counter_ns() >= perf_deadline_ns:
                self.close()
                raise RuntimeError('window-query slot wait cancelled or expired')
            time.sleep(.001)
        try:
            value = self._query('window_incarnation', xid, perf_deadline_ns, cancelled)
        finally:
            self._window_gate.release()
        if (type(value) is not str or len(value) != 64 or
                any(c not in '0123456789abcdef' for c in value)):
            self.close()
            raise RuntimeError('window continuity proof unavailable')
        return value
