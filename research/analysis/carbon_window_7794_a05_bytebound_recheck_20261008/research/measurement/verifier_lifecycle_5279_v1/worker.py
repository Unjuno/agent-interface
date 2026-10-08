"""One private stdio worker; no GUI, task actions, network or model weights."""
import time
ENTRY = time.monotonic_ns()
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
IMPORT_BEGIN = time.monotonic_ns()
from monitor import Monitor
IMPORT_END = time.monotonic_ns()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def memory():
    rows = Path('/proc/self/status').read_text().splitlines()
    rss = int(next(x for x in rows if x.startswith('VmRSS:')).split()[1])
    return {'rss_kib': rss, 'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def emit(obj):
    sys.stdout.write(canonical(obj) + '\n')
    sys.stdout.flush()


def main():
    mode = sys.argv[1]
    if mode not in {'COLD_PROCESS', 'WARM_CHECKOUT', 'RESIDENT_RESET', 'RESIDENT_BATCH', 'LEAKY'}:
        raise ValueError('mode')
    active = mode != 'WARM_CHECKOUT'
    shared = None
    count = 0
    boot = {'kind': 'ready', 'pid': os.getpid(), 'entry_ns': ENTRY,
            'import_begin_ns': IMPORT_BEGIN, 'import_end_ns': IMPORT_END,
            'monitor_sha256': hashlib.sha256(Path(__file__).with_name('monitor.py').read_bytes()).hexdigest(),
            'affinity': sorted(os.sched_getaffinity(0)), 'memory': memory()}
    boot['ready_ns'] = time.monotonic_ns()
    emit(boot)
    for line in sys.stdin:
        request = json.loads(line)
        op = request['op']
        if op == 'stop':
            emit({'kind': 'bye', 'pid': os.getpid(), 'count': count,
                  'cpu_ns': time.process_time_ns(), 'memory': memory(), 'at_ns': time.monotonic_ns()})
            return
        if op in ('activate', 'deactivate'):
            if mode != 'WARM_CHECKOUT':
                raise ValueError('activation mode')
            desired = op == 'activate'
            if desired == active:
                raise ValueError('activation state')
            active = desired
            emit({'kind': op, 'active': active, 'pid': os.getpid(), 'at_ns': time.monotonic_ns()})
            continue
        if not active or op not in ('run', 'batch'):
            raise ValueError('inactive or unknown operation')
        jobs = request['jobs'] if op == 'batch' else [request['job']]
        output = []
        for job in jobs:
            count += 1
            before = time.monotonic_ns()
            cpu = time.process_time_ns()
            verifier = shared if mode == 'LEAKY' and shared is not None else Monitor('AB', job['allowance'])
            initial = verifier.status
            states = [verifier.feed(t, labels) for t, labels in job['events']]
            if mode == 'LEAKY':
                shared = verifier
            elapsed_cpu = time.process_time_ns() - cpu
            after = time.monotonic_ns()
            output.append({'job_id': job['id'], 'input_sha256': hashlib.sha256(canonical(job).encode()).hexdigest(),
                           'initial': initial, 'states': states, 'serial': count,
                           'begin_ns': before, 'end_ns': after, 'compute_cpu_ns': elapsed_cpu,
                           'authority': False, 'task_success': None, 'pid': os.getpid()})
        emit({'kind': 'results', 'results': output, 'memory': memory(), 'pid': os.getpid()})
    raise ValueError('EOF without stop')


if __name__ == '__main__':
    main()
