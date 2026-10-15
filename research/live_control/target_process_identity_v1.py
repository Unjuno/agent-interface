"""Opt-in read-only Linux/XRes process evidence, separate from input custody."""
from pathlib import Path
import sys
import time

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

    def close(self):
        return self.worker.close()

    def read(self, xid, *, perf_deadline_ns, cancelled=lambda: False):
        if type(xid) is not int or xid <= 0 or type(perf_deadline_ns) is not int:
            raise ValueError('explicit surface and original perf-counter deadline required')
        monotonic_origin = time.monotonic_ns()
        remaining = perf_deadline_ns - time.perf_counter_ns()
        if remaining <= 0:
            raise RuntimeError('identity source expired')
        value = self.worker.read('process_identity', xid,
            deadline_ns=monotonic_origin + remaining, cancelled=cancelled)
        if cancelled() or time.perf_counter_ns() >= perf_deadline_ns:
            self.close()
            raise RuntimeError('late identity reply')
        if (type(value) is not str or len(value) != 64 or
                any(c not in '0123456789abcdef' for c in value)):
            self.close()
            raise RuntimeError('identity proof unavailable')
        return value
