"""Cooperative local counter receiver; not a production GUI retry adapter."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def initialize(path):
    con = sqlite3.connect(path, isolation_level=None)
    con.execute('PRAGMA journal_mode=DELETE')
    con.execute('PRAGMA synchronous=FULL')
    con.executescript('''
    CREATE TABLE effects(seq INTEGER PRIMARY KEY, attempt TEXT NOT NULL, delta INTEGER NOT NULL);
    CREATE TABLE receipts(key TEXT PRIMARY KEY, session TEXT NOT NULL, resource TEXT NOT NULL,
      intent TEXT NOT NULL, attempt TEXT NOT NULL, fingerprint TEXT NOT NULL, delta INTEGER NOT NULL);
    ''')
    con.close()


def handle(path, policy, req):
    result = {'rpc': req.get('rpc'), 'input_authority': False, 'replay_authority': False}
    if req.get('op') == 'stop':
        return dict(result, status='STOPPED', sql=[])
    required = {'op', 'rpc', 'session', 'resource', 'intent', 'attempt', 'delta'}
    if set(req) != required or req.get('op') not in ('submit', 'query'):
        return dict(result, status='INVALID_SCHEMA', sql=[])
    if any(type(req[k]) is not str or not 1 <= len(req[k]) <= 64
           for k in ('rpc', 'session', 'resource', 'intent', 'attempt')):
        return dict(result, status='INVALID_TYPE', sql=[])
    if type(req['delta']) is not int or not 1 <= req['delta'] <= 5:
        return dict(result, status='INVALID_TYPE', sql=[])
    if req['session'] != 'S' or req['resource'] != 'R':
        return dict(result, status='WRONG_SCOPE', sql=[])
    sql = []
    if req['op'] == 'query':
        con = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
        con.set_trace_callback(sql.append)
        rows = con.execute('SELECT attempt, delta FROM receipts WHERE session=? AND resource=? AND intent=? ORDER BY attempt',
                           (req['session'], req['resource'], req['intent'])).fetchall()
        con.close()
        return dict(result, status='COMPLETED' if rows else 'NOT_FOUND', receipts=rows, sql=sql)
    parts = [req['session'], req['resource'], req['intent']]
    if policy == 'ATTEMPT_KEY':
        parts.append(req['attempt'])
    elif policy != 'INTENT_KEY':
        raise ValueError('unrecognized policy')
    key = encode(parts)
    fingerprint = hashlib.sha256(encode({'resource': req['resource'], 'delta': req['delta']}).encode()).hexdigest()
    con = sqlite3.connect(path, isolation_level=None)
    con.execute('PRAGMA synchronous=FULL')
    con.set_trace_callback(sql.append)
    try:
        con.execute('BEGIN IMMEDIATE')
        prior = con.execute('SELECT fingerprint, attempt FROM receipts WHERE key=?', (key,)).fetchone()
        if prior:
            con.execute('ROLLBACK')
            return dict(result, status='DUPLICATE' if prior[0] == fingerprint else 'CONFLICT',
                        original_attempt=prior[1], sql=sql)
        con.execute('INSERT INTO effects(attempt,delta) VALUES(?,?)', (req['attempt'], req['delta']))
        con.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?,?)',
                    (key, req['session'], req['resource'], req['intent'], req['attempt'], fingerprint, req['delta']))
        con.execute('COMMIT')
        return dict(result, status='APPLIED', original_attempt=req['attempt'], sql=sql)
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('database', type=Path)
    ap.add_argument('policy', choices=['ATTEMPT_KEY', 'INTENT_KEY'])
    ap.add_argument('journal', type=Path)
    a = ap.parse_args()
    initialize(a.database)
    print(encode({'ready': True, 'pid': os.getpid()}), flush=True)
    with a.journal.open('x', encoding='utf-8') as out:
        for wire in sys.stdin:
            req = json.loads(wire)
            response = handle(a.database, a.policy, req)
            reply = encode(response) + '\n'
            out.write(encode({'request_wire': wire, 'response_wire': reply}) + '\n')
            out.flush()
            print(reply, end='', flush=True)
            if req.get('op') == 'stop':
                return 0
    raise RuntimeError('uncommanded EOF')


if __name__ == '__main__':
    raise SystemExit(main())
