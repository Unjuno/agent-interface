"""One frozen 36-case orchestration. Reusing an existing output directory is refused."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import selectors
import sqlite3
import subprocess
import sys
import time
from upstream.delivery_ledger_v2 import DeliveryLedger

HERE = Path(__file__).resolve().parent
POLICIES = ['BLIND_REPLACE', 'OFFSET_MAX', 'REVISION_CAS']
SCHEDULES = ['OVERLAP_SMALL_FIRST', 'OVERLAP_LARGE_FIRST', 'EXACT_RESPONSE_REPLAY', 'SEQUENTIAL']


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        f.write(encoded(value) + '\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def observe(root):
    with sqlite3.connect(f'file:{root / "host.sqlite"}?mode=ro', uri=True) as db:
        rev, cur = db.execute('SELECT revision,cursor FROM state WHERE id=1').fetchone()
        batches = [{'index': i, 'worker': w, 'request_id': r, 'response': json.loads(p)}
                   for i, w, r, p in db.execute('SELECT id,worker,request_id,response FROM batches ORDER BY id')]
    return {'revision': rev, 'cursor': json.loads(cur), 'batches': batches}


def run_case(out, policy, schedule, repetition):
    case_id = f'{policy}__{schedule}__{repetition}'
    root = out / case_id
    root.mkdir()
    stream_id = f'fixed-owner-{case_id}'
    ledger = DeliveryLedger()
    records = [ledger.prepare({'event': 'notification_fixture', 'ordinal': i,
                               'payload': f'payload-{case_id}-{i}'}) for i in range(1, 7)]
    source = ''.join(encoded(r) + '\n' for r in records).encode()
    (root / 'stream.jsonl').write_bytes(source)
    (root / 'stream.jsonl').chmod(0o444)
    cursor = {'schema': 'agent-interface/experimental-read-cursor-v1', 'stream_id': stream_id,
              'offset': 0, 'prefix_sha256': sha(b''), 'next_sequence': 1}
    with sqlite3.connect(root / 'host.sqlite') as db:
        db.executescript('CREATE TABLE state(id INTEGER PRIMARY KEY,revision INTEGER,cursor TEXT);'
                        'CREATE TABLE batches(id INTEGER PRIMARY KEY AUTOINCREMENT,worker TEXT,'
                        'request_id TEXT,response TEXT);')
        db.execute('INSERT INTO state VALUES(1,0,?)', (encoded(cursor),))
    raw = {'case_id': case_id, 'policy': policy, 'schedule': schedule, 'repetition': repetition,
           'stream_id': stream_id, 'stream_hex': source.hex(), 'source_before_sha256': sha(source),
           'initial': observe(root), 'events': [], 'processes': []}
    workers = {}
    try:
        for name in ('A', 'B', 'C'):
            argv = [sys.executable, '-B', str(HERE / 'worker.py'), str(root), name, policy, stream_id]
            stderr = (root / f'{name}.stderr').open('wb')
            proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=stderr, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            workers[name] = (proc, stderr, argv)

        def command(name, op, **kwargs):
            proc = workers[name][0]
            req = {'op': op, **kwargs}
            before = observe(root)
            reqbytes = (encoded(req) + '\n').encode()
            proc.stdin.write(reqbytes)
            proc.stdin.flush()
            with selectors.DefaultSelector() as poll:
                poll.register(proc.stdout, selectors.EVENT_READ)
                if not poll.select(8):
                    raise TimeoutError(f'{name}:{op}')
            response_bytes = proc.stdout.readline(1_000_001)
            if not response_bytes.endswith(b'\n') or len(response_bytes) > 1_000_000:
                raise RuntimeError('INVALID_WORKER_FRAME')
            response = json.loads(response_bytes)
            event = {'worker': name, 'request_hex': reqbytes.hex(),
                     'response_hex': response_bytes.hex(), 'before': before, 'after': observe(root)}
            raw['events'].append(event)
            with (root / 'journal.jsonl').open('a') as journal:
                journal.write(encoded(event) + '\n')
            return response

        command('A', 'prepare', limit=2, request_id=f'{case_id}/A')
        if schedule == 'SEQUENTIAL':
            command('A', 'commit')
            command('B', 'prepare', limit=4, request_id=f'{case_id}/B')
            command('B', 'commit')
        elif schedule == 'EXACT_RESPONSE_REPLAY':
            command('A', 'commit')
            command('A', 'commit')
        else:
            command('B', 'prepare', limit=4, request_id=f'{case_id}/B')
            for name in (('A', 'B') if schedule == 'OVERLAP_SMALL_FIRST' else ('B', 'A')):
                command(name, 'commit')
        # One explicitly registered fresh continuation, never reuses a rejected prepared result.
        command('C', 'prepare', limit=32, request_id=f'{case_id}/C')
        command('C', 'commit')
        for name in workers:
            command(name, 'quit')
        raw['final'] = observe(root)
        raw['source_after_sha256'] = sha((root / 'stream.jsonl').read_bytes())
    finally:
        for name, (proc, stderr, argv) in workers.items():
            forced = False
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=4)
                forced = True
            stderr.close()
            raw['processes'].append({'worker': name, 'pid': proc.pid, 'argv': argv,
                                     'returncode': proc.returncode, 'forced_kill': forced,
                                     'stderr_hex': (root / f'{name}.stderr').read_bytes().hex()})
        raw['database_sha256'] = sha((root / 'host.sqlite').read_bytes())
        save(root / 'raw.json', raw)
    if any(p['returncode'] != 0 or p['forced_kill'] or p['stderr_hex'] for p in raw['processes']):
        raise RuntimeError('WORKER_EXIT_FAILURE')
    return {'case_id': case_id, 'raw_sha256': sha((root / 'raw.json').read_bytes())}


def main():
    mode, dest = sys.argv[1:]
    if mode not in ('construction', 'formal'):
        raise ValueError('INVALID_MODE')
    freeze = json.loads((HERE / 'FREEZE.json').read_text())
    for name, digest in freeze['sha256'].items():
        if sha((HERE / name).read_bytes()) != digest:
            raise RuntimeError(f'SOURCE_MISMATCH:{name}')
    out = Path(dest).resolve()
    out.mkdir(parents=True, exist_ok=False)
    meta = {'schema': 'concurrent-reader-run-v1', 'mode': mode, 'started_ns': time.monotonic_ns(),
            'freeze_sha256': sha((HERE / 'FREEZE.json').read_bytes()), 'cases': [], 'status': 'STARTED'}
    reps = range(1, 4) if mode == 'formal' else range(1, 2)
    try:
        for policy, schedule, rep in itertools.product(POLICIES, SCHEDULES, reps):
            meta['cases'].append(run_case(out, policy, schedule, rep))
        meta['status'] = 'COMPLETED'
    except BaseException as exc:
        meta['status'] = 'STOP'
        meta['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        meta['finished_ns'] = time.monotonic_ns()
        save(out / 'RUN.json', meta)
        print(encoded(meta))


if __name__ == '__main__':
    main()
