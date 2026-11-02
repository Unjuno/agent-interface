"""Opt-in read-only Linux/XRes process evidence, separate from input custody."""
from pathlib import Path
import json
import os
import sys
import time
import threading
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.guarded_x11_v1.target_queries import TargetQueryWorker, X11TargetQueries


def valid_source(source):
    return (type(source) is tuple and len(source) == 4 and
            all(type(source[i]) is int and source[i] > 0 for i in (0, 1, 3)) and
            type(source[2]) is str and len(source[2]) == 64 and
            all(c in '0123456789abcdef' for c in source[2]))


class IdentityReader:
    def __init__(self, display_name, *, purpose='unspecified'):
        if type(display_name) is not str or not display_name:
            raise ValueError('explicit display required for process identity')
        if purpose not in ('unspecified', 'capture', 'window', 'input_owner'):
            raise ValueError('unknown identity reader purpose')
        self.purpose = purpose
        self.reader_id = uuid.uuid4().hex
        self._fault_hook = _test_delay_hook(self.purpose, self.reader_id)
        self.worker = TargetQueryWorker(lambda: X11TargetQueries(display_name),
                                        before_read=self._fault_hook)
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


_test_fault_lock = threading.Lock()
_test_fault_fired = False


def _test_delay_hook(purpose, reader_id):
    """Explicit, one-shot research fault affecting input-owner queries only.

    The delay runs inside TargetQueryWorker, so its caller can hit the original
    deadline and retire/quarantine the reader while the game and input release
    connection remain available. Unset variables leave the normal path intact.
    """
    raw_delay = os.environ.get('AGENT_INTERFACE_TEST_IDENTITY_QUERY_DELAY_MS')
    if raw_delay is None or purpose != 'input_owner':
        return None
    try:
        delay_ms = int(raw_delay)
    except ValueError as error:
        raise ValueError('test identity query delay must be an integer') from error
    if not 1000 < delay_ms <= 10000:
        raise ValueError('test identity query delay must be in [1001, 10000] ms')
    raw_occurrence = os.environ.get('AGENT_INTERFACE_TEST_IDENTITY_QUERY_OCCURRENCE', '1')
    try:
        occurrence = int(raw_occurrence)
    except ValueError as error:
        raise ValueError('test identity query occurrence must be an integer') from error
    if not 1 <= occurrence <= 100:
        raise ValueError('test identity query occurrence must be in [1, 100]')
    raw_path = os.environ.get('AGENT_INTERFACE_TEST_IDENTITY_QUERY_FAULT_PATH')
    if not raw_path:
        raise ValueError('test identity query fault path is required with delay')
    path = Path(raw_path)
    lock = _test_fault_lock
    query_count = 0

    def before_read(operation, xid):
        global _test_fault_fired
        nonlocal query_count
        if operation != 'process_identity':
            return
        with lock:
            query_count += 1
            if query_count != occurrence:
                return
            if _test_fault_fired:
                return
            _test_fault_fired = True
        row = {'schema': 'target-identity-query-delay-fault-v1',
               'event': 'delay_started', 'purpose': purpose,
               'reader_id': reader_id, 'operation': operation, 'xid': xid,
               'occurrence': occurrence, 'delay_ms': delay_ms,
               'started_ns': time.perf_counter_ns()}
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n')
            stream.flush()
        time.sleep(delay_ms / 1000)
        row = dict(row, event='delay_finished', finished_ns=time.perf_counter_ns())
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n')

    return before_read
