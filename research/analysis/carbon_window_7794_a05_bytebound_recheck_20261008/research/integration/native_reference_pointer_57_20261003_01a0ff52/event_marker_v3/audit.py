"""Raw-only type oracle, independent of decoder/runner; explicit check errors."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def demand(condition, error):
    if not condition:
        raise ValueError(error)


def expected(case):
    value = deepcopy(case['input'])
    if case['mode'] == 'roundtrip':
        return {'status': 'returned', 'result': value}
    if case['mode'] == 'decode':
        path, number = next(iter(value['event_references'].items()))
        marker = value['report'] if path == '/report' else value['report']['value']
        # Finite corpus has known locations. Reference identity is an exact
        # integer/type condition, not Python dictionary value equality.
        valid = (type(marker) is dict and set(marker) == {'event_ref'}
                 and type(marker['event_ref']) is int and marker['event_ref'] == number)
        if not valid:
            return {'status': 'error', 'exception': 'ValueError', 'message': 'event reference marker mismatch'}
        event = deepcopy(value['events'][number])
        if path == '/report':
            value['report'] = event
        else:
            value['report']['value'] = event
    value['schema'] = 'agent-interface/receipt-view-v1'
    value.pop('event_references')
    value.pop('reference_scope')
    return {'status': 'returned', 'result': value}


def inspect(raw, cases, freeze, freeze_bytes):
    demand(raw['schema'] == 'event-marker-json-v3', 'schema')
    demand(raw['freeze_sha256'] == hashlib.sha256(freeze_bytes).hexdigest(), 'freeze_identity')
    demand(encoded(raw['source_sha256']) == encoded(freeze['sources']), 'source_identity')
    demand(len(cases) == freeze['case_count'] == 72, 'case_denominator')
    table = {case['id']: case for case in cases}
    demand(len(table) == len(cases), 'fixture_duplicate')
    wanted = {(arm, name) for arm in ('baseline', 'fixed') for name in table}
    seen, mismatch = set(), {'baseline': [], 'fixed': []}
    for row in raw['rows']:
        key = row['arm'], row['id']
        demand(key in wanted and key not in seen, 'row_coverage')
        seen.add(key)
        case = table[row['id']]
        demand(row['input_sha256'] == hashlib.sha256(encoded(case['input'])).hexdigest(), 'input_identity')
        demand(row['input_unchanged'] is True, 'input_mutation')
        if encoded(row['observed']) != encoded(expected(case)):
            mismatch[row['arm']].append(row['id'])
    demand(seen == wanted, 'missing_row')
    demand(bool(mismatch['baseline']), 'nondiscriminating_baseline')
    demand(not mismatch['fixed'], 'fixed_contract_mismatch')
    return {'status': 'PASS_EVENT_MARKER_IDENTITY_SCOPED', 'rows': len(raw['rows']),
            'cases_per_arm': len(cases), 'baseline_mismatches': mismatch['baseline'],
            'fixed_mismatches': mismatch['fixed'],
            'valid_controls_per_arm': sum(expected(c)['status'] == 'returned' for c in cases)}


def main():
    root = Path(__file__).parent
    freeze_bytes = (root / 'FREEZE.json').read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, digest in freeze['hashes'].items():
        demand(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, 'frozen_file:' + name)
    result = inspect(json.loads((root / 'raw.json').read_bytes()),
                     json.loads((root / 'fixtures.json').read_bytes()), freeze, freeze_bytes)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
