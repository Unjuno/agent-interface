"""One fresh real SQLite sink process per case; no GUI or production endpoint."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import legacy_sink
import candidate


def tables(db):
    names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return {name: [list(r) for r in db.execute('SELECT * FROM ' + name + ' ORDER BY 1')]
            for name in sorted(names)}


def main():
    p = argparse.ArgumentParser(); p.add_argument('--db', type=Path, required=True); p.add_argument('--sql', type=Path, required=True)
    a = p.parse_args()
    if a.db.exists() or a.sql.exists():
        p.error('fresh paths required')
    raw = sys.stdin.read(); packet = json.loads(raw)
    trace = a.sql.open('x', encoding='utf-8')
    store = candidate.Store(a.db, packet['session']) if packet['policy'] == 'SUBMIT_EVENT' else legacy_sink.Store(a.db, packet['session'], 'REVISION_FENCE')
    def sql(s):
        trace.write(json.dumps(s) + '\n'); trace.flush()
    store.db.set_trace_callback(sql)
    result = {'pid': os.getpid(), 'started_ns': time.monotonic_ns(),
              'packet_sha256': hashlib.sha256(raw.encode()).hexdigest(), 'initial': tables(store.db), 'steps': []}
    try:
        for request in packet['requests']:
            result['steps'].append({'request': request, 'result': store.apply(request), 'tables': tables(store.db)})
        result['final'] = tables(store.db)
        result['pragmas'] = {'journal_mode': store.db.execute('PRAGMA journal_mode').fetchone()[0],
                             'synchronous': store.db.execute('PRAGMA synchronous').fetchone()[0]}
        result['ended_ns'] = time.monotonic_ns()
    finally:
        store.close(); trace.close()
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
