"""Actual frozen decoder with inert JSON only; no backend or oracle import."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def main():
    root = Path(__file__).parent
    raw_path = root / 'raw.json'
    if raw_path.exists():
        raise SystemExit('original raw path already exists')
    freeze = json.loads((root / 'FREEZE.json').read_text())
    for name, digest in freeze['hashes'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('frozen file mismatch: ' + name)
    cases = json.loads((root / 'fixtures.json').read_text())
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    for arm in ('baseline', 'fixed'):
        namespace = {'__name__': 'frozen_marker_' + arm}
        source = (root / (arm + '.py.txt')).read_bytes()
        exec(compile(source, '<frozen_marker_' + arm + '>', 'exec'), namespace)
        for case in cases:
            value = deepcopy(case['input'])
            before = encoded(value)
            try:
                received = namespace['compact_receipt'](value) if case['mode'] == 'roundtrip' else value
                result = namespace['expand_receipt'](received)
                observed = {'status': 'returned', 'result': result}
            except Exception as error:
                observed = {'status': 'error', 'exception': type(error).__name__, 'message': str(error)}
            rows.append({'arm': arm, 'id': case['id'], 'input_sha256': hashlib.sha256(before).hexdigest(),
                         'input_unchanged': before == encoded(value), 'observed': observed})
    raw = {'schema': 'event-marker-json-v3', 'started_utc': started,
           'ended_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
           'platform': platform.platform(), 'freeze_sha256': hashlib.sha256((root / 'FREEZE.json').read_bytes()).hexdigest(),
           'source_sha256': freeze['sources'], 'rows': rows}
    raw_path.write_bytes(encoded(raw) + b'\n')
    print(json.dumps({'rows': len(rows), 'cases_per_arm': len(cases), 'backend_calls': 0}))


if __name__ == '__main__':
    main()
