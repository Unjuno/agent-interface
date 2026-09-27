"""Disposable counter receiver; no network, GUI, or external application effect."""
import argparse
import json
import os
import sqlite3
import sys


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate(req):
    if type(req) is not dict or set(req) != {'scope', 'operation_id', 'delta'}:
        raise ValueError('request_shape')
    if req['scope'] != 'e5d7-private':
        raise ValueError('scope')
    if type(req['operation_id']) is not str or not 1 <= len(req['operation_id']) <= 32:
        raise ValueError('operation_id')
    if type(req['delta']) is not int or not -3 <= req['delta'] <= 3:
        raise ValueError('delta')


def receive(path, req, policy, crash):
    validate(req)
    if policy not in ('CURRENT_PROJECTION', 'RECORDED_RESULT'):
        raise ValueError('policy')
    db = sqlite3.connect(path, isolation_level=None, timeout=0)
    db.set_trace_callback(lambda sql: print(sql, file=sys.stderr, flush=True))
    db.execute('PRAGMA synchronous=FULL')
    db.execute('BEGIN IMMEDIATE')
    counter, version = db.execute('SELECT counter,version FROM state WHERE singleton=1').fetchone()
    old = db.execute('SELECT delta,counter_after,commit_version FROM effects WHERE operation_id=?',
                     (req['operation_id'],)).fetchone()
    fresh = False
    result = None
    status = 'CONFLICT'
    if old is None:
        counter += req['delta']
        version += 1
        db.execute('UPDATE state SET counter=?,version=? WHERE singleton=1', (counter, version))
        db.execute('INSERT INTO effects VALUES(?,?,?,?)',
                   (req['operation_id'], req['delta'], counter, version))
        result = {'operation_id': req['operation_id'], 'counter_after': counter, 'commit_version': version}
        fresh, status = True, 'APPLIED'
    elif old[0] == req['delta']:
        value, commit = (counter, version) if policy == 'CURRENT_PROJECTION' else (old[1], old[2])
        result = {'operation_id': req['operation_id'], 'counter_after': value, 'commit_version': commit}
        status = 'REPLAYED'
    db.execute('COMMIT')
    # This deliberate termination belongs to this disposable process only.
    if crash:
        print('OWNED_EXIT_AFTER_COMMIT_73', file=sys.stderr, flush=True)
        os._exit(73)
    db.close()
    return {'status': status, 'result': result, 'current': {'counter': counter, 'version': version},
            'new_effect': fresh, 'authority': False, 'task_success': None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    parser.add_argument('--policy', required=True)
    parser.add_argument('--crash', action='store_true')
    args = parser.parse_args()
    print(encode(receive(args.db, json.load(sys.stdin), args.policy, args.crash)), flush=True)
