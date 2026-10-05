"""One finite native-SQLite comparison. Every DB and output is exclusive/new."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import _sqlite3
import sqlite3.dbapi2
import subprocess
import sys
import traceback


ROOT = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scalar(conn, sql):
    cursor = conn.execute(sql)
    try:
        return cursor.fetchone()[0]
    finally:
        cursor.close()


def rows(conn, sql):
    cursor = conn.execute(sql)
    try:
        return cursor.fetchall()
    finally:
        cursor.close()


def case(spec, out, record):
    db = out / 'dbs' / (spec['id'] + '.db')
    if db.exists():
        raise RuntimeError('DB already exists; no replay')
    setup = sqlite3.connect(db, isolation_level=None, timeout=0)
    try:
        effective = scalar(setup, 'PRAGMA journal_mode=' + spec['journal'])
        if effective.upper() != spec['journal']:
            raise RuntimeError('unsupported requested journal')
        setup.executescript((ROOT / 'fixture.sql').read_text(encoding='utf-8'))
    finally:
        setup.close()
    record.update({'id': spec['id'], 'journal': spec['journal'], 'policy': spec['policy'],
              'desired': spec['desired'], 'started_utc': utc(), 'producer_pid': os.getpid(),
              'events': [], 'writer_sql': [], 'observer_sql': [], 'db': 'dbs/' + db.name})

    def event(name):
        record['events'].append({'index': len(record['events']), 'name': name})

    writer = sqlite3.connect(db, isolation_level=None, timeout=0)
    observer = None
    writer.set_trace_callback(record['writer_sql'].append)
    try:
        writer.execute('PRAGMA busy_timeout=0').close()
        writer.execute('PRAGMA read_uncommitted=0').close()
        record['writer_settings'] = {
            'busy_timeout': scalar(writer, 'PRAGMA busy_timeout'),
            'read_uncommitted': scalar(writer, 'PRAGMA read_uncommitted'),
            'journal': scalar(writer, 'PRAGMA journal_mode'),
            'synchronous': scalar(writer, 'PRAGMA synchronous')}
        if spec['policy'] != 'endpoint_only':
            uri = db.resolve().as_uri() + '?mode=ro'
            observer = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=0)
            observer.set_trace_callback(record['observer_sql'].append)
            observer.execute('PRAGMA query_only=ON').close()
            observer.execute('PRAGMA busy_timeout=0').close()
            record['observer_settings'] = {
                'uri_mode': 'ro', 'query_only': scalar(observer, 'PRAGMA query_only'),
                'busy_timeout': scalar(observer, 'PRAGMA busy_timeout'),
                'journal': scalar(observer, 'PRAGMA journal_mode')}
            if spec['policy'] != 'short_target':
                observer.execute('BEGIN').close()
            sql = 'SELECT 1' if spec['policy'] == 'held_sham' else 'SELECT value, revision FROM task WHERE task_id=1'
            record['observed_before'] = rows(observer, sql)
            record['observer_in_transaction_before'] = observer.in_transaction
            event('observer_ready')
            if spec['policy'] == 'short_target':
                record['observer_total_changes'] = observer.total_changes
                observer.close()
                observer = None
                event('observer_closed_before_write')
        writer.execute('BEGIN IMMEDIATE').close()
        event('writer_began')
        cursor = writer.execute('UPDATE task SET value=?, revision=revision+1 WHERE task_id=1', (spec['desired'],))
        record['update_count'] = cursor.rowcount
        cursor.close()
        event('writer_updated')
        record['private_row'] = rows(writer, 'SELECT value, revision FROM task WHERE task_id=1')
        event('commit_attempt')
        try:
            writer.execute('COMMIT').close()
            record['commit'] = {'ok': True, 'in_transaction_after': writer.in_transaction}
            event('commit_succeeded')
        except sqlite3.OperationalError as error:
            record['commit'] = {'ok': False, 'error_code': error.sqlite_errorcode,
                'error_name': error.sqlite_errorname, 'error_type': type(error).__name__,
                'message': str(error), 'in_transaction_after': writer.in_transaction}
            event('commit_failed')
            if error.sqlite_errorcode != sqlite3.SQLITE_BUSY:
                raise
            writer.execute('ROLLBACK').close()
            event('writer_rolled_back')
        if observer is not None:
            record['observed_after'] = rows(observer, sql)
            record['observer_in_transaction_after'] = observer.in_transaction
            record['observer_total_changes'] = observer.total_changes
            event('observer_read_after_commit_attempt')
        record['writer_total_changes'] = writer.total_changes
    finally:
        if writer.in_transaction:
            writer.rollback()
        writer.close()
        event('writer_closed')
        if observer is not None:
            if observer.in_transaction:
                observer.execute('ROLLBACK').close()
            observer.close()
            event('observer_closed_after_write')
    event('actors_closed')
    record['db_bytes'] = db.stat().st_size
    record['db_sha256_before_score'] = digest(db)
    event('fresh_scorer_started')
    start = utc()
    argv = [sys.executable, str(ROOT / 'endpoint.py'), str(db)]
    completed = subprocess.run(argv, capture_output=True, timeout=5)
    record['scorer'] = {'argv_role': ['frozen_python', 'endpoint.py', record['db']],
        'started_utc': start, 'finished_utc': utc(), 'exit_code': completed.returncode,
        'stdout': completed.stdout.decode('utf-8'), 'stderr': completed.stderr.decode('utf-8')}
    event('fresh_scorer_finished')
    record['db_sha256_after_score'] = digest(db)
    record['sidecars_after_score'] = [suffix for suffix in ('-journal', '-wal', '-shm')
                                     if Path(str(db) + suffix).exists()]
    record['finished_utc'] = utc()
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    freeze = json.loads(Path(args.freeze).read_bytes())
    for name, expected in freeze['source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError('source differs from prospective freeze: ' + name)
    native_paths = {'python_exe': Path(sys.executable), 'sqlite_extension': Path(_sqlite3.__file__),
                    'sqlite_dll': Path(_sqlite3.__file__).with_name('sqlite3.dll'),
                    'python_dll': Path(sys.base_prefix) / f'python{sys.version_info.major}{sys.version_info.minor}.dll',
                    'sqlite_module': Path(sqlite3.__file__), 'sqlite_dbapi2': Path(sqlite3.dbapi2.__file__)}
    for name, expected in freeze['native_sha256'].items():
        if digest(native_paths[name]) != expected:
            raise RuntimeError('native binary differs: ' + name)
    if sqlite3.sqlite_version != freeze['sqlite_version'] or sys.version != freeze['python_version']:
        raise RuntimeError('native versions differ')
    plan = json.loads((ROOT / 'plan.json').read_bytes())
    out = Path(args.out)
    out.mkdir()  # consumes the exclusive comparison ID, even if a later step fails
    (out / 'dbs').mkdir()
    raw = out / 'raw.jsonl'
    with raw.open('x', encoding='utf-8', newline='\n') as stream:
        for spec in plan['cases']:
            record = {'id': spec['id'], 'stage': 'setup'}
            try:
                case(spec, out, record)
            except Exception:
                record['exception'] = traceback.format_exc()
                (out / 'first_partial_case.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n', encoding='utf-8')
                raise
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
    print(json.dumps({'recorded': len(plan['cases']), 'raw_sha256': digest(raw),
                      'out': args.out, 'classification': 'native comparison recorded; auditor pending'}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(2)
