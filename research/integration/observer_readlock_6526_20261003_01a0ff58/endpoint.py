"""Fresh process scorer: read an already closed DB, with no producer import."""
import argparse
import json
import os
from pathlib import Path
import sqlite3


def score(path):
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=0)
    trace = []
    conn.set_trace_callback(trace.append)
    try:
        conn.execute('PRAGMA query_only=ON').close()
        query_only = conn.execute('PRAGMA query_only').fetchone()[0]
        rows = conn.execute('SELECT task_id, value, revision FROM task ORDER BY task_id').fetchall()
        result = {'pid': os.getpid(), 'rows': rows, 'query_only': query_only,
                  'total_changes': conn.total_changes, 'in_transaction': conn.in_transaction,
                  'sqlite_version': sqlite3.sqlite_version, 'uri_mode': 'ro'}
    finally:
        conn.close()
    result['closed'] = True
    result['sql_trace'] = trace
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('db')
    args = parser.parse_args()
    print(json.dumps(score(args.db), ensure_ascii=False, sort_keys=True))
