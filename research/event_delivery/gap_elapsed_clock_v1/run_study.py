"""One-shot local clock study. Existing output directories are always refused."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import sqlite3
import subprocess
import sys
import time
import traceback
import contiguous_model as model

HERE = Path(__file__).resolve().parent

def dump(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')

def snapshot(path: Path) -> dict:
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as c:
        return {'consumer': [list(x) for x in c.execute('SELECT * FROM consumer ORDER BY seq')],
                'pending': [list(x) for x in c.execute('SELECT * FROM pending ORDER BY pos')],
                'ack': [list(x) for x in c.execute('SELECT * FROM ack')]}

def read_line(proc: subprocess.Popen, timeout: float = 3.0) -> str:
    with selectors.DefaultSelector() as selector:
        selector.register(proc.stdout, selectors.EVENT_READ)
        if not selector.select(timeout):
            raise TimeoutError('worker reply timeout')
    line = proc.stdout.readline(65537)
    if not line.endswith(b'\n') or len(line) > 65536:
        raise RuntimeError('incomplete or oversized JSON line')
    return line.decode('utf-8')

def check_freeze(freeze: Path) -> dict:
    data = json.loads(freeze.read_text())
    for filename, sha in data['sources'].items():
        if hashlib.sha256((HERE / filename).read_bytes()).hexdigest() != sha:
            raise RuntimeError('SOURCE_MISMATCH: ' + filename)
    return data

def run_case(spec: dict, folder: Path) -> dict:
    folder.mkdir()
    db = folder / 'state.sqlite3'
    model.init_db(db)
    with sqlite3.connect(db) as c:
        assert model.ack_through(c, 2, model.ack_digest(c, 2)) == 'ACK_APPLIED'
    procs = {}
    handles = {}
    metadata = dict(spec=spec, initial=snapshot(db), workers={}, exits={}, error=None)
    journal = (folder / 'journal.jsonl').open('x')
    counter = 0
    def rpc(role: str, command: dict, scheduled_ms: int | None) -> dict:
        nonlocal counter
        counter += 1
        request = dict(command, request_id=f"{spec['id']}:{counter}")
        raw = json.dumps(request, separators=(',', ':')) + '\n'
        before = snapshot(db)
        sent = time.monotonic_ns()
        procs[role].stdin.write(raw.encode()); procs[role].stdin.flush()
        response_line = read_line(procs[role])
        received = time.monotonic_ns()
        response = json.loads(response_line)
        if response['request_id'] != request['request_id']:
            raise RuntimeError('reply identity mismatch')
        entry = {'role': role, 'scheduled_ms': scheduled_ms, 'request_line': raw,
                 'response_line': response_line, 'sent_ns': sent, 'received_ns': received,
                 'before': before, 'after': snapshot(db)}
        journal.write(json.dumps(entry, separators=(',', ':')) + '\n'); journal.flush()
        return response
    try:
        for role in ('producer', 'consumer'):
            handles[role] = (folder / f'{role}.stderr').open('xb')
            argv = [sys.executable, '-B', '-u', str(HERE/'worker.py'), '--db', str(db),
                    '--role', role, '--policy', spec['policy']]
            proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=handles[role], bufsize=0,
                                    env={'PATH': os.environ.get('PATH', ''), 'LANG': 'C.UTF-8',
                                         'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
            procs[role] = proc
            ready_line = read_line(proc)
            ready = json.loads(ready_line)
            assert ready['ready'] is True and ready['pid'] == proc.pid and ready['role'] == role
            metadata['workers'][role] = {'argv': argv, 'pid': proc.pid, 'ready_line': ready_line}
        rpc('producer', {'op': 'offer', 'seq': 5}, None)
        start = time.monotonic_ns()
        metadata['start_ns'] = start
        acked = False
        for event in spec['events']:
            deadline = start + event['ms'] * 1_000_000
            remain = deadline - time.monotonic_ns()
            if remain > 0:
                time.sleep(remain / 1e9)
            role = 'producer' if event['op'] == 'offer' else 'consumer'
            command = {k: v for k, v in event.items() if k != 'ms'}
            reply = rpc(role, command, event['ms'])
            if spec['scenario'] == 'new_gap' and not acked and event['op'] == 'poll':
                accepted = [x.get('head', [None])[0] for x in reply['steps'] if x['status'] == 'EVENT_ACCEPTED']
                if 5 in accepted:
                    rpc('consumer', {'op': 'ack'}, None); acked = True
        for role in procs:
            rpc(role, {'op': 'stop'}, None)
    except BaseException:
        metadata['error'] = traceback.format_exc()
    finally:
        for role, proc in procs.items():
            try:
                proc.stdin.close()
                code = proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill(); code = proc.wait(timeout=3)
                metadata['error'] = (metadata['error'] or '') + '\nWORKER_KILLED_ON_TIMEOUT'
            metadata['exits'][role] = code
            handles[role].close()
        journal.close()
        metadata['final'] = snapshot(db)
        metadata['db_sha256'] = hashlib.sha256(db.read_bytes()).hexdigest()
        metadata['end_ns'] = time.monotonic_ns()
        dump(folder/'case.json', metadata)
    if metadata['error'] or metadata['exits'] != {'producer': 0, 'consumer': 0}:
        raise RuntimeError(f"case stopped: {spec['id']}; retained {folder}")
    return {'id': spec['id'], 'status': 'COMPLETE'}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--schedule', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--freeze', type=Path)
    args = parser.parse_args()
    schedule = json.loads(args.schedule.read_text())
    if args.freeze:
        check_freeze(args.freeze)
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic_ns()
    result = {'allocation': schedule['allocation'], 'planned': len(schedule['cases']),
              'completed': [], 'status': 'RUNNING', 'error': None,
              'schedule_sha256': hashlib.sha256(args.schedule.read_bytes()).hexdigest(),
              'freeze_sha256': hashlib.sha256(args.freeze.read_bytes()).hexdigest() if args.freeze else None,
              'invocations': 1, 'reruns': 0}
    dump(args.out/'invocation.json', result)
    try:
        for spec in schedule['cases']:
            result['completed'].append(run_case(spec, args.out/spec['id']))
            dump(args.out/'invocation.json', result)
        if args.freeze:
            check_freeze(args.freeze)
        result['status'] = 'COMPLETE'
    except BaseException:
        result['status'] = 'STOP_LOCAL_EXECUTION'
        result['error'] = traceback.format_exc()
    result['duration_ns'] = time.monotonic_ns() - started
    dump(args.out/'invocation.json', result)
    print(json.dumps(result))
    return 0 if result['status'] == 'COMPLETE' else 2

if __name__ == '__main__':
    raise SystemExit(main())
