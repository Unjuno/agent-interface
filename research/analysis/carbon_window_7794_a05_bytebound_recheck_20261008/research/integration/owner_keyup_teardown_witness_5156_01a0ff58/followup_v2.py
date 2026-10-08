import copy
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from witness_audit import gates

HERE = Path(__file__).resolve().parent


def main():
    freeze = json.loads((HERE / 'FOLLOWUP_FREEZE.json').read_bytes())
    for name, digest in freeze['files'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
            raise ValueError('followup freeze mismatch:' + name)
    out = HERE / 'followup-v2-01'
    out.mkdir(exist_ok=False)
    sys.path.insert(0, str(HERE / 'source_v2'))
    spec = importlib.util.spec_from_file_location('reviewed_v2', HERE / 'source_v2/repair_v2/teardown_audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    previous = json.loads((HERE / 'review-01/probe.json').read_bytes())
    retained = []
    for row in previous['rows']:
        raw = json.loads((HERE / 'review-01' / row['file']).read_bytes())
        errors = module.audit(raw)
        expected_invalid = bool(gates(raw))
        retained.append({'case': row['name'], 'errors': errors,
                         'independent_invalid': expected_invalid,
                         'matches': bool(errors) == expected_invalid})
    original = json.loads((HERE / 'source/retained/raw.json').read_bytes())
    variants = []
    first = copy.deepcopy(original)
    first['cases'][1]['owner_rows_appended'][0]['verified'] = 1
    variants.append(('single_appended_verified_integer', first))
    second = copy.deepcopy(original)
    receipt = original['cases'][8]['receipt']
    projection = {k:v for k,v in receipt.items() if k not in ['release_call_started_ns','release_call_returned_ns']}
    indices = [i for i,v in enumerate(second['owner_snapshots_final']) if v == projection]
    if len(indices) != 1:
        raise ValueError('control final witness is not unique')
    second['owner_snapshots_final'][indices[0]]['verified'] = 1
    variants.append(('cancel_final_verified_integer', second))
    typed = []
    for name, raw in variants:
        data = (json.dumps(raw, sort_keys=True, indent=2) + '\n').encode()
        (out / (name + '.json')).write_bytes(data)
        typed.append({'case': name, 'sha256': hashlib.sha256(data).hexdigest(),
                      'errors': module.audit(raw), 'independent_witnesses': gates(raw)})
    result = {'review_id': freeze['review_id'], 'target_head': freeze['target_head'],
              'finished_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
              'retained_16_rows': retained, 'separate_type_boundary_2_rows': typed,
              'retained_matrix_matches': sum(r['matches'] for r in retained),
              'type_boundary_false_accepts': sum(not r['errors'] and bool(r['independent_witnesses']) for r in typed)}
    (out / 'result.json').write_bytes((json.dumps(result, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({'retained_matches': result['retained_matrix_matches'],
                      'type_boundary_false_accepts': result['type_boundary_false_accepts']}))


if __name__ == '__main__':
    main()
