"""Independent finite trace reconstruction; imports no producer or kernel."""
import copy
import json
from pathlib import Path
import sys

BASE = '2c0c1183b861519fde7c71462a589fb904c3451e'
ARMS = ('baseline', 'observation_floor', 'authorization_floor')
GRANTS = (200, 400)
TIMES = (0, 99, 100, 199, 200, 300, 399, 400, 1000)
H = 'a' * 64
ROW_KEYS = {'arm', 'grant_ns', 'begin_ns', 'request_matches', 'before', 'accepted',
            'after', 'error_type', 'error_message', 'request_identity', 'unchanged_on_refusal'}


def same_json(left, right):
    return json.dumps(left, sort_keys=True, separators=(',', ':')) == json.dumps(right, sort_keys=True, separators=(',', ':'))


def state_before(arm, grant):
    state = {'stage': 'authorized',
             'observation': {'sequence': 7, 'captured_ns': 100, 'surface_id': 'clock-surface',
                             'payload_sha256': H, 'width': 10, 'height': 10, 'encoding': 'rgb'},
             'binding': {'target_id': 'clock-target', 'observation_sequence': 7,
                         'surface_id': 'clock-surface', 'binding_digest': H},
             'lease': {'lease_id': 'clock-lease', 'observation_sequence': 7,
                       'surface_id': 'clock-surface', 'valid_until_ns': 1000, 'allowed_actions': ['pointer']},
             'request': None, 'execution': None, 'effect': None, 'stop_reason': None,
             'execution_started_ns': None}
    if arm == 'authorization_floor':
        state['authorized_ns'] = grant
    return state


def state_after(before, begin):
    after = copy.deepcopy(before)
    after['execution_started_ns'] = begin
    after['request'] = {'command_id': 'clock-command', 'invariant_manifest_id': H,
                        'binding': copy.deepcopy(before['binding']), 'lease': copy.deepcopy(before['lease']),
                        'actions': [{'action_id': 'clock-action', 'kind': 'pointer', 'operation': 'click'}]}
    return after


def audit(record):
    errors = []
    if type(record) is not dict or set(record) != {'schema', 'source_base', 'rows'}:
        return {'decision': 'HOLD_ORDER_EVIDENCE', 'errors': ['record_shape']}
    if record['schema'] != 'authority-begin-order-v1' or record['source_base'] != BASE:
        errors.append('schema_or_source')
    rows = record['rows']
    if type(rows) is not list or len(rows) != 108:
        return {'decision': 'HOLD_ORDER_EVIDENCE', 'errors': errors + ['row_count']}
    expected_order = [(a, g, t, m) for a in ARMS for g in GRANTS for t in TIMES for m in (True, False)]
    observed_order = []
    seen = set()
    accepted_counts = {arm: 0 for arm in ARMS}
    stale_counts = {arm: 0 for arm in ARMS}
    witnesses = {}
    for index, row in enumerate(rows):
        if type(row) is not dict or set(row) != ROW_KEYS:
            errors.append(f'{index}:row_shape'); continue
        arm, grant, begin, matches = (row[k] for k in ('arm', 'grant_ns', 'begin_ns', 'request_matches'))
        if type(arm) is not str or arm not in ARMS or type(grant) is not int or grant not in GRANTS or type(begin) is not int or begin not in TIMES or type(matches) is not bool:
            errors.append(f'{index}:identity_type'); continue
        identity = (arm, grant, begin, matches)
        if identity in seen:
            errors.append(f'{index}:duplicate')
        seen.add(identity)
        observed_order.append(identity)
        expected = matches and begin < 1000
        if arm == 'observation_floor':
            expected = expected and begin >= 100
        if arm == 'authorization_floor':
            expected = expected and begin >= grant
        before = state_before(arm, grant)
        after = state_after(before, begin) if expected else before
        if type(row['accepted']) is not bool or row['accepted'] is not expected:
            errors.append(f'{index}:acceptance')
        if not same_json(row['before'], before) or not same_json(row['after'], after):
            errors.append(f'{index}:complete_state')
        if row['request_identity'] is not True:
            errors.append(f'{index}:request_identity')
        if expected:
            if row['unchanged_on_refusal'] is not None or row['error_type'] is not None or row['error_message'] is not None:
                errors.append(f'{index}:accepted_evidence')
        elif row['unchanged_on_refusal'] is not True or row['error_type'] != 'ContractError' or type(row['error_message']) is not str or not row['error_message']:
            errors.append(f'{index}:refusal_evidence')
        if row['accepted'] is True:
            accepted_counts[arm] += 1
            stale_counts[arm] += begin < grant
        if begin == 300 and matches:
            witnesses[(arm, grant)] = row
    if seen != set(expected_order) or observed_order != expected_order:
        errors.append('complete_ordered_denominator')
    witness_results = {}
    for arm in ARMS:
        earlier, later = witnesses.get((arm, 200)), witnesses.get((arm, 400))
        if earlier is None or later is None:
            errors.append(arm + ':missing_witness'); continue
        same_before = same_json(earlier['before'], later['before'])
        if arm != 'authorization_floor':
            valid = same_before and earlier['accepted'] is True and later['accepted'] is True
        else:
            e, l = copy.deepcopy(earlier['before']), copy.deepcopy(later['before'])
            valid = e.pop('authorized_ns', None) == 200 and l.pop('authorized_ns', None) == 400 and same_json(e, l) and earlier['accepted'] is True and later['accepted'] is False
        if not valid:
            errors.append(arm + ':indistinguishability_witness')
        witness_results[arm] = {'complete_before_state_equal': same_before, 'begin_ns': 300,
                                'accepted_grant200': earlier['accepted'], 'accepted_grant400': later['accepted']}
    if accepted_counts != {'baseline': 16, 'observation_floor': 12, 'authorization_floor': 5} or stale_counts != {'baseline': 11, 'observation_floor': 7, 'authorization_floor': 0}:
        errors.append('derived_counts')
    return {'decision': 'HOLD_ORDER_EVIDENCE' if errors else 'PASS_ORDER_MEMORY_SCOPED',
            'rows': len(rows), 'accepted': accepted_counts, 'before_grant_accepted': stale_counts,
            'witnesses': witness_results, 'errors': errors}


def controls(record):
    tests = []
    def trial(name, mutate):
        modified = copy.deepcopy(record)
        mutate(modified)
        result = audit(modified)
        tests.append({'control': name, 'effective': not same_json(modified, record),
                      'refused': bool(result['errors']), 'decision': result['decision'], 'errors': result['errors']})
    trial('missing_row', lambda x: x['rows'].pop())
    trial('duplicate_row', lambda x: x['rows'].__setitem__(0, copy.deepcopy(x['rows'][1])))
    trial('wrong_row_order', lambda x: x['rows'].reverse())
    trial('boolean_grant', lambda x: x['rows'][0].__setitem__('grant_ns', True))
    trial('integer_request_flag', lambda x: x['rows'][0].__setitem__('request_matches', 1))
    trial('nested_boolean_clock', lambda x: x['rows'][0]['before']['observation'].__setitem__('captured_ns', True))
    def stale(x):
        row = next(r for r in x['rows'] if r['arm'] == 'authorization_floor' and r['grant_ns'] == 400 and r['begin_ns'] == 300 and r['request_matches'])
        row.update(accepted=True, after=state_after(row['before'], 300), error_type=None, error_message=None, unchanged_on_refusal=None)
    trial('fabricated_stale_acceptance', stale)
    def equality(x):
        row = next(r for r in x['rows'] if r['arm'] == 'authorization_floor' and r['grant_ns'] == r['begin_ns'] and r['request_matches'])
        row.update(accepted=False, after=copy.deepcopy(row['before']), error_type='ContractError', error_message='fabricated equality rejection', unchanged_on_refusal=True)
    trial('fabricated_equality_refusal', equality)
    def consumed(x):
        row = next(r for r in x['rows'] if r['arm'] == 'authorization_floor' and r['grant_ns'] == 400 and r['begin_ns'] == 300 and r['request_matches'])
        row['after'] = state_after(row['before'], 300)
    trial('refusal_consumed_request', consumed)
    def remembered(x):
        row = next(r for r in x['rows'] if r['arm'] == 'authorization_floor')
        row['before']['authorized_ns'] = 900
    trial('false_grant_memory', remembered)
    trial('wrong_exception_type', lambda x: x['rows'][1].__setitem__('error_type', 'RuntimeError'))
    trial('wrong_source_identity', lambda x: x.__setitem__('source_base', '0'*40))
    return tests


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('audit_retained.py matrix.raw.json')
    raw = json.loads(Path(sys.argv[1]).read_bytes(), object_pairs_hook=unique_object)
    result = audit(raw)
    result['controls'] = controls(raw)
    result['control_gate'] = all(row['effective'] and row['refused'] for row in result['controls'])
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']) or not result['control_gate'])
