"""Independent exact raw joins; imports no tested validator or probe module."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def exact(left, right):
    return json.dumps(left, sort_keys=True, separators=(',', ':')) == json.dumps(right, sort_keys=True, separators=(',', ':'))


def gates(raw):
    errors = []
    for index in (1, 5, 8):
        case = raw['cases'][index]
        receipt = case['receipt']
        label = case['case']
        t = receipt['verified_ns']
        if type(t) is not int or not receipt['release_call_started_ns'] <= t <= receipt['release_call_returned_ns']:
            errors.append(label + ':verification_not_nested')
        projection = {key: value for key, value in receipt.items()
                      if key not in ('release_call_started_ns', 'release_call_returned_ns')}
        if not any(exact(projection, record) for record in raw['owner_snapshots_final']):
            errors.append(label + ':receipt_not_joined_to_final_owner_snapshot')
        if index in (1, 5) and not exact(case['owner_rows_appended'], [projection]):
            errors.append(label + ':appended_witness_differs_from_receipt')
    return errors


def leaves_changed(left, right, path=()):
    if type(left) is dict and type(right) is dict and set(left) == set(right):
        return [delta for key in left for delta in leaves_changed(left[key], right[key], path + (key,))]
    if type(left) is list and type(right) is list and len(left) == len(right):
        return [delta for i, (a, b) in enumerate(zip(left, right)) for delta in leaves_changed(a, b, path + (i,))]
    return [] if exact(left, right) else [list(path)]


def audit(out):
    report = json.loads((out / 'probe.json').read_bytes())
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    original = json.loads((HERE / 'source/retained/raw.json').read_bytes())
    issues = []
    if report['review_id'] != freeze['review_id'] or report['target_head'] != freeze['target_head']:
        issues.append('review identity')
    expected = ['control']
    for label in ('single', 'two_key'):
        expected.extend(label + '_appended_' + field for field in ('owner_id', 'intent_token', 'verified_ns'))
    for label in ('single', 'two_key', 'cancel'):
        expected.extend(label + '_' + kind for kind in ('before_caller', 'after_caller', 'different_witness_time'))
    if [row['name'] for row in report['rows']] != expected:
        issues.append('complete ordered census')
    contradictions = []
    for row in report['rows']:
        data = (out / row['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            issues.append('hash:' + row['name'])
        raw = json.loads(data)
        delta = leaves_changed(original, raw)
        if row['name'] == 'control':
            if delta or gates(raw) or row['supplement'] != {'errors': [], 'exception': None}:
                issues.append('unchanged positive')
        else:
            if delta != [row['mutation_path']] or not gates(raw):
                issues.append('mutation/witness:' + row['name'])
            selected = raw
            for part in row['mutation_path']:
                selected = selected[part]
            if not exact(selected, row['mutation_value']):
                issues.append('mutation value:' + row['name'])
            if row['supplement'] == {'errors': [], 'exception': None}:
                contradictions.append({'name': row['name'], 'witnesses': gates(raw)})
    return {'status': 'PASS_INDEPENDENT_REVIEW_RECONSTRUCTION_SCOPED' if not issues else 'FAIL',
            'review_id': freeze['review_id'], 'errors': issues, 'rows': len(report['rows']),
            'contradictory_rows_accepted_by_supplement': contradictions,
            'scope': 'fixed A18 teardown exact consistency only; no physical release or live raw fabrication claim'}


if __name__ == '__main__':
    out = Path(sys.argv[1])
    result = audit(out)
    (out / 'witness-audit.json').write_bytes((json.dumps(result, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({'status': result['status'], 'rows': result['rows'], 'errors': result['errors'],
                      'contradictory_accepts': len(result['contradictory_rows_accepted_by_supplement'])}))
    raise SystemExit(bool(result['errors']))
