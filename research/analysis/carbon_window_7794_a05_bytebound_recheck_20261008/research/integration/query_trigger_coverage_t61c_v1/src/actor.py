"""Private SQLite query/maintenance actor. No GUI, network or external effects."""
import json
import os
from pathlib import Path
import sqlite3
import sys


def metadata(db):
    return {
        'identity': db.execute('SELECT identity FROM meta').fetchone()[0],
        'epoch': db.execute("SELECT epoch FROM scopes WHERE tenant='A'").fetchone()[0],
        'cookie': db.execute('PRAGMA main.schema_version').fetchone()[0],
        'triggers': db.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger' AND tbl_name='items' ORDER BY name").fetchall(),
    }


def main():
    role, dbpath, policy, config = sys.argv[1:]
    expected = json.loads(Path(config).read_text())
    db = sqlite3.connect(dbpath, isolation_level=None, timeout=0)
    db.execute('PRAGMA synchronous=FULL')
    trace = []
    db.set_trace_callback(trace.append)
    prepared = None
    print(json.dumps({'boot': role, 'pid': os.getpid(), 'argv': sys.argv,
                      'sqlite': sqlite3.sqlite_version}), flush=True)
    try:
        for line in sys.stdin:
            request = json.loads(line)
            trace.clear()
            op = request['op']
            if op == 'stop':
                value = {'stopped': True}
            elif role == 'writer' and op == 'change':
                statements = {
                    'drop': 'DROP TRIGGER item_insert',
                    'restore': dict(expected['triggers'])['item_insert'],
                    'insert_a': "INSERT INTO items VALUES(1,'A',1,9,1)",
                    'insert_b': "INSERT INTO items VALUES(1,'B',1,9,1)",
                    'unrelated': 'CREATE TABLE unrelated(note TEXT)',
                }
                db.execute('BEGIN IMMEDIATE')
                for step in request['steps']:
                    db.execute(statements[step])
                db.execute('ROLLBACK' if request['rollback'] else 'COMMIT')
                value = {'changed': True, 'rollback': request['rollback']}
            elif role == 'reader' and op == 'prepare':
                db.execute('BEGIN')
                basis = metadata(db)
                rows = db.execute("SELECT id,payload,revision FROM items WHERE tenant='A' AND active=1 ORDER BY id").fetchall()
                db.execute('COMMIT')
                # SQL text is a contract check, not a semantic trigger verifier.
                supported = basis['identity'] == expected['identity']
                if policy != 'REVISION_ONLY':
                    supported = supported and json.loads(json.dumps(basis['triggers'])) == expected['triggers']
                prepared = dict(basis=basis, rows=rows) if supported else None
                value = {'status': 'PREPARED' if supported else 'UNSUPPORTED',
                         'basis': basis, 'rows': rows}
            elif role == 'reader' and op == 'commit':
                db.execute('BEGIN IMMEDIATE')
                now = metadata(db)  # No current query-result oracle enters this decision.
                reasons = []
                if prepared is None:
                    reasons.append('NO_PREPARATION')
                else:
                    old = prepared['basis']
                    if now['identity'] != old['identity']:
                        reasons.append('IDENTITY_CHANGED')
                    if now['epoch'] != old['epoch']:
                        reasons.append('EPOCH_CHANGED')
                    if policy != 'REVISION_ONLY' and json.loads(json.dumps(now['triggers'])) != expected['triggers']:
                        reasons.append('TRIGGER_CONTRACT_CHANGED')
                    if policy == 'SCHEMA_COOKIE' and now['cookie'] != old['cookie']:
                        reasons.append('SCHEMA_CHANGED')
                if not reasons:
                    db.execute('INSERT INTO effects VALUES(?,?,?)',
                               (expected['identity'], 'A', json.dumps(prepared['rows'], separators=(',', ':'))))
                db.execute('COMMIT')
                value = {'status': 'REFUSED' if reasons else 'STORED',
                         'reasons': reasons, 'basis': now, 'authority': False}
            else:
                raise ValueError('UNKNOWN_OPERATION')
            print(json.dumps({'request': request, 'value': value, 'sql': trace.copy()},
                             separators=(',', ':')), flush=True)
            if op == 'stop':
                break
    finally:
        db.close()


if __name__ == '__main__':
    main()
