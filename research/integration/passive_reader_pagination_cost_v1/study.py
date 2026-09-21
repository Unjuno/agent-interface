"""Issue 3985: exact reader, fixed-byte streams, separate timing/accounting passes."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import types

ROOT = Path(__file__).resolve().parent
PINS = {'reader.py': 'ea72c166c2cea511ea91031dfbb14563fe4e3245',
        'delivery_ledger_v2.py': 'fb50be9d4d821a7836e6a0158c53a983f0f91df5'}


def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name):
    path = ROOT / 'upstream' / name
    data = path.read_bytes()
    git_id = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if git_id != PINS[name]:
        raise ValueError('UPSTREAM_SOURCE_MISMATCH:' + name)
    spec = importlib.util.spec_from_file_location('frozen_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stream_bytes(n):
    ledger = load('delivery_ledger_v2.py').DeliveryLedger()
    rows = []
    for i in range(1, n + 1):
        record = ledger.prepare({'event': 'observation', 'index': i, 'pad': ''})
        record['pad'] = 'x' * (255 - len(encode(record)))
        line = encode(record) + b'\n'
        if len(line) != 256:
            raise ValueError('RECORD_WIDTH')
        rows.append(line)
    return b''.join(rows)


class Counters:
    """Delegate actual reads and SHA-256; only count arguments and returned bytes."""
    def __init__(self):
        self.reads = []
        self.hash_lengths = []

    def digest(self, data=b''):
        self.hash_lengths.append(len(data))
        return hashlib.sha256(data)

    def path(self, name):
        counter = self
        path = Path(name)
        class OpenPath:
            def open(self, mode):
                source = path.open(mode)
                class Stream:
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        source.close()
                    def read(self, requested):
                        data = source.read(requested)
                        counter.reads.append([requested, len(data)])
                        return data
                return Stream()
        return OpenPath()


def drain(reader, path, n, page, count=False):
    counter = Counters()
    if count:
        reader.Path = counter.path
        reader.hashlib = types.SimpleNamespace(sha256=counter.digest)
    calls = []
    cursor = None
    start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    for k in range(n // page + 1):
        old = cursor
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        response = reader.read_pending(path, stream_id='issue3985-fixed-lifetime',
                                       cursor=cursor, max_records=page, max_bytes=1048576)
        c1, t1 = time.process_time_ns(), time.perf_counter_ns()
        cursor = response['next_cursor']
        calls.append({'request_cursor': old, 'response': response,
                      'wall_start_ns': t0, 'wall_end_ns': t1,
                      'cpu_start_ns': c0, 'cpu_end_ns': c1})
    cpu_end, end = time.process_time_ns(), time.perf_counter_ns()
    return {'calls': calls, 'wall_start_ns': start, 'wall_end_ns': end,
            'cpu_start_ns': cpu_start, 'cpu_end_ns': cpu_end,
            'read_calls': counter.reads, 'hash_lengths': counter.hash_lengths}


def worker(out, n, page, rep):
    out.mkdir(parents=True, exist_ok=False)
    reader = load('reader.py')
    setup_start = time.perf_counter_ns()
    data = stream_bytes(n)
    path = out / 'stream.jsonl'
    path.write_bytes(data)
    if path.read_bytes() != data:
        raise ValueError('STREAM_WRITE_OR_PRIME_MISMATCH')
    setup_end = time.perf_counter_ns()
    plain = drain(reader, path, n, page)
    measured = drain(reader, path, n, page, True)
    result = {'schema': 'pagination-cost-3985-v1', 'pid': os.getpid(), 'n': n,
              'page': page, 'rep': rep, 'line_bytes': 256, 'max_bytes': 1048576,
              'source_blobs': PINS, 'stream_sha256': sha(data),
              'stream_after_sha256': sha(path.read_bytes()),
              'setup_start_ns': setup_start, 'setup_end_ns': setup_end,
              'plain': plain, 'measured': measured}
    raw = encode(result) + b'\n'
    (out / 'RAW.json').write_bytes(raw)
    print(json.dumps({'pid': os.getpid(), 'raw_sha256': sha(raw), 'status': 'completed'}), flush=True)


def capacity(out):
    out.mkdir(parents=True, exist_ok=False)
    reader = load('reader.py')
    data = stream_bytes(4)
    rows = []
    for page in (1, 8, 32):
        for mode in ('exact_cap', 'overflow_initial', 'overflow_suffix'):
            path = out / f'{page}-{mode}.jsonl'
            path.write_bytes(data)
            initial = None
            cursor = None
            if mode == 'overflow_suffix':
                initial = reader.read_pending(path, stream_id='issue3985-fixed-lifetime',
                                              max_records=2, max_bytes=1024)
                cursor = initial['next_cursor']
            if mode != 'exact_cap':
                with path.open('ab') as sink:
                    sink.write(b' ')
            before = path.read_bytes()
            cursor_before = encode(cursor).decode()
            try:
                response = reader.read_pending(path, stream_id='issue3985-fixed-lifetime',
                                               cursor=cursor, max_records=page, max_bytes=1024)
                error = None
            except ValueError as exc:
                response, error = None, str(exc)
            rows.append({'page': page, 'mode': mode, 'initial': initial,
                         'cursor_before_json': cursor_before, 'cursor_after_json': encode(cursor).decode(),
                         'source': path.name, 'before_sha256': sha(before),
                         'after_sha256': sha(path.read_bytes()), 'bytes': len(before),
                         'response': response, 'error': error})
    raw = encode({'schema': 'pagination-capacity-3985-v1', 'pid': os.getpid(), 'rows': rows}) + b'\n'
    (out / 'RAW.json').write_bytes(raw)
    print(json.dumps({'pid': os.getpid(), 'raw_sha256': sha(raw), 'status': 'completed'}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('out', type=Path)
    p.add_argument('--n', type=int, default=64)
    p.add_argument('--page', type=int, default=4)
    p.add_argument('--rep', type=int, default=-1)
    p.add_argument('--capacity', action='store_true')
    a = p.parse_args()
    if a.capacity:
        capacity(a.out)
    else:
        if a.n < 1 or a.page < 1 or a.n % a.page:
            raise SystemExit('invalid count/page')
        worker(a.out, a.n, a.page, a.rep)
