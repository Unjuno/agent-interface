"""Raw-only reference audit. Does not import runtime or candidate tests."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FLOOR = ['capture.frame', 'clock.monotonic', 'display.geometry', 'event.feedback',
         'input.keyboard', 'input.pointer', 'input.release_all', 'input.scroll',
         'input.text', 'window.focus']


def expected(manifest, before):
    os_name = manifest['platform']['os']
    state = manifest['capabilities']['input.release_all']['state']
    frames = manifest['coordinate_frames']
    os_ok = type(os_name) is str and os_name in ('linux', 'windows', 'macos')
    state_ok = type(state) is str and state in ('supported', 'unsupported', 'unknown', 'permission_required')
    frames_ok = (type(frames) is list and len(frames) > 0
                 and all(type(frame) is str and frame in
                         ('screen_physical_px', 'screen_logical', 'window_client') for frame in frames)
                 and len(frames) == len(set(frames)))
    valid = os_ok and state_ok and frames_ok
    unhashable = (isinstance(os_name, (list, dict))
                  or (os_ok and isinstance(state, (list, dict)))
                  or (os_ok and state_ok and type(frames) is list and len(frames) > 0
                      and any(isinstance(frame, (list, dict)) for frame in frames)))
    if before and unhashable:
        return {label: {'exception': 'TypeError'} for label in ('validate', 'admit', 'readiness')}
    if not valid:
        return {'validate': {'exception': 'ContractError'},
                'admit': {'accepted': False, 'error': 'INVALID_PROGRAM', 'required': []},
                'readiness': {'exception': 'ContractError'}}
    error = (None if state == 'supported' else 'PERMISSION_DENIED'
             if state == 'permission_required' else 'UNSUPPORTED_CAPABILITY')
    states = {key: state if key == 'input.release_all' else 'unknown' for key in FLOOR}
    return {'validate': {'valid': True},
            'admit': {'accepted': error is None, 'error': error, 'required': ['input.release_all']},
            'readiness': {'ready': False, 'blocking_capabilities': [key for key in FLOOR if states[key] != 'supported'],
                          'states': states}}


def verify(raw, fixtures, before, source_sha):
    errors = []
    if raw.get('schema') != 'manifest-enum-regression-v1':
        errors.append('schema')
    if raw.get('backend_opened') is not False or raw.get('input_dispatched') is not False:
        errors.append('side_effect_declaration')
    if raw.get('source_sha256') != source_sha:
        errors.append('source_identity')
    if raw.get('fixtures_sha256') != hashlib.sha256((HERE / 'fixtures.json').read_bytes()).hexdigest():
        errors.append('fixture_identity')
    rows = raw.get('rows')
    if type(rows) is not list or len(rows) != len(fixtures['cases']):
        return errors + ['denominator']
    for row, case in zip(rows, fixtures['cases']):
        name = case['id']
        if row.get('id') != name or row.get('manifest') != case['manifest']:
            errors.append('case_identity:' + name)
        if row.get('unchanged') is not True:
            errors.append('mutation:' + name)
        for label, value in expected(case['manifest'], before).items():
            if row.get(label) != value:
                errors.append(label + ':' + name)
    return errors


if __name__ == '__main__':
    fixtures = json.loads((HERE / 'fixtures.json').read_text(encoding='utf-8'))
    identity = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
    if hashlib.sha256((HERE / 'fixtures.json').read_bytes()).hexdigest() != identity['fixtures_sha256']:
        raise SystemExit('frozen fixture identity mismatch')
    results = {}
    for stage in ('before', 'after'):
        raw = json.loads((HERE / (stage + '.json')).read_text(encoding='utf-8'))
        errors = verify(raw, fixtures, stage == 'before', identity[stage + '_source_sha256'])
        results[stage] = {'rows': len(raw['rows']), 'errors': errors,
                          'type_error_rows': sum(row['validate'] == {'exception': 'TypeError'} for row in raw['rows'])}
    raw = json.loads((HERE / 'after.json').read_text(encoding='utf-8'))
    controls = []
    for mutation in ('omitted_row', 'duplicate_id', 'input_changed', 'input_mutated',
                     'accepted_invalid', 'escaped_type_error', 'source_identity',
                     'fixture_identity', 'permission_promoted', 'side_effects'):
        copy = deepcopy(raw)
        if mutation == 'omitted_row':
            copy['rows'].pop()
        elif mutation == 'duplicate_id':
            copy['rows'][1]['id'] = copy['rows'][0]['id']
        elif mutation == 'input_changed':
            copy['rows'][0]['manifest']['platform']['os'] = 'linux'
        elif mutation == 'input_mutated':
            copy['rows'][0]['unchanged'] = False
        elif mutation == 'accepted_invalid':
            copy['rows'][0]['admit'] = {'accepted': True, 'error': None, 'required': []}
        elif mutation == 'escaped_type_error':
            copy['rows'][0]['validate'] = {'exception': 'TypeError'}
        elif mutation == 'source_identity':
            copy['source_sha256'] = '0' * 64
        elif mutation == 'fixture_identity':
            copy['fixtures_sha256'] = '0' * 64
        elif mutation == 'permission_promoted':
            row = next(row for row in copy['rows'] if row['id'] == 'valid-linux-screen_physical_px-permission_required')
            row['admit'] = {'accepted': True, 'error': None, 'required': ['input.release_all']}
        else:
            copy['input_dispatched'] = True
        errors = verify(copy, fixtures, False, identity['after_source_sha256'])
        controls.append({'mutation': mutation, 'rejected': bool(errors), 'errors': errors})
    ok = all(not value['errors'] for value in results.values()) and all(c['rejected'] for c in controls)
    result = {'status': 'PASS_JSON_MANIFEST_BOUNDARY_SCOPED' if ok else 'FAIL_AUDIT',
              'stages': results, 'corruption_controls': controls,
              'independent_implementation': True, 'external_non_author_review': False}
    with Path(sys.argv[1]).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(result))
    raise SystemExit(0 if ok else 1)
