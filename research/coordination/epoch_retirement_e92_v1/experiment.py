"""Private SQLite epoch-retirement experiment; no action/input authority."""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

POLICIES = ('DELETE_FIRST', 'FENCE_FIRST')
SCHEDULES = ('BASELINE', 'FIRST_UNCOMMITTED', 'BETWEEN_COMMITS',
             'SECOND_UNCOMMITTED', 'COMPLETE', 'FOREIGN_EXPECTATION')
SOURCE = Path(__file__).resolve()


def emit(kind: str, **fields: object) -> None:
    print(json.dumps({'kind': kind, **fields}, sort_keys=True), flush=True)


def connection(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=0, isolation_level=None)
    db.execute('PRAGMA journal_mode=DELETE')
    db.execute('PRAGMA synchronous=FULL')
    return db


def initialize(path: Path) -> None:
    db = connection(path)
    db.executescript('CREATE TABLE meta(current_epoch INTEGER NOT NULL);'
                     'INSERT INTO meta VALUES(7);'
                     'CREATE TABLE excluded(epoch INTEGER, id TEXT, '
                     'PRIMARY KEY(epoch,id));'
                     "INSERT INTO excluded VALUES(7,'A'),(7,'B'),(7,'C');")
    db.close()


def writer(path: Path, policy: str, schedule: str) -> None:
    db = connection(path)
    emit('start', pid=os.getpid(), role='writer', policy=policy, schedule=schedule,
         journal_mode=db.execute('PRAGMA journal_mode').fetchone()[0],
         synchronous=db.execute('PRAGMA synchronous').fetchone()[0])
    db.set_trace_callback(lambda sql: emit('sql', sql=sql))
    expected = 6 if schedule == 'FOREIGN_EXPECTATION' else 7
    if db.execute('SELECT current_epoch FROM meta').fetchone()[0] != expected:
        emit('refused', reason='EXPECTED_EPOCH_MISMATCH')
        db.close()
        return
    if schedule == 'BASELINE':
        emit('baseline')
        db.close()
        return
    operations = ('DELETE', 'FENCE') if policy == 'DELETE_FIRST' else ('FENCE', 'DELETE')
    for index, operation in enumerate(operations, 1):
        db.execute('BEGIN IMMEDIATE')
        if operation == 'DELETE':
            db.execute('DELETE FROM excluded WHERE epoch=7')
        else:
            db.execute('UPDATE meta SET current_epoch=8 WHERE current_epoch=7')
        emit('pending', index=index, operation=operation)
        if schedule == ('FIRST_UNCOMMITTED' if index == 1 else 'SECOND_UNCOMMITTED'):
            emit('declared_exit', code=23)
            os._exit(23)
        db.execute('COMMIT')
        emit('committed', index=index, operation=operation)
        if index == 1 and schedule == 'BETWEEN_COMMITS':
            emit('declared_exit', code=23)
            os._exit(23)
    emit('maintenance_complete')
    db.close()


def reader(path: Path) -> None:
    db = connection(path)  # SQLite may recover an unfinished transaction here.
    epoch = db.execute('SELECT current_epoch FROM meta').fetchone()[0]
    excluded = [list(row) for row in db.execute('SELECT epoch,id FROM excluded ORDER BY epoch,id')]
    checks = []
    for requested_epoch, key in ((7, 'A'), (7, 'D'), (8, 'A'), (9, 'A')):
        reason = ('EPOCH_MISMATCH' if requested_epoch != epoch else
                  'EXCLUDED' if [requested_epoch, key] in excluded else 'ELIGIBLE')
        checks.append({'epoch': requested_epoch, 'id': key, 'reason': reason})
    emit('reader', pid=os.getpid(), epoch=epoch, excluded=excluded, probes=checks,
         integrity=db.execute('PRAGMA integrity_check').fetchone()[0],
         authority_granted=False, task_success=None)
    db.close()


def snapshot(path: Path) -> dict:
    files = {}
    for name, item in (('db', path), ('journal', Path(str(path) + '-journal'))):
        if item.exists():
            data = item.read_bytes()
            files[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                           'base64': base64.b64encode(data).decode('ascii')}
    return files


def child(*arguments: str) -> dict:
    argv = [sys.executable, '-S', '-B', str(SOURCE), *arguments]
    start = time.monotonic_ns()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=8)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate()
    return {'argv': argv, 'pid': process.pid, 'exit': process.returncode,
            'timed_out': timed_out, 'start_ns': start, 'end_ns': time.monotonic_ns(),
            'stdout': stdout.decode('utf-8'), 'stderr': stderr.decode('utf-8')}


def run_batch(root: Path, schedule_index: int, phase: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    claim = root / f'batch-{schedule_index}.claim'
    with claim.open('x') as stream:
        stream.write(f'{os.getpid()}\n')
    schedule = SCHEDULES[schedule_index]
    names = []
    for policy in POLICIES:
        for repetition in range(2):
            name = f'{schedule_index}-{policy}-{repetition}'
            case_path = root / f'{name}.json'
            workspace = root / 'work' / name
            workspace.mkdir(parents=True, exist_ok=False)
            database = workspace / 'state.db'
            initialize(database)
            record = {'id': name, 'phase': phase, 'schedule': schedule, 'policy': policy,
                      'repetition': repetition, 'initial': snapshot(database)}
            record['writer'] = child('writer', str(database), policy, schedule)
            record['before_reopen'] = snapshot(database)
            expected_exit = 23 if schedule in SCHEDULES[1:4] else 0
            if record['writer']['exit'] == expected_exit and not record['writer']['timed_out']:
                record['reader'] = child('reader', str(database))
                record['after_reopen'] = snapshot(database)
            case_path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n')
            names.append(name)
            if (record['writer']['exit'] != expected_exit or record['writer']['timed_out']
                    or record.get('reader', {}).get('exit') != 0):
                raise RuntimeError('Incomplete first outcome: ' + name)
    (root / f'batch-{schedule_index}.json').write_text(json.dumps(
        {'batch': schedule_index, 'phase': phase, 'pid': os.getpid(), 'cases': names},
        sort_keys=True) + '\n')


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'writer':
        writer(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
    elif mode == 'reader':
        reader(Path(sys.argv[2]))
    elif mode == 'batch':
        run_batch(Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    else:
        raise SystemExit('Expected writer, reader or batch')
