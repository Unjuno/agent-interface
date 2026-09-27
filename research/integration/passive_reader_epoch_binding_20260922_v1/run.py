"""One finite allocation; output directories are exclusive and never reused."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
SCENARIOS = ('APPEND', 'READER_RESTART', 'RESTART_IDENTICAL',
             'RESTART_SHARED_PREFIX', 'RESTART_CHANGED_PREFIX', 'RESTART_SHORT',
             'MIXED_EPOCH_SUFFIX', 'FRESH_EPOCH_ADOPTION')
PROTOCOLS = ('LEGACY_CALLER_ID', 'IN_BAND_EPOCH')
WORKER = ROOT / 'worker.py'


def encoded(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, obj):
    with path.open('x', encoding='utf-8') as file:
        file.write(encoded(obj))
        file.flush()
        os.fsync(file.fileno())


def check_freeze():
    freeze_bytes = (ROOT / 'FREEZE.json').read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, expected in freeze['files'].items():
        data = (ROOT / name).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if digest(data) != expected['sha256'] or blob != expected['git_blob']:
            raise RuntimeError('STOP_SOURCE_MISMATCH:' + name)
    return digest(freeze_bytes)


class Producer:
    def __init__(self, case, config):
        self.record = {'argv': [sys.executable, str(WORKER), 'produce'],
                       'config': config, 'rpc': []}
        case['producers'].append(self.record)
        self.process = subprocess.Popen(self.record['argv'], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.record['pid'] = self.process.pid
        self.exchange(config)

    def exchange(self, request):
        raw = encoded(request)
        exchange = {'request_utf8': raw}
        self.record['rpc'].append(exchange)
        self.process.stdin.write(raw.encode())
        self.process.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            if not selector.select(timeout=5):
                raise TimeoutError('producer response timeout')
        line = self.process.stdout.readline()
        exchange['stdout_utf8'] = line.decode()
        if not line.endswith(b'\n'):
            raise RuntimeError('producer incomplete response')
        return json.loads(line)

    def close(self):
        if self.process.poll() is None:
            self.exchange({'op': 'stop'})
            self.process.stdin.close()
        self.record['returncode'] = self.process.wait(timeout=5)
        self.record['trailing_stdout_utf8'] = self.process.stdout.read().decode()
        self.record['stderr_utf8'] = self.process.stderr.read().decode()
        if self.record['returncode'] != 0:
            raise RuntimeError('producer process failure')

    def cleanup(self):
        if self.process.poll() is None:
            self.process.kill()
        self.record.setdefault('cleanup_returncode', self.process.wait(timeout=5))


def read(case, path, epoch, cursor, limit):
    request = {'protocol': case['protocol'], 'path': str(path), 'stream_id': epoch,
               'cursor': cursor, 'max_records': limit}
    entry = {'argv': [sys.executable, str(WORKER), 'read'],
             'request_utf8': encoded(request)}
    case['reads'].append(entry)
    child = subprocess.Popen(entry['argv'], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    entry['pid'] = child.pid
    try:
        out, err = child.communicate(entry['request_utf8'].encode(), timeout=5)
    except BaseException:
        child.kill()
        out, err = child.communicate()
        entry.update(stdout_utf8=out.decode(), stderr_utf8=err.decode(), returncode=child.returncode)
        raise
    entry.update(stdout_utf8=out.decode(), stderr_utf8=err.decode(), returncode=child.returncode)
    if child.returncode != 0 or not out.endswith(b'\n'):
        raise RuntimeError('reader process failure')
    return json.loads(out)['result']


def one(case, directory):
    directory.mkdir(exist_ok=False)
    path = directory / 'delivered.jsonl'
    epoch_a, epoch_b = case['id'] + ':A', case['id'] + ':B'
    case.update(epochs=[epoch_a, epoch_b], producers=[], reads=[], snapshots={})
    producers = []
    def spawn(epoch):
        item = Producer(case, {'path': str(path), 'epoch': epoch, 'protocol': case['protocol']})
        producers.append(item)
        return item
    def snapshot(label):
        data = path.read_bytes()
        case['snapshots'][label] = {'utf8': data.decode(), 'sha256': digest(data)}
    try:
        a = spawn(epoch_a)
        scenario = case['scenario']
        count = 2 if scenario in ('APPEND', 'MIXED_EPOCH_SUFFIX') else 3
        a.exchange({'op': 'create', 'values': list(range(1, count + 1))})
        snapshot('initial')
        first = read(case, path, epoch_a, None, 2)
        if first['status'] != 'OK' or len(first['receipt']['records']) != 2:
            raise RuntimeError('initial reader failed')
        cursor = first['receipt']['next_cursor']
        if scenario == 'APPEND':
            a.exchange({'op': 'append', 'values': [3]})
        elif scenario != 'READER_RESTART':
            a.close()
            b = spawn(epoch_b)
            values = {'RESTART_IDENTICAL': [1, 2, 3],
                      'RESTART_SHARED_PREFIX': [1, 2, 303],
                      'RESTART_CHANGED_PREFIX': [101, 2, 3],
                      'RESTART_SHORT': [1], 'MIXED_EPOCH_SUFFIX': [1, 2, 3],
                      'FRESH_EPOCH_ADOPTION': [11, 12, 13]}[scenario]
            b.exchange({'op': 'append' if scenario == 'MIXED_EPOCH_SUFFIX' else 'replace',
                        'values': values, 'skip': 2 if scenario == 'MIXED_EPOCH_SUFFIX' else 0})
        snapshot('final')
        fresh = scenario == 'FRESH_EPOCH_ADOPTION'
        read(case, path, epoch_b if fresh else epoch_a, None if fresh else cursor, 32)
        for item in producers:
            if 'returncode' not in item.record:
                item.close()
        snapshot('after_read')
    finally:
        for item in producers:
            item.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', choices=['construction', 'formal'], required=True)
    args = parser.parse_args()
    # Exclusive allocation precedes all work; even a STOP consumes this path.
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.time_ns()
    record = {'schema': 'producer-epoch-experiment-v1', 'phase': args.phase,
              'allocation': args.output.name, 'started_unix_ns': started,
              'source_freeze_sha256': None, 'cases': [], 'status': 'RUNNING'}
    status = 1
    try:
        record['source_freeze_sha256'] = check_freeze() if args.phase == 'formal' else 'UNFROZEN_CONSTRUCTION'
        repetitions = 3 if args.phase == 'formal' else 1
        for rep in range(repetitions):
            for scenario in SCENARIOS:
                for protocol in PROTOCOLS:
                    case = {'id': f'{args.phase}-{rep}-{scenario}-{protocol}',
                            'rep': rep, 'protocol': protocol, 'scenario': scenario}
                    record['cases'].append(case)
                    try:
                        one(case, args.output / case['id'])
                    finally:
                        save(args.output / (case['id'] + '.json'), case)
        if args.phase == 'formal' and check_freeze() != record['source_freeze_sha256']:
            raise RuntimeError('STOP_FREEZE_CHANGED')
        record['status'] = 'COMPLETE'
        status = 0
    except BaseException:
        record['status'] = 'STOP_EXECUTION'
        record['traceback'] = traceback.format_exc()
    finally:
        record['ended_unix_ns'] = time.time_ns()
        save(args.output / 'RAW.json', record)
    print(json.dumps({'status': record['status'], 'cases': len(record['cases']),
                      'raw_sha256': digest((args.output / 'RAW.json').read_bytes())}))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
