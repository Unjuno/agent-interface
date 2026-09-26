"""Cooperative private SQLite application. Deliberately NO retired-epoch submit fence.
Both experimental clients use these same bytes. Never deploy as a GUI/runtime guard.
"""
import json
import os
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote


def check_request(q):
    if (type(q) is not dict or set(q) != {'session','resource','epoch','op_id','delta'}
        or any(type(q[k]) is not str or not 0 < len(q[k]) <= 64
               for k in ('session','resource','op_id'))
        or type(q['epoch']) is not int or not 0 < q['epoch'] < 2**63
        or type(q['delta']) is not int or not 0 < q['delta'] <= 9):
        raise ValueError('invalid fixture request')


def main():
    db = Path(sys.argv[1]).resolve()
    command = json.loads(sys.stdin.readline())
    op = command['op']
    if op not in ('init','execute','retire','query'):
        raise ValueError('invalid operation')
    if op == 'init' and db.exists():
        raise FileExistsError(db)
    if op != 'init' and not db.is_file():
        raise FileNotFoundError(db)
    uri = 'file:' + quote(str(db), safe='/') + ('?mode=ro' if op == 'query' else '?mode=rwc')
    connection = sqlite3.connect(uri, uri=True, timeout=1, isolation_level=None)
    sql = []
    connection.set_trace_callback(sql.append)
    if op == 'query':
        # Enforced at SQLite's access boundary, not just a self-reported flag.
        def readonly(action, table, column, database, trigger):
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ and table in ('meta','receipts'):
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        connection.set_authorizer(readonly)
    else:
        connection.execute('PRAGMA journal_mode=DELETE')
        connection.execute('PRAGMA synchronous=FULL')
    result = None
    if op == 'init':
        connection.executescript('''BEGIN IMMEDIATE;
CREATE TABLE meta(id INTEGER PRIMARY KEY, session TEXT, resource TEXT, epoch INTEGER);
CREATE TABLE receipts(epoch INTEGER, op_id TEXT, request TEXT, status TEXT,
                      PRIMARY KEY(epoch,op_id));
CREATE TABLE effects(serial INTEGER PRIMARY KEY, session TEXT, resource TEXT,
                     epoch INTEGER, op_id TEXT, delta INTEGER);
INSERT INTO meta VALUES(1,'fixture-session','counter',7);
COMMIT;''')
        result = {'status': 'INITIALIZED'}
    elif op == 'retire':
        connection.execute('BEGIN IMMEDIATE')
        epoch = connection.execute('SELECT epoch FROM meta WHERE id=1').fetchone()[0]
        connection.execute('DELETE FROM receipts WHERE epoch<=?', (epoch,))
        connection.execute('UPDATE meta SET epoch=? WHERE id=1', (epoch+1,))
        connection.execute('COMMIT')
        result = {'status': 'RETIRED', 'coverage_epoch': epoch+1}
    elif op == 'query':
        q = command['request']
        session, resource, epoch = connection.execute(
            'SELECT session,resource,epoch FROM meta WHERE id=1').fetchone()
        old = connection.execute('SELECT request,status FROM receipts WHERE epoch=? AND op_id=?',
                                 (q['epoch'],q['op_id'])).fetchone()
        result = {'request': q, 'scope': {'session':session,'resource':resource},
                  'coverage_epoch': epoch, 'receipt': None if old is None else
                  {'request': json.loads(old[0]), 'status': old[1]},
                  'authority':'none','input_dispatched':False}
    else:
        q = command['request']
        check_request(q)
        connection.execute('BEGIN IMMEDIATE')
        scope = connection.execute('SELECT session,resource FROM meta WHERE id=1').fetchone()
        if scope != (q['session'],q['resource']):
            raise ValueError('wrong scope')
        old = connection.execute('SELECT request,status FROM receipts WHERE epoch=? AND op_id=?',
                                 (q['epoch'],q['op_id'])).fetchone()
        if old:
            result = {'status':'REPLAY' if json.loads(old[0]) == q else 'CONFLICT_CONTENT'}
        else:
            connection.execute('INSERT INTO effects(session,resource,epoch,op_id,delta) VALUES(?,?,?,?,?)',
                               (q['session'],q['resource'],q['epoch'],q['op_id'],q['delta']))
            connection.execute('INSERT INTO receipts VALUES(?,?,?,?)',
                               (q['epoch'],q['op_id'],json.dumps(q,sort_keys=True),'COMPLETED'))
            result = {'status':'APPLIED'}
        connection.execute('COMMIT')
    connection.close()
    print(json.dumps({'pid':os.getpid(),'operation':op,'result':result,'sql':sql},sort_keys=True),flush=True)

if __name__ == '__main__':
    main()
