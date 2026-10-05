"""Independent RFC grammar/output oracle, importing no runtime/test/probe code."""
import copy
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

ALPHABET = '012-+ _\t٠０'
KINDS = ('event', 'native_single', 'native_multiple')


def output_digest(kind, index):
    if kind == 'event':
        event = {'event': 'released', 'verified': True}
        report = [{'event_ref': 0}, {'event_ref': 0}]
        report[index] = event
        expected = {'schema': 'agent-interface/receipt-view-v1', 'events': [event], 'report': report}
    else:
        observation = {'sequence': 1, 'native': {'title': 'private fixture'}}
        history = [{'observation_ref': '/native_result/observation'}] * 2
        history[index] = observation
        expected = {'native_result': {'observation': observation, 'history': history}}
    return hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def check(raw, source_sha256):
    errors = []
    if raw.get('schema') != 'receipt-pointer-boundary-v1' or raw.get('source_sha256') != source_sha256:
        errors.append('identity')
    expected_ids = [(kind, ''.join(chars)) for size in range(4)
                    for chars in itertools.product(ALPHABET, repeat=size) for kind in KINDS]
    rows = raw.get('rows')
    if not isinstance(rows, list) or len(rows) != len(expected_ids):
        return {'status': 'FAIL_BOUNDARY', 'errors': ['denominator'], 'rows': 0}
    for row, (kind, token) in zip(rows, expected_ids):
        if not isinstance(row, list) or len(row) != 6 or row[:2] != [kind, token]:
            errors.append('row_identity')
            continue
        admissible = re.fullmatch(r'0|[1-9][0-9]*', token) is not None and int(token) < 2
        if row[2] is not admissible or row[4] is not True:
            errors.append('decision_or_input_mutation')
        if admissible:
            if row[3] is not None or row[5] != output_digest(kind, int(token)):
                errors.append('reconstruction')
        elif row[3] != 'ValueError' or row[5] is not None:
            errors.append('refusal_type')
    return {'status': 'PASS_FINITE_POINTER_GRAMMAR' if not errors else 'FAIL_BOUNDARY',
            'rows': len(rows), 'errors': sorted(set(errors))}


def main():
    raw_path, freeze_path, out_path = map(Path, sys.argv[1:])
    data = raw_path.read_bytes()
    raw = json.loads(data)
    freeze = json.loads(freeze_path.read_bytes())
    result = check(raw, freeze['source_sha256'])
    controls = []
    for name in ('omit_row', 'duplicate_row', 'false_admit', 'wrong_output', 'source_drift'):
        changed = copy.deepcopy(raw)
        if name == 'omit_row':
            changed['rows'].pop()
        elif name == 'duplicate_row':
            changed['rows'][1] = copy.deepcopy(changed['rows'][0])
        elif name == 'false_admit':
            changed['rows'][0][2] = True
        elif name == 'wrong_output':
            changed['rows'][3][5] = '0' * 64
        else:
            changed['source_sha256'] = '0' * 64
        control = check(changed, freeze['source_sha256'])
        controls.append({'name': name, 'status': control['status'], 'errors': control['errors']})
    result.update(raw_sha256=hashlib.sha256(data).hexdigest(), corruption_controls=controls)
    passed = result['status'] == 'PASS_FINITE_POINTER_GRAMMAR' and all(c['status'] == 'FAIL_BOUNDARY' for c in controls)
    with out_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(result))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
