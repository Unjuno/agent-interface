"""Read-only independent process; no sink imports and no database writes."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
p = Path(sys.argv[1]).resolve()
before = p.read_bytes(); started = time.monotonic_ns()
db = sqlite3.connect(p.as_uri() + '?mode=ro', uri=True)
db.execute('PRAGMA query_only=ON')
try:
    tables = {}
    for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        if name not in {'document', 'commits', 'seen', 'submissions'}:
            raise ValueError('unexpected table')
        tables[name] = [list(row) for row in db.execute('SELECT * FROM ' + name + ' ORDER BY 1')]
finally:
    db.close()
after = p.read_bytes()
if before != after:
    raise ValueError('read changed bytes')
print(json.dumps({'pid': os.getpid(), 'started_ns': started, 'ended_ns': time.monotonic_ns(),
                  'sha256': hashlib.sha256(before).hexdigest(), 'bytes': len(before),
                  'unchanged': True, 'tables': tables}, sort_keys=True))
