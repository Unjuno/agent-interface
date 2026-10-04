"""Ordinary input-free regression; each output is created once."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549'

if __name__ == '__main__':
    stage, output = sys.argv[1], Path(sys.argv[2])
    if stage not in ('before', 'fixed'):
        raise SystemExit('stage must be before or fixed')
    source = (subprocess.check_output(['git', 'show', BASE + ':runtime/core_v1/contract.py'], cwd=ROOT)
              if stage == 'before' else (ROOT / 'runtime/core_v1/contract.py').read_bytes())
    module = types.ModuleType('frozen_contract_' + stage)
    sys.modules[module.__name__] = module
    exec(compile(source, 'frozen_contract.py', 'exec'), module.__dict__)
    fixture_bytes = (HERE / 'fixtures.json').read_bytes()
    fixtures = json.loads(fixture_bytes)
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    for case in fixtures['cases']:
        program, manifest, context = (copy.deepcopy(fixtures['program']),
            copy.deepcopy(fixtures['manifest']), copy.deepcopy(case['context']))
        initial = json.dumps([program, manifest, context], sort_keys=True, allow_nan=False)
        try:
            value = module.admit_program(program, manifest, **context)
            result = {'accepted': value.accepted, 'error': value.error, 'required': list(value.required_capabilities)}
        except Exception as error:
            result = {'exception': type(error).__name__}
        rows.append({'id': case['id'], 'context': context, 'result': result,
                     'unchanged': initial == json.dumps([program, manifest, context], sort_keys=True, allow_nan=False)})
    record = {'schema': 'admission-context-regression-v1', 'stage': stage, 'base': BASE,
              'python': platform.python_version(), 'source_sha256': hashlib.sha256(source).hexdigest(),
              'fixtures_sha256': hashlib.sha256(fixture_bytes).hexdigest(), 'started_utc': started,
              'ended_utc': datetime.now(timezone.utc).isoformat(),
              'backend_opened': False, 'input_dispatched': False, 'rows': rows}
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'stage': stage, 'rows': len(rows), 'source_sha256': record['source_sha256'],
                      'raw_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
