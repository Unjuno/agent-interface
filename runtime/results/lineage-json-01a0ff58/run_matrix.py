"""Run exact source copies with an inert callback; never opens a backend."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parent


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def main():
    started = datetime.now(timezone.utc).isoformat()
    frozen = json.loads((ROOT / 'freeze.json').read_bytes())
    for name, expected in frozen['hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    cases = json.loads((ROOT / 'corpus.json').read_bytes())
    output = []
    for arm, name in [('baseline', 'baseline.txt'), ('candidate', 'candidate.txt')]:
        namespace = {'__name__': f'frozen_{arm}'}
        exec(compile((ROOT / name).read_bytes(), f'<frozen_{arm}>', 'exec'), namespace)
        for item in cases:
            value = deepcopy(item['input'])
            before = canon(value)
            calls = []
            try:
                result = namespace['dispatch_with_lineage'](
                    value['program'], {}, value['receipt'], value['sidecar'],
                    **value['current'],
                    dispatch_fn=lambda *a, **k: calls.append(1) or {'inert': True})
                observed = {'status': result['status'], 'error': result.get('error')}
            except Exception as error:
                observed = {'status': 'exception', 'error': type(error).__name__}
            output.append({'arm': arm, 'id': item['id'], 'observed': observed,
                           'dispatch_calls': len(calls), 'input_unchanged': before == canon(value),
                           'input_sha256': hashlib.sha256(before.encode()).hexdigest()})
    result = {'schema': 'lineage-json-matrix-v1', 'started_utc': started,
              'ended_utc': datetime.now(timezone.utc).isoformat(),
              'python': sys.version, 'os': platform.platform(),
              'freeze_sha256': hashlib.sha256((ROOT / 'freeze.json').read_bytes()).hexdigest(),
              'rows': output, 'backend_calls': 0}
    (ROOT / 'raw.json').write_text(canon(result) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'rows': len(output), 'arms': 2, 'backend_calls': 0}))


if __name__ == '__main__':
    main()
