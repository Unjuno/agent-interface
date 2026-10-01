"""Private read-session cancellation fixture. No GUI, input or external service."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

role, database, log_path = sys.argv[1:]
log = open(log_path, 'x', encoding='utf-8')
trace = []
con = sqlite3.connect(database, autocommit=True, timeout=0)
con.set_trace_callback(trace.append)
con.execute('PRAGMA busy_timeout=0').close()
con.execute('PRAGMA synchronous=FULL').close()
con.execute('PRAGMA wal_autocheckpoint=0').close()
if role == 'reader':
    con.execute('PRAGMA query_only=ON').close()
cursors, copies = [], []


def close_reads():
    count = len(cursors)
    for cursor in cursors:
        cursor.close()
    cursors.clear()
    rollback = con.in_transaction
    if rollback:
        con.execute('ROLLBACK').close()
    return {'closed': count, 'rollback': rollback}


def handle(q):
    op = q['op']
    if op == 'INIT' and role == 'writer':
        journal = con.execute('PRAGMA journal_mode=WAL').fetchone()[0]
        con.execute('CREATE TABLE t(i INTEGER PRIMARY KEY,v INTEGER)').close()
        con.execute('BEGIN IMMEDIATE').close()
        con.executemany('INSERT INTO t VALUES(?,?)', [(i, i) for i in range(q['n'])]).close()
        con.execute('COMMIT').close()
        checkpoint = list(con.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())
        return {'journal': journal, 'checkpoint': checkpoint, 'n': q['n']}
    if op == 'ARM' and role == 'reader':
        state = q['state']
        if state.startswith('EXPLICIT'):
            con.execute('BEGIN').close()
        if state != 'IDLE':
            cursors.append(con.execute('SELECT i,v FROM t ORDER BY i'))
            first = [list(cursors[0].fetchone())]
            if state == 'EXPLICIT_DONE':
                first.extend(list(x) for x in cursors[0].fetchall())
            copies.append(first)
            if state == 'IMPLICIT_TWO':
                cursors.append(con.execute('SELECT i,v FROM t ORDER BY i'))
                copies.append([list(cursors[1].fetchone())])
        return {'copies': copies, 'cursor_count': len(cursors), 'in_transaction': con.in_transaction}
    if op == 'UPDATE' and role == 'writer':
        con.execute('BEGIN IMMEDIATE').close()
        con.execute('UPDATE t SET v=9999 WHERE i=0').close()
        con.execute('COMMIT').close()
        return {'value': con.execute('SELECT v FROM t WHERE i=0').fetchone()[0]}
    if op == 'CANCEL' and role == 'reader':
        con.interrupt()
        result = {'interrupt_returned': True, 'target_error': None, 'tail': [], 'closed': 0, 'rollback': False}
        if q['mode'] == 'AWAIT_TARGET' and cursors:
            try:
                result['tail'] = [list(x) for x in cursors[0].fetchall()]
            except sqlite3.OperationalError as error:
                result['target_error'] = {'type': type(error).__name__, 'message': str(error), 'code': error.sqlite_errorcode, 'name': error.sqlite_errorname}
        if q['mode'] == 'FINALIZE_ALL':
            result.update(close_reads())
        result.update(in_transaction=con.in_transaction, copies=copies)
        return result
    if op == 'CHECK' and role == 'writer':
        checkpoint = list(con.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())
        wal = Path(database + '-wal')
        return {'checkpoint': checkpoint, 'wal_bytes': wal.stat().st_size if wal.exists() else 0}
    if op == 'CLEAN' and role == 'reader':
        result = close_reads()
        return dict(result, in_transaction=con.in_transaction, copies=copies)
    if op == 'QUIT':
        con.close()
        return {'closed_connection': True}
    raise ValueError('unsupported fixture command')


for raw in sys.stdin:
    log.write(json.dumps({'recv': raw}) + '\n'); log.flush()
    q = json.loads(raw)
    started = time.monotonic_ns()
    value = handle(q)
    reply = {'op': q['op'], 'role': role, 'pid': os.getpid(), 'start_ns': started, 'end_ns': time.monotonic_ns(), 'value': value, 'sql': list(trace)}
    trace.clear()
    text = json.dumps(reply, sort_keys=True, separators=(',', ':')) + '\n'
    log.write(json.dumps({'send': text}) + '\n'); log.flush()
    sys.stdout.write(text); sys.stdout.flush()
    if q['op'] == 'QUIT':
        break
log.close()
