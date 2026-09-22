"""Resident cooperative SQLite writer/read-only observer; a fresh connection per op."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import time


def operate(path, command):
    observe = command == 'observe'
    db = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro' if observe else path,
                         uri=observe, isolation_level=None, timeout=2)
    try:
        if observe:
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            result = {'tables': {name: list(db.execute(
                f'SELECT value,revision FROM {name}').fetchone()) for name in ('a','b','u')},
                'view_sql': db.execute("SELECT sql FROM sqlite_master WHERE name='current_view'").fetchone()[0],
                'view_value': db.execute('SELECT value FROM current_view').fetchone()[0],
                'schema_version': db.execute('PRAGMA schema_version').fetchone()[0],
                'effects': [list(x) for x in db.execute('SELECT request_id,payload FROM effects ORDER BY request_id')]}
            db.execute('COMMIT')
        else:
            db.execute('BEGIN IMMEDIATE')
            if command == 'retarget_b':
                db.execute('DROP VIEW current_view')
                db.execute('CREATE VIEW current_view AS SELECT value FROM b')
            elif command in ('change_a','change_b','change_u','rollback_a'):
                name = command[-1]
                db.execute(f"UPDATE {name} SET value=value || '+changed', revision=revision+1")
            elif command != 'none':
                raise ValueError('UNKNOWN_FIXTURE_COMMAND')
            db.execute('ROLLBACK' if command == 'rollback_a' else 'COMMIT')
            result = {'operation': command}
        return result
    finally:
        db.close()


def main():
    path = sys.argv[1]
    for line in sys.stdin:
        request=json.loads(line)
        start=time.monotonic_ns()
        command=request['command']
        result={'status':'BYE'} if command=='stop' else operate(path,command)
        print(json.dumps({'pid':os.getpid(),'op_id':request['op_id'],'command':command,
                          'started_ns':start,'finished_ns':time.monotonic_ns(),
                          'result':result},sort_keys=True),flush=True)
        if command=='stop':return
    raise RuntimeError('PEER_MISSING_STOP')

if __name__=='__main__':main()
