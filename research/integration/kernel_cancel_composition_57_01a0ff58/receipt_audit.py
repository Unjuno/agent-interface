"""Read-only join of frozen source, per-child outputs and aggregate raw."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit():
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    errors = []
    for name, digest in freeze['files'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
            errors.append('source freeze:' + name)
    run = json.loads((HERE / 'run-01/RUN.json').read_bytes())
    raw = json.loads((HERE / 'run-01/raw.json').read_bytes())
    ids = sorted(freeze['arms'])
    if run['study'] != freeze['study'] or [r['arm'] for r in run['children']] != ids:
        errors.append('receipt census/identity')
    if type(run['backend_input_model_container_gpu_invocations']) is not int or run['backend_input_model_container_gpu_invocations'] != 0:
        errors.append('scope counter')
    prior = datetime.fromisoformat(freeze['frozen_utc'])
    for receipt, arm in zip(run['children'], raw['arms']):
        name = receipt['arm']
        start, finish = (datetime.fromisoformat(receipt[k]) for k in ('started_utc', 'finished_utc'))
        if not prior <= start <= finish:
            errors.append('UTC sequence:' + name)
        prior = finish
        if type(receipt['exit']) is not int or receipt['exit'] != 0 or receipt['command'] != ['python', '-I', '-B', 'child_arm.py', name]:
            errors.append('command/exit:' + name)
        for stream in ('stdout', 'stderr'):
            data = (HERE / 'run-01' / (name + ('.stdout.json' if stream == 'stdout' else '.stderr.txt'))).read_bytes()
            if hashlib.sha256(data).hexdigest() != receipt[stream + '_sha256']:
                errors.append('stream hash:' + name + ':' + stream)
            if stream == 'stdout':
                expected = {k: v for k, v in arm.items() if k != 'source_sha256'}
                if json.dumps(json.loads(data), sort_keys=True) != json.dumps(expected, sort_keys=True):
                    errors.append('raw/child join:' + name)
            elif data:
                errors.append('unexpected stderr:' + name)
    if len(run['children']) != len(raw['arms']) or len(raw['arms']) != 8:
        errors.append('complete census')
    return errors


if __name__ == '__main__':
    errors = audit()
    result = {'errors': errors, 'status': 'PASS_FROZEN_SOURCE_CHILD_RAW_JOIN' if not errors else 'HOLD'}
    with (HERE / 'run-01/receipt-audit.json').open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(bool(errors))
