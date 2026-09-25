"""Cooperative private SQLite actors. Classifications are read-only, not authority."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from vendor531 import Receipt, WatermarkLedger

COLUMNS = ('intent_id', 'intent_seq', 'from_generation', 'to_generation',
           'confirmation_content_id', 'confirmation_revision')


def select_component(db: sqlite3.Connection, name: str):
    if name == 'meta':
        cur = db.execute('SELECT capacity,generation,retired_through_seq FROM meta WHERE id=1')
        value = dict(zip(('capacity','generation','retired_through_seq'), cur.fetchone()))
    elif name == 'history':
        cur = db.execute('SELECT ' + ','.join(COLUMNS) + ' FROM history ORDER BY intent_seq')
        value = [dict(zip(COLUMNS, r)) for r in cur.fetchall()]
    else:
        raise ValueError('UNKNOWN_COMPONENT')
    cur.close()  # Finish each statement; do not accidentally preserve an implicit snapshot.
    return value


def classify(view: dict, requests: dict) -> dict:
    model = WatermarkLedger(view['meta']['capacity'])
    model.generation = view['meta']['generation']
    model.retired_through_seq = view['meta']['retired_through_seq']
    model.history = [Receipt(**r) for r in view['history']]
    before = model.snapshot()
    results = {name: model.classify(Receipt(**r)) for name, r in requests.items()}
    if before != model.snapshot():
        raise RuntimeError('CLASSIFIER_MUTATED_STATE')
    return results


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--role', choices=['reader','writer'], required=True)
    p.add_argument('--db', type=Path, required=True)
    p.add_argument('--case-id', required=True)
    a = p.parse_args()
    uri = a.db.resolve().as_uri() + ('?mode=ro' if a.role == 'reader' else '?mode=rw')
    db = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=2)
    db.execute('PRAGMA busy_timeout=2000')
    if a.role == 'reader':
        db.execute('PRAGMA query_only=ON')
    sql = []
    db.set_trace_callback(sql.append)
    view = {}
    print(json.dumps({'ready':True,'role':a.role,'pid':os.getpid(),'case_id':a.case_id,
                      'clock_ns':time.monotonic_ns()}, sort_keys=True), flush=True)
    try:
        for wire in sys.stdin:
            req = json.loads(wire)
            start = time.monotonic_ns()
            checkpoint = len(sql)
            op = req['op']
            payload = {}
            if op == 'start' and a.role == 'reader':
                if req['policy'] == 'SNAPSHOT':
                    db.execute('BEGIN DEFERRED')
                elif req['policy'] != 'AUTOCOMMIT':
                    raise ValueError('UNKNOWN_POLICY')
            elif op == 'read' and a.role == 'reader':
                component = req['component']
                if component in view:
                    raise ValueError('DUPLICATE_COMPONENT')
                view[component] = select_component(db, component)
                payload = {'component':component,'value':view[component]}
            elif op == 'retire' and a.role == 'writer':
                db.execute('BEGIN IMMEDIATE')
                db.execute('DELETE FROM history')
                db.execute('UPDATE meta SET retired_through_seq=3 WHERE id=1')
                db.execute('COMMIT')
                payload = {'retired_through_seq':3}
            elif op == 'finish' and a.role == 'reader':
                if set(view) != {'meta','history'}:
                    raise RuntimeError('MISSING_COMPONENT')
                decisions = classify(view, req['requests'])
                if db.in_transaction:
                    db.execute('COMMIT')
                payload = {'view':view,'decisions':decisions,'authority':'none',
                           'input_dispatched':False,'state_applied':False}
            elif op == 'close':
                if db.in_transaction:
                    raise RuntimeError('UNFINISHED_TRANSACTION')
            else:
                raise ValueError('INVALID_ROLE_OPERATION')
            response = {'case_id':a.case_id,'request_id':req['request_id'],'op':op,
                        'pid':os.getpid(),'started_ns':start,'ended_ns':time.monotonic_ns(),
                        'sql':sql[checkpoint:],'in_transaction':db.in_transaction,
                        'total_changes':db.total_changes, **payload}
            print(json.dumps(response,sort_keys=True), flush=True)
            if op == 'close':
                break
    finally:
        db.close()


if __name__ == '__main__':
    main()
