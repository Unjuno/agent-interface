"""Process-scoped monotonic timing records with explicit missing endpoints."""
import copy
import json
import os
import time
import uuid
from pathlib import Path


STATES = {'OBSERVED', 'MISSING', 'NOT_RECORDED'}


def process_clock():
    info = time.get_clock_info('perf_counter')
    return {
        'kind': 'python_perf_counter_ns',
        'domain_id': uuid.uuid4().hex,
        'scope': 'one_recorder_process',
        'pid': os.getpid(),
        'implementation': info.implementation,
        'resolution_ns': max(1, int(info.resolution * 1e9)),
        'monotonic': info.monotonic,
        'adjustable': info.adjustable,
    }


def validate(record):
    required = {'sequence', 'event', 'state', 'timestamp_ns', 'clock',
                'uncertainty_ns', 'cause', 'details'}
    if type(record) is not dict or set(record) != required:
        raise ValueError('exact timing event required')
    if type(record['sequence']) is not int or record['sequence'] < 1:
        raise ValueError('positive sequence required')
    if type(record['event']) is not str or not record['event']:
        raise ValueError('event name required')
    if record['state'] not in STATES:
        raise ValueError('explicit timing state required')
    if record['state'] == 'OBSERVED':
        if type(record['timestamp_ns']) is not int or record['timestamp_ns'] < 0:
            raise ValueError('observed timestamp required')
        clock = record['clock']
        if type(clock) is not dict or not clock.get('domain_id'):
            raise ValueError('observed clock domain required')
        if type(record['uncertainty_ns']) is not int or record['uncertainty_ns'] < 0:
            raise ValueError('nonnegative uncertainty required')
    elif (record['timestamp_ns'] is not None or record['clock'] is not None or
          record['uncertainty_ns'] is not None):
        raise ValueError('missing endpoints cannot carry inferred timing')
    if record['cause'] is not None and type(record['cause']) is not str:
        raise ValueError('cause must be string or null')
    if type(record['details']) is not dict:
        raise ValueError('details object required')
    return copy.deepcopy(record)


def interval(start, end):
    start, end = validate(start), validate(end)
    if start['state'] != 'OBSERVED' or end['state'] != 'OBSERVED':
        return {'status': 'missing_endpoint', 'duration_ns': None,
                'uncertainty_ns': None}
    if start['clock']['domain_id'] != end['clock']['domain_id']:
        return {'status': 'different_clock_domain', 'duration_ns': None,
                'uncertainty_ns': None}
    if end['timestamp_ns'] < start['timestamp_ns']:
        return {'status': 'ordering_error', 'duration_ns': None,
                'uncertainty_ns': None}
    return {'status': 'comparable',
            'duration_ns': end['timestamp_ns'] - start['timestamp_ns'],
            'uncertainty_ns': start['uncertainty_ns'] + end['uncertainty_ns']}


class Recorder:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise ValueError('timing record already exists')
        self.clock = process_clock()
        self.sequence = 0

    def record(self, event, *, timestamp_ns=None, uncertainty_ns=0,
               cause=None, details=None, state='OBSERVED'):
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
        with self.path.open('a', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(row, sort_keys=True) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        return row
