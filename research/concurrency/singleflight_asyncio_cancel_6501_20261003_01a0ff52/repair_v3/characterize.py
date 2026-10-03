"""Measure old/new auditor decisions on immutable/copied raw; no candidate."""
import hashlib
import importlib.util
import json
from pathlib import Path

from audit_v3 import check
from gate_controls import reordered_gates, serialize
from mutations import mutations


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    root = Path(__file__).resolve().parent
    study = root.parent
    original = (study/'execution/raw.json').read_bytes()
    raw = json.loads(original)
    legacy = load('held_v1', study/'audit.py')
    previous = load('held_v2', study/'repair_v2/audit_v2.py')
    if check(raw):
        raise ValueError('unchanged baseline does not pass')
    out = root/'execution/gate-witnesses'
    out.mkdir(exist_ok=False)
    results = []
    total = 0
    for index, altered in reordered_gates(raw):
        payload = serialize(altered)
        total += len(payload)
        if payload == original or total > 3*1024*1024:
            raise ValueError('ineffective control or copy cap')
        (out/(f'row{index:02}.json')).write_bytes(payload)
        old = legacy.check(altered)
        prior = previous.check(altered)
        new = check(altered)
        if old or prior or not new or not any('requested waiter detach before gate' in e for e in new):
            raise ValueError('gate characterization disagreement: '+str(index))
        results.append({'row': index, 'sha256': hashlib.sha256(payload).hexdigest(),
                        'v1_errors': old, 'v2_errors': prior, 'v3_errors': new})
    if len(results) != 16 or next(x for x in results if x['row'] == 6)['sha256'] != 'f6e789430da805a5a29e9b7ba601e115a0cbaaa53c0dc78afd3c0e39fcfb7f19':
        raise ValueError('exact witness identity/count')
    prior_controls = []
    for name, altered in mutations(raw):
        payload = serialize(altered)
        if payload == original or not check(altered):
            raise ValueError('lost prior refusal: '+name)
        prior_controls.append({'name': name, 'sha256': hashlib.sha256(payload).hexdigest(), 'v3_errors': check(altered)})
    if len(prior_controls) != 25:
        raise ValueError('prior control denominator')
    result = {'classification': 'ordinary copied retained-raw characterization; no original allocation replay',
              'raw_sha256': hashlib.sha256(original).hexdigest(), 'unchanged_v3_errors': [],
              'gate_witnesses': results, 'gate_copy_bytes': total, 'prior_controls': prior_controls,
              'v1_v2_gate_false_accepts': 16, 'v3_rejected': 41, 'original_rows_outcomes': [48,120]}
    (root/'execution/controls.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'old_gate_false_accepts':16,'v3_rejected':41,'copy_bytes':total,'original_errors':0}))


if __name__ == '__main__':
    main()
