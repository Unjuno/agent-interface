"""Buffered process-scoped timing records; one explicit close-time durability sync."""
import copy
import json
import os
import time
from pathlib import Path

from timing_envelope_v1 import process_clock, validate


class Recorder:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise ValueError('timing record already exists')
        self.clock = process_clock()
        self.sequence = 0
        self.handle = self.path.open('x', encoding='utf-8', newline='\n',
                                     buffering=65536)
        self.closed = False

    def record(self, event, *, timestamp_ns=None, uncertainty_ns=0,
               cause=None, details=None, state='OBSERVED'):
        if self.closed:
            raise ValueError('timing recorder closed')
        self.sequence += 1
        if state == 'OBSERVED':
            timestamp_ns = time.perf_counter_ns() if timestamp_ns is None else timestamp_ns
            clock = self.clock
        else:
            timestamp_ns = None
            clock = None
            uncertainty_ns = None
        row = validate({
            'sequence': self.sequence, 'event': event, 'state': state,
            'timestamp_ns': timestamp_ns, 'clock': copy.deepcopy(clock),
            'uncertainty_ns': uncertainty_ns, 'cause': cause,
            'details': {} if details is None else details,
        })
        self.handle.write(json.dumps(row, sort_keys=True) + '\n')
        return row

    def close(self):
        if self.closed:
            return
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
