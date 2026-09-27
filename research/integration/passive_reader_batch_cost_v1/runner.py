"""Issue 3988: one-shot local backlog benchmark, never starts a GUI or model."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from types import SimpleNamespace
import reader

ROOT = Path(__file__).resolve().parent
SIZES = (128, 512, 2048)
BATCHES = (1, 32, 128)
ALLOCATION = 'reader-batch-cost-3988-20260922-01'


def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def corpus(n):
    lines = []
    for i in range(1, n + 1):
        row = dict(delivery_id=f'delivery:{i}', event='progress',
                   value=f'item-{i:06d}', padding='')
        row['padding'] = chr(97 + i % 26) * (255 - len(encode(row)))
        line = encode(row) + b'\n'
        assert len(line) == 256
        lines.append(line)
    return b''.join(lines)


def put(root, data):
    name = digest(data)
    p = root / 'objects' / name
    if p.exists():
        assert p.read_bytes() == data
    else:
        with p.open('xb') as f:
            f.write(data)
    return name


def check_freeze():
    freeze = json.loads((ROOT / 'FREEZE.json').read_bytes())
    for name, sha in freeze['sha256'].items():
        if digest((ROOT / name).read_bytes()) != sha:
            raise ValueError('SOURCE_OR_INPUT_CHANGED:' + name)
    return digest((ROOT / 'FREEZE.json').read_bytes())


def drain(path, n, batch):
    cursor = None
    records, trace = [], []
    cpu0 = time.process_time_ns()
    wall0 = time.perf_counter_ns()
    first = None
    while True:
        response = reader.read_pending(path, stream_id=f'backlog-3988-{n}',
                                       cursor=cursor, max_records=batch)
        if first is None:
            first = time.perf_counter_ns()
        cursor = response['next_cursor']
        records.extend(response['records'])
        trace.append([len(response['records']), cursor['offset'],
                      cursor['next_sequence'], response['tail_state'],
                      response['problem'], response['authority'],
                      response['acknowledged'], response['input_dispatched']])
        if response['tail_state'] != 'limit':
            break
        if len(trace) > n + 1:
            raise RuntimeError('BOUNDED_DRAIN_EXCEEDED')
    wall1 = time.perf_counter_ns()
    cpu1 = time.process_time_ns()
    return {'clocks': [cpu0, cpu1, wall0, first, wall1],
            'cursor': cursor, 'records': records, 'trace': trace}


class CountFile:
    def __init__(self, file, counts):
        self.file, self.counts = file, counts
    def __enter__(self):
        self.file.__enter__()
        return self
    def __exit__(self, *args):
        return self.file.__exit__(*args)
    def read(self, size):
        data = self.file.read(size)
        self.counts['reads'] += 1
        self.counts['requested_bytes'] += size
        self.counts['read_bytes'] += len(data)
        return data


def child(n, batch, rep, inputs, out, formal):
    freeze_sha = check_freeze() if formal else None
    os.sched_setaffinity(0, {0})
    path = inputs / f'{n}.jsonl'
    original = path.read_bytes()  # warm cache; outside timing
    timed = drain(path, n, batch)
    # Observe real calls in a separate, explicitly untimed accounting pass.
    counts = dict(opens=0, reads=0, requested_bytes=0, read_bytes=0,
                  hash_calls=0, hash_bytes=0)
    real_path, real_hashlib = reader.Path, reader.hashlib
    class CountPath:
        def __init__(self, p):
            self.path = real_path(p)
        def open(self, mode):
            assert mode == 'rb'
            counts['opens'] += 1
            return CountFile(self.path.open(mode), counts)
    def counted_sha(data=b''):
        counts['hash_calls'] += 1
        counts['hash_bytes'] += len(data)
        return real_hashlib.sha256(data)
    try:
        reader.Path = CountPath
        reader.hashlib = SimpleNamespace(sha256=counted_sha)
        accounting = drain(path, n, batch)
    finally:
        reader.Path, reader.hashlib = real_path, real_hashlib
    empty = reader.read_pending(path, stream_id=f'backlog-3988-{n}',
                                cursor=timed['cursor'], max_records=batch)
    result = dict(n=n, batch=batch, rep=rep, pid=os.getpid(),
                  affinity=sorted(os.sched_getaffinity(0)),
                  freeze_sha256=freeze_sha, input_sha256=digest(original),
                  source_unchanged=path.read_bytes() == original,
                  counts=counts, empty=empty, passes={})
    for label, record in (('timed', timed), ('accounting', accounting)):
        data = b''.join(encode(row) + b'\n' for row in record['records'])
        result['passes'][label] = dict(
            data=put(out, data), trace=put(out, encode(record['trace']) + b'\n'),
            clocks=record['clocks'], cursor=record['cursor'])
    if formal:
        assert check_freeze() == freeze_sha
    print(encode(result).decode(), flush=True)


def prepare():
    inputs = ROOT / 'inputs'
    inputs.mkdir(exist_ok=False)
    for n in SIZES:
        p = inputs / f'{n}.jsonl'
        p.write_bytes(corpus(n))
        p.chmod(0o444)
    import _hashlib
    env = {'python': sys.version, 'executable': sys.executable,
           'executable_sha256': digest(Path(sys.executable).read_bytes()),
           'platform': platform.platform(), 'cpu_count': os.cpu_count(),
           'available_affinity': sorted(os.sched_getaffinity(0)),
           'timed_child_affinity': [0], 'clock_frequency_locked': False,
           'docker_cli': None, 'container_image_identity': None,
           'cpu_snapshot': [s for s in Path('/proc/cpuinfo').read_text().splitlines()
                            if s.startswith(('model name', 'cpu MHz'))],
           'clocks': {s: vars(time.get_clock_info(s))
                      for s in ('process_time', 'perf_counter')},
           'hashlib_binary': _hashlib.__file__,
           'hashlib_binary_sha256': digest(Path(_hashlib.__file__).read_bytes()),
           'cgroup': {s: (Path('/sys/fs/cgroup') / s).read_text()
                      for s in ('cpu.max', 'memory.max', 'cpuset.cpus.effective')
                      if (Path('/sys/fs/cgroup') / s).exists()}}
    (ROOT / 'ENVIRONMENT.json').write_bytes(encode(env) + b'\n')


def schedule(formal):
    if not formal:
        return [(16, 1, 0), (16, 8, 0), (64, 1, 0), (64, 32, 0)]
    rows = []
    for n in SIZES:
        for rep in range(3):
            for batch in BATCHES[rep:] + BATCHES[:rep]:
                rows.append((n, batch, rep))
    return rows


def run(out, formal):
    freeze_sha = check_freeze() if formal else None
    out.mkdir(exist_ok=False)
    (out / 'objects').mkdir()
    (out / 'cases').mkdir()
    inputs = ROOT / 'inputs'
    if not formal:
        inputs = out / 'inputs'
        inputs.mkdir()
        for n in (16, 64):
            (inputs / f'{n}.jsonl').write_bytes(corpus(n))
    result = {'allocation': ALLOCATION if formal else 'construction-01',
              'formal': formal, 'freeze_sha256': freeze_sha, 'cases': [],
              'status': 'RUNNING', 'start_wall_ns': time.perf_counter_ns()}
    try:
        for index, (n, batch, rep) in enumerate(schedule(formal)):
            argv = [sys.executable, '-S', '-B', str(ROOT / 'runner.py'),
                    'child', str(n), str(batch), str(rep), str(inputs),
                    str(out), str(int(formal))]
            cp = subprocess.run(argv, capture_output=True, timeout=10,
                                env={**os.environ, 'PYTHONHASHSEED': '0'})
            stem = f'cases/{index:02d}'
            (out / (stem + '.stdout')).write_bytes(cp.stdout)
            (out / (stem + '.stderr')).write_bytes(cp.stderr)
            result['cases'].append({'index': index, 'n': n, 'batch': batch,
                                    'rep': rep, 'returncode': cp.returncode,
                                    'argv': argv, 'stdout': stem + '.stdout',
                                    'stdout_sha256': digest(cp.stdout),
                                    'stderr': stem + '.stderr',
                                    'stderr_sha256': digest(cp.stderr)})
            with (out / 'journal.jsonl').open('ab') as journal:
                journal.write(encode(result['cases'][-1]) + b'\n')
            if cp.returncode != 0:
                raise RuntimeError('CHILD_NONZERO')
        if formal:
            assert check_freeze() == freeze_sha
        result['status'] = 'COMPLETE'
    except Exception as exc:
        result['status'] = 'STOP'
        result['error'] = type(exc).__name__ + ':' + str(exc)
        if isinstance(exc, subprocess.TimeoutExpired):
            (out / 'timeout.stdout').write_bytes(exc.stdout or b'')
            (out / 'timeout.stderr').write_bytes(exc.stderr or b'')
    result['end_wall_ns'] = time.perf_counter_ns()
    (out / 'RAW.json').write_bytes(encode(result) + b'\n')
    print(encode({'status': result['status'], 'cases': len(result['cases']),
                  'raw_sha256': digest((out / 'RAW.json').read_bytes())}).decode())
    return 0 if result['status'] == 'COMPLETE' else 2


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'prepare':
        prepare()
    elif mode == 'child':
        child(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]),
              Path(sys.argv[5]), Path(sys.argv[6]), bool(int(sys.argv[7])))
    elif mode in ('construction', 'formal'):
        raise SystemExit(run(Path(sys.argv[2]).resolve(), mode == 'formal'))
    else:
        raise SystemExit('Unknown mode')
