"""Ordinary reviewer construction: immutable A18 raw, no backend invocation."""
import copy
import hashlib
import importlib.util
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'source'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    for name, digest in freeze['files'].items():
        if sha(HERE / name) != digest:
            raise ValueError('freeze mismatch:' + name)
    out = HERE / 'review-01'
    out.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    spec = importlib.util.spec_from_file_location('pr6865_supplement', SOURCE / 'boundary_audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = json.loads((SOURCE / 'retained/raw.json').read_bytes())
    variants = [('control', original, None, None)]
    for index in (1, 5):
        label = original['cases'][index]['case']
        for field, value in [('owner_id', 'f' * 32), ('intent_token', 'foreign-review-intent'),
                             ('verified_ns', original['cases'][index]['owner_rows_appended'][0]['verified_ns'] + 1)]:
            raw = copy.deepcopy(original)
            raw['cases'][index]['owner_rows_appended'][0][field] = value
            variants.append((label + '_appended_' + field, raw,
                             ['cases', index, 'owner_rows_appended', 0, field], value))
    for index in (1, 5, 8):
        label = original['cases'][index]['case']
        receipt = original['cases'][index]['receipt']
        for kind, value in [('before_caller', receipt['release_call_started_ns'] - 1),
                            ('after_caller', receipt['release_call_returned_ns'] + 1),
                            ('different_witness_time', receipt['verified_ns'] + 1)]:
            raw = copy.deepcopy(original)
            raw['cases'][index]['receipt']['verified_ns'] = value
            variants.append((label + '_' + kind, raw,
                             ['cases', index, 'receipt', 'verified_ns'], value))
    rows = []
    for name, raw, pointer, value in variants:
        target = out / (name + '.json')
        target.write_bytes((json.dumps(raw, indent=2, sort_keys=True) + '\n').encode())
        result = {}
        for mode, function in [('legacy', module.legacy.audit), ('supplement', module.audit)]:
            try:
                result[mode] = {'errors': function(raw), 'exception': None}
            except Exception as exc:
                result[mode] = {'errors': None, 'exception': type(exc).__name__ + ':' + str(exc)}
        rows.append({'name': name, 'file': target.name, 'sha256': sha(target),
                     'mutation_path': pointer, 'mutation_value': value, **result})
    report = {'review_id': freeze['review_id'], 'target_head': freeze['target_head'],
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
              'pid': os.getpid(), 'python': sys.version, 'platform': platform.platform(),
              'original_raw_sha256': sha(SOURCE / 'retained/raw.json'), 'rows': rows,
              'scope': 'private copied-raw engineering review; no A18/C01 candidate, backend or formal rerun'}
    (out / 'probe.json').write_bytes((json.dumps(report, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({'rows': len(rows), 'supplement_accepted': sum(not r['supplement']['errors'] and
                      r['supplement']['exception'] is None for r in rows), 'review_id': freeze['review_id']}))


if __name__ == '__main__':
    main()
