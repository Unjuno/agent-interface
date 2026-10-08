"""Input-free ordinary regression matrix; output is exclusive-create."""
import hashlib
import json
from pathlib import Path
import platform
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from runtime.core_v1 import contract as c


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(fixtures):
    rows = []
    for case in fixtures['cases']:
        manifest = case['manifest']
        initial = json.dumps(manifest, sort_keys=True)
        result = {'id': case['id'], 'manifest': manifest}
        for label, call in (
            ('validate', lambda: c.validate_backend_manifest(manifest)),
            ('admit', lambda: c.admit_program(fixtures['program'], manifest, now_ns=1,
                                            current_observation_seq=1, current_binding_revision=1)),
            ('readiness', lambda: c.office_readiness(manifest)),
        ):
            try:
                value = call()
                if label == 'admit':
                    result[label] = {'accepted': value.accepted, 'error': value.error,
                                     'required': list(value.required_capabilities)}
                elif label == 'readiness':
                    result[label] = value
                else:
                    result[label] = {'valid': True}
            except Exception as error:
                result[label] = {'exception': type(error).__name__}
        result['unchanged'] = initial == json.dumps(manifest, sort_keys=True)
        rows.append(result)
    return rows


if __name__ == '__main__':
    fixture_path = Path(__file__).with_name('fixtures.json')
    output = Path(sys.argv[1])
    started = datetime.now(timezone.utc).isoformat()
    rows = run(json.loads(fixture_path.read_text(encoding='utf-8')))
    record = {'schema': 'manifest-enum-regression-v1', 'python': platform.python_version(),
              'platform': platform.platform(), 'started_utc': started,
              'ended_utc': datetime.now(timezone.utc).isoformat(),
              'source_sha256': sha(ROOT / 'runtime/core_v1/contract.py'),
              'fixtures_sha256': sha(fixture_path), 'rows': rows,
              'backend_opened': False, 'input_dispatched': False}
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'rows': len(rows), 'output_sha256': sha(output)}))
