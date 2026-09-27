"""Cooperative local SQL owner/peer. No arbitrary SQL or external endpoints."""
import json
import pathlib
import sqlite3
import sys

SQL = 'SELECT value,revision FROM slot.v_dep'
TABLES = ('alpha', 'beta')


def main():
    role, root_arg, policy = sys.argv[1:]
    root = pathlib.Path(root_arg)
    log = (root / (role + '.sql.jsonl')).open('x', encoding='utf-8')
    serial = 0
    callbacks = []
    collect = False
    con = None
    generations = {}
    metadata = {}
    token = None

    def record(kind, data):
        log.write(json.dumps({'request': serial, 'kind': kind, 'data': data}) + '\n')
        log.flush()

    def connect(path, readonly=False):
        uri = path.as_uri() + '?mode=ro' if readonly else str(path)
        db = sqlite3.connect(uri, uri=readonly, isolation_level=None,
                             timeout=2, cached_statements=128)
        db.set_trace_callback(lambda sql: record('sql', sql))
        return db

    def authorizer(*args):
        if collect:
            callbacks.append(list(args))
        record('authorizer', list(args))
        return sqlite3.SQLITE_OK

    def bind(alias, name):
        if alias not in ('slot', 'other') or name not in ('A', 'B', 'U'):
            raise ValueError('UNSUPPORTED_BINDING')
        if alias in generations:
            con.execute('DETACH DATABASE ' + alias)
        con.execute('ATTACH DATABASE ? AS ' + alias, (str(root / (name + '.db')),))
        generations[alias] = generations.get(alias, 0) + 1
        return {'alias': alias, 'generation': generations[alias], 'database': name}

    if role == 'reader':
        if policy not in ('SCHEMA_ONLY', 'BINDING_SCOPED'):
            raise ValueError('UNSUPPORTED_POLICY')
        con = connect(root / 'main.db')
        con.set_authorizer(authorizer)
        bind('slot', 'A')
        bind('other', 'U')
    elif role != 'peer':
        raise ValueError('UNSUPPORTED_ROLE')

    try:
        for line in sys.stdin:
            request = json.loads(line)
            serial += 1
            op = request['op']
            record('request', request)
            if op == 'stop':
                result = {'stopped': True}
            elif role == 'reader' and op == 'bind':
                result = bind(request['alias'], request['database'])
            elif role == 'reader' and op == 'prepare':
                con.execute('BEGIN')
                schema = con.execute('PRAGMA slot.schema_version').fetchone()[0]
                key = ('slot', SQL, schema)
                if policy == 'BINDING_SCOPED':
                    key += (generations['slot'],)
                callbacks.clear()
                collect = True
                value, revision = con.execute(SQL).fetchone()
                collect = False
                observed = sorted({x[1] for x in callbacks
                                   if x[0] == sqlite3.SQLITE_READ
                                   and x[1] in TABLES and x[3] == 'slot'})
                reused = key in metadata
                if not reused:
                    if len(observed) != 1:
                        raise ValueError('UNKNOWN_DEPENDENCY')
                    metadata[key] = observed
                dependencies = {table: con.execute(
                    'SELECT revision FROM slot.' + table).fetchone()[0]
                    for table in metadata[key]}
                token = {'schema': schema, 'binding': generations['slot'],
                         'dependencies': dependencies, 'value': value,
                         'row_revision': revision}
                con.execute('COMMIT')
                result = {'token': token, 'callbacks': callbacks[:],
                          'observed': observed, 'metadata_reused': reused}
            elif role == 'reader' and op == 'validate':
                if token is None:
                    raise ValueError('NO_PREPARATION')
                con.execute('BEGIN IMMEDIATE')
                schema = con.execute('PRAGMA slot.schema_version').fetchone()[0]
                current = {table: con.execute(
                    'SELECT revision FROM slot.' + table).fetchone()[0]
                    for table in token['dependencies']}
                reason = 'ACCEPT'
                if schema != token['schema']:
                    reason = 'SCHEMA_CHANGED'
                elif policy == 'BINDING_SCOPED' and generations['slot'] != token['binding']:
                    reason = 'BINDING_CHANGED'
                elif current != token['dependencies']:
                    reason = 'REVISION_CHANGED'
                if reason == 'ACCEPT':
                    con.execute('INSERT INTO effects(value,prepared_binding) VALUES (?,?)',
                                (token['value'], token['binding']))
                con.execute('COMMIT')
                result = {'accepted': reason == 'ACCEPT', 'reason': reason,
                          'schema': schema, 'binding': generations['slot'],
                          'current_revisions': current}
            elif role == 'peer' and op == 'mutate':
                name, table = request['database'], request['table']
                if name not in ('A', 'B', 'U') or table not in TABLES:
                    raise ValueError('UNSUPPORTED_MUTATION')
                db = connect(root / (name + '.db'))
                db.execute('BEGIN IMMEDIATE')
                db.execute('UPDATE ' + table + " SET value=value||'!',revision=revision+1")
                db.execute('COMMIT')
                result = {'database': name, 'table': table, 'row': list(
                    db.execute('SELECT value,revision FROM ' + table).fetchone())}
                db.close()
            elif role == 'peer' and op == 'snapshot':
                result = {}
                for name in ('A', 'B', 'U', 'main'):
                    db = connect(root / (name + '.db'), readonly=True)
                    db.execute('BEGIN')
                    if name == 'main':
                        result[name] = {'effects': db.execute(
                            'SELECT value,prepared_binding FROM effects ORDER BY rowid').fetchall()}
                    else:
                        result[name] = {'schema': db.execute('PRAGMA schema_version').fetchone()[0],
                                        'view': db.execute("SELECT sql FROM sqlite_schema WHERE name='v_dep'").fetchone()[0],
                                        'rows': {t: list(db.execute('SELECT value,revision FROM ' + t).fetchone()) for t in TABLES}}
                    db.execute('COMMIT')
                    db.close()
            else:
                raise ValueError('UNKNOWN_OPERATION')
            reply = {'ok': True, 'result': result}
            print(json.dumps(reply, sort_keys=True), flush=True)
            if op == 'stop':
                break
    finally:
        if con is not None:
            con.close()
        log.close()


if __name__ == '__main__':
    main()
