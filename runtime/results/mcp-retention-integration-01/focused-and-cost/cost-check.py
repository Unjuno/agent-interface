import hashlib
import json
from pathlib import Path
import statistics
import time
from runtime.cli_v1.attempt import _write_json

root = Path('/out')
payload = json.loads(Path('/payload').read_bytes())
data = json.dumps(payload, allow_nan=False).encode('utf-8')
plan = {'scope': 'local filesystem engineering check, not model or GUI timing',
        'pairs': 6, 'payload_sha256': hashlib.sha256(data).hexdigest(),
        'payload_bytes': len(data), 'order': 'alternate direct/atomic then atomic/direct',
        'failures': 'stop on first exception, keep all earlier rows; no retries',
        'adoption': 'no default speed benefit claim; review added storage cost before publication'}
(root/'plan.json').write_text(json.dumps(plan))
rows = []
for pair in range(6):
    for route in (['direct', 'atomic'] if pair % 2 == 0 else ['atomic', 'direct']):
        path = root/f'{pair}-{route}.json'
        started = time.monotonic_ns()
        if route == 'direct':
            path.write_bytes(data)
        else:
            _write_json(path, payload)
        elapsed = time.monotonic_ns()-started
        actual = path.read_bytes()
        assert actual == data
        rows.append({'pair': pair, 'route': route, 'elapsed_ns': elapsed,
                     'sha256': hashlib.sha256(actual).hexdigest()})
        (root/'rows.json').write_text(json.dumps(rows, indent=2))
print(json.dumps({'rows': len(rows), 'median_ms': {
    route: statistics.median(r['elapsed_ns']/1e6 for r in rows if r['route']==route)
    for route in ['direct', 'atomic']}, 'scope': plan['scope']}))
