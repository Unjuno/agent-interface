"""Published-byte integrity only, not original producer or auditor replay."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
names = ['current_primary_first_error_57_20261003_01a0ff53',
         'review_current_primary_v2_57_20261003_45e9']
counts = {}
for name in names:
    packet = root / 'research/integration' / name
    rows = json.loads((packet / 'MANIFEST.json').read_bytes())['files']
    for row in rows:
        data = (packet / row['path']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError(name + '/' + row['path'])
    counts[name] = len(rows)
print(json.dumps({'status': 'PASS', 'counts': counts,
                  'scope': 'published bytes only; private originals and historical PID custody not replayed'}, sort_keys=True))
