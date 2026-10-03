"""Separate retained-data reference; never imports or runs assay/endpoint."""
import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parent
MODES = ('DELETE', 'WAL')
POLICIES = ('endpoint_only', 'short_target', 'held_sham', 'held_target')
VALUES = ('saved-A', 'saved-B')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def equal(left, right, reason):
    # Exact JSON types, including bool/int, matter to these finite records.
    require(json.dumps(left, sort_keys=True, allow_nan=False) ==
            json.dumps(right, sort_keys=True, allow_nan=False), reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(records, out, freeze):
    deck = [(m, p, v) for m in MODES for p in POLICIES for v in VALUES]
    equal(len(records), 16, 'coverage count')
    commits, blocked, stale = 0, 0, 0
    for index, (row, (mode, policy, value)) in enumerate(zip(records, deck)):
        case_id = f'{index:02d}-{mode.lower()}-{policy}-{value[-1].lower()}'
        equal([row['id'], row['journal'], row['policy'], row['desired']],
              [case_id, mode, policy, value], 'ordered condition')
        require(type(row['producer_pid']) is int and row['producer_pid'] > 0, 'producer PID')
        equal(row['writer_settings'], {'busy_timeout': 0, 'read_uncommitted': 0,
              'journal': mode.lower(), 'synchronous': 2}, 'native writer settings')
        equal(row['update_count'], 1, 'one successful UPDATE')
        equal(row['private_row'], [[value, 1]], 'writer private effect')
        equal(row['writer_total_changes'], 1, 'native changed-row count')
        busy = mode == 'DELETE' and policy == 'held_target'
        commit = {'ok': False, 'error_code': 5, 'error_name': 'SQLITE_BUSY',
                  'error_type': 'OperationalError', 'message': 'database is locked',
                  'in_transaction_after': True} if busy else {'ok': True, 'in_transaction_after': False}
        equal(row['commit'], commit, 'predeclared COMMIT result')
        expected_sql = ['PRAGMA busy_timeout=0', 'PRAGMA read_uncommitted=0',
            'PRAGMA busy_timeout', 'PRAGMA read_uncommitted', 'PRAGMA journal_mode',
            'PRAGMA synchronous', 'BEGIN IMMEDIATE',
            f"UPDATE task SET value='{value}', revision=revision+1 WHERE task_id=1",
            'SELECT value, revision FROM task WHERE task_id=1', 'COMMIT']
        if busy:
            expected_sql.append('ROLLBACK')
        equal(row['writer_sql'], expected_sql, 'actual writer SQL; no retry')
        names = []
        observer_sql = []
        if policy != 'endpoint_only':
            equal(row['observer_settings'], {'uri_mode': 'ro', 'query_only': 1,
                'busy_timeout': 0, 'journal': mode.lower()}, 'read-only observer settings')
            equal(row['observer_total_changes'], 0, 'observer mutated rows')
            held = policy != 'short_target'
            equal(row['observer_in_transaction_before'], held, 'observer lifetime before')
            before = [[1]] if policy == 'held_sham' else [['old', 0]]
            equal(row['observed_before'], before, 'observer prior state')
            observer_sql = ['PRAGMA query_only=ON', 'PRAGMA busy_timeout=0',
                'PRAGMA query_only', 'PRAGMA busy_timeout', 'PRAGMA journal_mode']
            if held:
                observer_sql.append('BEGIN')
            query = 'SELECT 1' if policy == 'held_sham' else 'SELECT value, revision FROM task WHERE task_id=1'
            observer_sql.append(query)
            names.append('observer_ready')
            if not held:
                names.append('observer_closed_before_write')
            else:
                equal(row['observed_after'], before, 'held observer snapshot')
                equal(row['observer_in_transaction_after'], True, 'observer lifetime after')
                observer_sql.extend([query, 'ROLLBACK'])
        else:
            require(not any(k.startswith('observer_') and k != 'observer_sql' for k in row), 'endpoint-only observer absent')
        equal(row['observer_sql'], observer_sql, 'actual observer SQL')
        names.extend(['writer_began', 'writer_updated', 'commit_attempt',
                      'commit_failed' if busy else 'commit_succeeded'])
        if busy:
            names.append('writer_rolled_back')
        if policy in ('held_sham', 'held_target'):
            names.append('observer_read_after_commit_attempt')
        names.append('writer_closed')
        if policy in ('held_sham', 'held_target'):
            names.append('observer_closed_after_write')
        names.extend(['actors_closed', 'fresh_scorer_started', 'fresh_scorer_finished'])
        equal(row['events'], [{'index': i, 'name': n} for i, n in enumerate(names)], 'actual lifecycle order')
        expected_rows = [[1, 'old', 0]] if busy else [[1, value, 1]]
        child = row['scorer']
        equal(child['exit_code'], 0, 'native scorer exit')
        equal(child['stderr'], '', 'scorer stderr')
        equal(child['argv_role'], ['frozen_python', 'endpoint.py', row['db']], 'scorer invocation')
        scored = json.loads(child['stdout'])
        require(type(scored['pid']) is int and scored['pid'] > 0 and scored['pid'] != row['producer_pid'], 'fresh process')
        equal({k: v for k, v in scored.items() if k != 'pid'},
              {'rows': expected_rows, 'query_only': 1, 'total_changes': 0,
               'in_transaction': False, 'sqlite_version': freeze['sqlite_version'],
               'uri_mode': 'ro', 'closed': True,
               'sql_trace': ['PRAGMA query_only=ON', 'PRAGMA query_only',
                             'SELECT task_id, value, revision FROM task ORDER BY task_id']}, 'fresh scorer primitive')
        path = out / row['db']
        equal(row['db'], 'dbs/' + case_id + '.db', 'private DB path')
        equal(row['db_bytes'], path.stat().st_size, 'DB size')
        require(type(row['db_bytes']) is int and row['db_bytes'] <= 65536, 'bounded DB')
        equal(row['db_sha256_before_score'], sha(path), 'actual persisted DB bytes')
        equal(row['db_sha256_after_score'], sha(path), 'scorer left DB bytes unchanged')
        equal(row['sidecars_after_score'], [], 'closed witness needs no missing sidecar')
        conn = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, isolation_level=None, timeout=0)
        try:
            conn.execute('PRAGMA query_only=ON')
            actual = conn.execute('SELECT task_id, value, revision FROM task ORDER BY task_id').fetchall()
        finally:
            conn.close()
        equal(actual, expected_rows, 'independent DB witness read')
        equal(sha(path), row['db_sha256_before_score'], 'auditor left DB bytes unchanged')
        times = [datetime.fromisoformat(row['started_utc']), datetime.fromisoformat(child['started_utc']),
                 datetime.fromisoformat(child['finished_utc']), datetime.fromisoformat(row['finished_utc'])]
        require(all(t.utcoffset().total_seconds() == 0 for t in times) and times == sorted(times), 'actual UTC sequence')
        blocked += busy
        commits += not busy
        stale += mode == 'WAL' and policy == 'held_target'
    return {'rows': 16, 'committed': commits, 'busy_and_rolled_back': blocked,
            'wal_held_snapshot_old_despite_fresh_desired': stale,
            'classification': 'finite native observer-intervention construction reconciled'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--freeze', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    freeze = json.loads(Path(args.freeze).read_bytes())
    for name, expected in freeze['source_sha256'].items():
        equal(sha(ROOT / name), expected, 'prospective source pin: ' + name)
    plan = json.loads((ROOT / 'plan.json').read_bytes())
    records = [json.loads(line) for line in (out / 'raw.jsonl').read_text(encoding='utf-8').splitlines()]
    equal([{'id': x['id'], 'journal': x['journal'], 'policy': x['policy'], 'desired': x['desired']} for x in records], plan['cases'], 'separate coverage deck')
    result = check(records, out, freeze)
    controls = {
        'missing': lambda r: r.pop(),
        'duplicate': lambda r: r.__setitem__(1, copy.deepcopy(r[0])),
        'commit_flip': lambda r: r[6]['commit'].__setitem__('ok', True),
        'observer_sql_hidden': lambda r: r[6]['observer_sql'].remove('BEGIN'),
        'query_only_bool': lambda r: r[2]['observer_settings'].__setitem__('query_only', True),
        'endpoint_lie': lambda r: r[6]['scorer'].__setitem__('stdout', r[0]['scorer']['stdout']),
        'db_hash': lambda r: r[0].__setitem__('db_sha256_before_score', '0' * 64),
        'native_exit': lambda r: r[0]['scorer'].__setitem__('exit_code', 9)}
    equal(list(controls), plan['copied_raw_controls'], 'prospective corruption deck')
    detected = []
    for name, corrupt in controls.items():
        copied = copy.deepcopy(records)
        corrupt(copied)
        require(json.dumps(copied, sort_keys=True) != json.dumps(records, sort_keys=True), 'ineffective copied control: ' + name)
        try:
            check(copied, out, freeze)
        except ValueError as error:
            detected.append({'control': name, 'rejected': str(error)})
        else:
            raise ValueError('copied control accepted: ' + name)
    result.update(copied_raw_controls=detected, raw_sha256=sha(out / 'raw.jsonl'),
                  freeze_sha256=sha(args.freeze), producer_reexecuted=False)
    with (out / 'audit.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
