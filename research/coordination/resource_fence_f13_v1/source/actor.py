"""Cooperative private SQLite actors; no application or OS input authority."""
import json
import os
import sqlite3
import sys


def emit(value):
    print(json.dumps(value, sort_keys=True, separators=(',', ':')), flush=True)


def serve(role, mode, path, scope, trace_path):
    trace = open(trace_path, 'x', encoding='utf-8')
    db = sqlite3.connect(path, timeout=0, isolation_level=None)
    db.set_trace_callback(lambda sql: (trace.write(sql + '\n'), trace.flush()))
    db.execute('PRAGMA journal_mode=DELETE')
    db.execute('PRAGMA synchronous=FULL')
    db.execute('PRAGMA busy_timeout=0')
    db.execute('BEGIN IMMEDIATE')
    db.execute('CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,epoch INTEGER,value INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS journal(n INTEGER PRIMARY KEY,request TEXT,response TEXT)')
    for k, v in [('scope', scope), ('epoch', '7'), ('highwater', '7')]:
        db.execute('INSERT OR IGNORE INTO meta VALUES(?,?)', (k, v))
    db.execute('COMMIT')

    def state():
        m = dict(db.execute('SELECT k,v FROM meta'))
        return {'scope': m['scope'], 'epoch': int(m['epoch']),
                'highwater': int(m['highwater']),
                'entries': [list(r) for r in db.execute('SELECT * FROM entries ORDER BY id')]}

    emit({'boot': True, 'pid': os.getpid(), 'role': role, 'mode': mode, 'state': state()})
    try:
        for line in sys.stdin:
            q = json.loads(line)
            if q['op'] in ('close', 'exit23'):
                emit({'status': 'CLOSED' if q['op'] == 'close' else 'EXIT23'})
                if q['op'] == 'exit23':
                    os._exit(23)
                break
            db.execute('BEGIN IMMEDIATE')
            before = state()
            status, grant = 'INVALID', None
            if role == 'issuer' and q['op'] == 'grant':
                existing = db.execute('SELECT epoch,value FROM entries WHERE id=?', (q['id'],)).fetchone()
                if existing is None and type(q['value']) is int:
                    grant = {'scope': scope, 'id': q['id'], 'epoch': before['epoch'], 'value': q['value']}
                    db.execute('INSERT INTO entries VALUES(?,?,?)', (q['id'], before['epoch'], q['value']))
                    status = 'GRANTED'
            elif role == 'issuer' and q['op'] == 'retire':
                if type(q['next']) is int and q['expected'] == before['epoch'] and q['next'] > before['epoch']:
                    db.execute("UPDATE meta SET v=? WHERE k='epoch'", (str(q['next']),))
                    status = 'RETIRED'
                else:
                    status = 'WRONG_EPOCH'
            elif role == 'resource' and q['op'] == 'install':
                if mode == 'INSTALLED_EPOCH' and q['expected'] == before['epoch'] and type(q['next']) is int and q['next'] > before['epoch']:
                    db.execute("UPDATE meta SET v=? WHERE k='epoch'", (str(q['next']),))
                    status = 'INSTALLED'
                else:
                    status = 'WRONG_EPOCH'
            elif role == 'resource' and q['op'] == 'apply':
                g = q['grant']
                typed = type(g.get('epoch')) is int and g['epoch'] > 0 and type(g.get('value')) is int
                existing = db.execute('SELECT epoch,value FROM entries WHERE id=?', (g.get('id'),)).fetchone()
                if not typed or g.get('scope') != scope or not isinstance(g.get('id'), str):
                    status = 'BAD_SCOPE_OR_TYPE'
                elif existing is not None:
                    status = 'DUPLICATE' if list(existing) == [g['epoch'], g['value']] else 'CONFLICT'
                elif mode == 'MAX_SEEN' and g['epoch'] < before['highwater']:
                    status = 'OLD_TOKEN'
                elif mode == 'INSTALLED_EPOCH' and g['epoch'] != before['epoch']:
                    status = 'WRONG_EPOCH'
                else:
                    db.execute('INSERT INTO entries VALUES(?,?,?)', (g['id'], g['epoch'], g['value']))
                    db.execute("UPDATE meta SET v=? WHERE k='highwater'", (str(max(before['highwater'], g['epoch'])),))
                    status = 'APPLIED'
            response = {'status': status, 'before': before, 'after': state(),
                        'grant': grant, 'authority_granted': False, 'task_success': None}
            db.execute('INSERT INTO journal(request,response) VALUES(?,?)',
                       (json.dumps(q, sort_keys=True), json.dumps(response, sort_keys=True)))
            db.execute('COMMIT')
            emit(response)
    finally:
        db.close()
        trace.close()


if __name__ == '__main__':
    serve(*sys.argv[1:])
