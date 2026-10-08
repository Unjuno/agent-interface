"""Separate raw-only oracle; imports neither candidate nor production code."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def serialized(value):
    return json.dumps(value, separators=(',', ':'), sort_keys=True, allow_nan=False).encode()


def typed_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def oracle(value):
    p, r, s, current = (value[k] for k in ('program', 'receipt', 'sidecar', 'current'))
    receipt_fields = {k: r[k] for k in ('receipt_id', 'role', 'currentness', 'point',
                      'observation_seq', 'binding_revision', 'source_receipt_id')}
    sidecar_fields = {k: s[k] for k in ('program_digest', 'evidence_receipt_digest',
                      'role', 'currentness', 'point', 'observation_seq', 'binding_revision')}
    hash_of = lambda v: hashlib.sha256(serialized(v)).hexdigest()
    if r['digest'] != hash_of(receipt_fields):
        return 'EVIDENCE_RECEIPT_DIGEST_MISMATCH'
    if s['digest'] != hash_of(sidecar_fields):
        return 'SIDECAR_DIGEST_MISMATCH'
    if s['program_digest'] != hash_of(p):
        return 'PROGRAM_DIGEST_MISMATCH'
    if s['evidence_receipt_digest'] != r['digest']:
        return 'EVIDENCE_DIGEST_MISMATCH'
    if any(not typed_equal(s[k], r[k]) for k in ('role', 'currentness', 'point',
                                                'observation_seq', 'binding_revision')):
        return 'SIDECAR_RECEIPT_MISMATCH'
    if r['role'] != 'ADMISSION_DEPENDENCY' or r['currentness'] != 'CURRENT':
        return 'LINEAGE_NOT_CURRENT_ADMISSION'
    if not typed_equal(r['observation_seq'], current['current_observation_seq']):
        return 'STALE_OBSERVATION'
    if not typed_equal(r['binding_revision'], current['current_binding_revision']):
        return 'STALE_BINDING'
    if not typed_equal(p['source'], {k: r[k] for k in ('observation_seq', 'binding_revision')}):
        return 'PROGRAM_SOURCE_MISMATCH'
    if not typed_equal([p['ops'][0]['x'], p['ops'][0]['y']], r['point']):
        return 'PROGRAM_POINT_MISMATCH'
    return None


def inspect(raw, cases, frozen):
    assert raw['schema'] == 'lineage-json-matrix-v1'
    assert raw['freeze_sha256'] == hashlib.sha256((ROOT / 'freeze.json').read_bytes()).hexdigest()
    assert type(raw['backend_calls']) is int and raw['backend_calls'] == 0
    assert len(cases) == frozen['case_count'] == 116
    expected = {(arm, c['id']): c['input'] for arm in ('baseline', 'candidate') for c in cases}
    seen = set()
    mismatches = {'baseline': [], 'candidate': []}
    for row in raw['rows']:
        key = row['arm'], row['id']
        assert key in expected and key not in seen
        seen.add(key)
        value = expected[key]
        assert row['input_sha256'] == hashlib.sha256(serialized(value)).hexdigest()
        assert row['input_unchanged'] is True
        assert type(row['dispatch_calls']) is int
        error = oracle(value)
        wanted = {'status': 'lineage_rejected' if error else 'delegated', 'error': error}
        actual = row['observed']
        assert row['dispatch_calls'] == (1 if actual['status'] == 'delegated' else 0)
        if actual != wanted:
            mismatches[row['arm']].append(row['id'])
    assert seen == set(expected)
    assert mismatches['baseline'], 'baseline must expose the reproduced identity gap'
    assert not mismatches['candidate'], mismatches['candidate']
    return mismatches


def main():
    frozen = json.loads((ROOT / 'freeze.json').read_bytes())
    for name, expected_hash in frozen['hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected_hash, name
    cases = json.loads((ROOT / 'corpus.json').read_bytes())
    raw = json.loads((ROOT / 'raw.json').read_bytes())
    mismatches = inspect(raw, cases, frozen)
    controls = []
    for kind in ('drop', 'duplicate', 'bad-hash', 'dispatch-count', 'mutation', 'wrong-verdict'):
        altered = deepcopy(raw)
        if kind == 'drop':
            altered['rows'].pop()
        elif kind == 'duplicate':
            altered['rows'].append(deepcopy(altered['rows'][0]))
        elif kind == 'bad-hash':
            altered['rows'][0]['input_sha256'] = '0' * 64
        elif kind == 'dispatch-count':
            altered['rows'][0]['dispatch_calls'] = True
        elif kind == 'mutation':
            altered['rows'][0]['input_unchanged'] = False
        else:
            altered['rows'][-1]['observed'] = {'status': 'delegated', 'error': None}
            altered['rows'][-1]['dispatch_calls'] = 1
        try:
            inspect(altered, cases, frozen)
        except AssertionError:
            controls.append({'control': kind, 'rejected': True})
        else:
            raise AssertionError(f'false accept: {kind}')
    report = {'status': 'PASS_JSON_IDENTITY_SCOPED', 'case_count': len(cases),
              'baseline_mismatches': len(mismatches['baseline']), 'candidate_mismatches': 0,
              'mismatch_ids': mismatches['baseline'], 'corruption_controls': controls,
              'raw_sha256': hashlib.sha256((ROOT / 'raw.json').read_bytes()).hexdigest()}
    (ROOT / 'audit.json').write_bytes(serialized(report) + b'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'mismatch_ids'}, sort_keys=True))


if __name__ == '__main__':
    main()
