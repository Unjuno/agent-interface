"""Read-only integrity checks; not an experiment or original auditor replay."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
review = root / 'research/integration/review_current_primary_57_20261003_45e9'
author = root / 'research/integration/current_primary_57_20261003_01a0ff53'
counts = {}
for row in json.loads((review / 'MANIFEST.json').read_bytes())['files']:
    data = (review / row['path']).read_bytes()
    if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
        raise ValueError(row['path'])
counts['review_manifest'] = len(json.loads((review / 'MANIFEST.json').read_bytes())['files'])
rows = (author / 'SHA256SUMS').read_text().splitlines()
for row in rows:
    digest, name = row.split('  ', 1)
    if hashlib.sha256((author / name).read_bytes()).hexdigest() != digest:
        raise ValueError(name)
counts['author_manifest'] = len(rows)
print(json.dumps({'status': 'PASS', 'counts': counts,
                  'scope': 'saved published bytes only; no runtime, PID or formal replay'}, sort_keys=True))
