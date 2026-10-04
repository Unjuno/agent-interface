"""Raw-only independent literal receipt semantics and exhaustive path oracle."""
from __future__ import annotations
import copy
import hashlib
import itertools
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def require(value, label):
    if not value:
        raise ValueError(label)

def path_oracle(case, steps):
    require(type(steps) is int and 0 <= steps <= 8, 'bounded path length')
    paths = []
    for start in case['initial_states']:
        for disturbances in itertools.product(case['disturbances'], repeat=steps):
            positions = [start]
            for drift in disturbances:
                positions.append(positions[-1] + case['action'] + drift)
            paths.append(positions)
    for index in range(steps + 1):
        values = [path[index] for path in paths]
        if max(values) >= case['boundary_by_step'][index]:
            return {'safe': False, 'first_unsafe_step': index, 'worst_position': max(values)}
    return {'safe': True, 'first_unsafe_step': None, 'worst_position': max(path[-1] for path in paths)}

def usable(event, case):
    return event.get('kind') == 'FRESH' and event.get('generation') == case['source_generation'] and event.get('age', case['max_receipt_age'] + 1) <= case['max_receipt_age']

def reference(case, legacy_empty=False):
    # A known scheduled deadline has no delivered observation when the deck is
    # empty. The second interpretation models the hypothesized retained defect.
    records = case['checkpoint_events']
    if not records:
        records = [{'kind': 'FRESH', 'generation': case['source_generation'], 'age': 0}] if legacy_empty else [{'kind': 'MISSING'}]
    first_fresh = usable(records[0], case)
    misses = 0
    invalid = case['target_invalidated']
    for event in records:
        if usable(event, case):
            break
        if event.get('kind') == 'TARGET_INVALIDATED':
            invalid = True
            break
        misses += 1
    safe_base = [h for h in range(case['max_horizon'] + 1) if path_oracle(case, 0 if h == 0 else h + case['release_lag'])['safe']]
    base = max(safe_base)
    a_steps = 0 if not base or invalid else base + case['release_lag'] + (0 if first_fresh else case['observation_interval'])
    a = path_oracle(case, a_steps)
    b_steps = 0 if not base or invalid else base + case['release_lag']
    b = path_oracle(case, b_steps)
    table = []
    bound = case['max_consecutive_misses']
    if invalid:
        selected, c_disposition = 0, 'YIELD_INVALIDATED_TARGET'
    else:
        feasible = []
        for h in range(case['max_horizon'] + 1):
            checks = [{'misses': n, **path_oracle(case, 0 if h == 0 else h + n * case['observation_interval'] + case['release_lag'])} for n in range(bound + 1)]
            certified = all(check['safe'] for check in checks)
            table.append({'horizon': h, 'checks': checks, 'safe_for_all_loss_patterns': certified})
            if certified:
                feasible.append(h)
        selected, c_disposition = max(feasible), 'ROBUST_LOSS_HORIZON'
    c_safe = selected == 0 if invalid else all(row['safe_for_all_loss_patterns'] for row in table if row['horizon'] <= selected)
    beyond = misses > bound
    stress = None
    if beyond and selected:
        extra_steps = selected + (bound + 1) * case['observation_interval'] + case['release_lag']
        stress = {'misses': bound + 1, 'safe': path_oracle(case, extra_steps)['safe'], 'disposition': 'OUT_OF_BOUND_NOT_CERTIFIED', 'held_steps_if_illegally_continued': extra_steps}
    actual = 'YIELD_INVALIDATED_TARGET' if invalid else ('BOUND_EXCEEDED_STOP_AT_FROZEN_DEADLINE' if beyond else ('NO_LOSS_CONTROL' if misses == 0 else 'IN_BOUND_ERASURE_PATTERN'))
    return {
        'case_id': case['id'],
        'base_no_loss_horizon': base,
        'policy_a_optimistic': {'assumes_checkpoint_success': True, 'receipt_was_usable': first_fresh, 'held_steps_before_release': a_steps, 'safe': a['safe'] and not invalid, 'disposition': 'INVALIDATED' if invalid else ('UNSAFE_OPTIMISTIC_EXTENSION' if not a['safe'] else 'SAFE_IN_THIS_FIXTURE')},
        'policy_b_release_on_absence': {'release_on_missing_or_stale': not first_fresh, 'receipt_was_usable': first_fresh, 'held_steps_before_release': b_steps, 'safe': b['safe'] and not invalid, 'disposition': 'YIELD_INVALIDATED_TARGET' if invalid else ('RELEASED_ON_ABSENT_OR_STALE' if not first_fresh else 'FRESH_CHECKPOINT')},
        'policy_c_loss_robust': {'selected_horizon': selected, 'disposition': c_disposition, 'safe_for_all_declared_patterns': c_safe, 'horizon_table': table, 'actual_consecutive_misses': misses, 'actual_status': actual},
        'stress': stress,
    }

def audit(raw):
    cases_bytes = (HERE / 'CASES.json').read_bytes()
    sources_bytes = (HERE / 'SOURCE_MAP.json').read_bytes()
    require(raw['schema'] == 'checkpoint-delivery-raw-v1', 'raw schema')
    require(raw['source_map_sha256'] == hashlib.sha256(sources_bytes).hexdigest(), 'source-map identity')
    require(raw['cases_sha256'] == hashlib.sha256(cases_bytes).hexdigest(), 'case identity')
    cases = json.loads(cases_bytes)['cases']
    expected_keys = [(item['case']['id'], arm) for item in cases for arm in ['legacy', 'explicit_absence']]
    require([(row['case_id'], row['arm']) for row in raw['rows']] == expected_keys, 'row coverage/order')
    require(type(raw['owner_thread_id']) is int and raw['owner_thread_id'] > 0, 'owner type')
    contract_mismatches = []
    row_by_key = {}
    for row, (case_id, arm) in zip(raw['rows'], expected_keys):
        item = next(item for item in cases if item['case']['id'] == case_id)
        original = item['case']
        require(row['context'] == item['context'] and row['encoding'] == item['encoding'], 'case labels')
        evaluated = copy.deepcopy(original)
        if arm == 'explicit_absence' and evaluated['checkpoint_events'] == []:
            evaluated['checkpoint_events'] = [{'kind': 'MISSING'}]
        require(encoded(row['evaluated_case']) == encoded(evaluated), 'evaluated input')
        require(row['original_case_sha256'] == hashlib.sha256(encoded(original)).hexdigest(), 'original input hash')
        require(row['evaluated_case_sha256'] == hashlib.sha256(encoded(evaluated)).hexdigest(), 'evaluated input hash')
        require(row['input_unchanged'] is True, 'input mutation')
        require(type(row['owner_thread_id']) is int and row['owner_thread_id'] == raw['owner_thread_id'], 'thread mismatch')
        require(encoded(row['output']) == encoded(reference(evaluated, legacy_empty=(arm == 'legacy'))), 'full literal source-behavior mismatch: ' + case_id + '/' + arm)
        require(encoded(row['retained_audit']) == encoded({'status': 'PASS_METHOD_SCOPED', 'rows': 1, 'errors': []}), 'retained audit record')
        desired = reference(original)
        if encoded(row['output']) != encoded(desired):
            contract_mismatches.append({'case_id': case_id, 'arm': arm, 'retained_audit_accepted': True, 'receipt_was_usable': row['output']['policy_b_release_on_absence']['receipt_was_usable'], 'actual_status': row['output']['policy_c_loss_robust']['actual_status']})
        row_by_key[(case_id, arm)] = row
    require(len(contract_mismatches) == 3 and all(row['arm'] == 'legacy' and row['case_id'].endswith('__empty') for row in contract_mismatches), 'frozen counterexample gate')
    for item in cases:
        key = item['case']['id']
        if item['encoding'] != 'empty':
            require(encoded(row_by_key[(key, 'legacy')]['output']) == encoded(row_by_key[(key, 'explicit_absence')]['output']), 'nonempty behavior changed')
        else:
            repaired = copy.deepcopy(row_by_key[(key, 'explicit_absence')]['output'])
            explicit = copy.deepcopy(row_by_key[(item['context'] + '__missing', 'legacy')]['output'])
            repaired.pop('case_id'); explicit.pop('case_id')
            require(encoded(repaired) == encoded(explicit), 'absence encoding inequivalence after normalization')
    return {'status': 'COUNTEREXAMPLE_DELIVERY_REPRESENTATION_AND_NORMALIZATION_SCOPED', 'rows': len(raw['rows']), 'literal_reconstruction_errors': 0, 'legacy_contract_mismatches': contract_mismatches, 'normalized_contract_mismatches': 0, 'nonempty_case_pairs_unchanged': 9, 'normalized_empty_equals_explicit_missing': 3, 'not_a_physical_safety_or_live_result': True}

def controls(raw):
    changed = []
    item = copy.deepcopy(raw); item['rows'].pop(); changed.append(('omitted_row', item))
    item = copy.deepcopy(raw); item['rows'][1] = copy.deepcopy(item['rows'][0]); changed.append(('duplicate_row', item))
    item = copy.deepcopy(raw); item['rows'][0]['output']['policy_b_release_on_absence']['receipt_was_usable'] = False; changed.append(('conceal_legacy_false_fresh', item))
    item = copy.deepcopy(raw); item['rows'][1]['output']['policy_b_release_on_absence']['receipt_was_usable'] = True; changed.append(('invent_normalized_fresh', item))
    item = copy.deepcopy(raw); item['rows'][0]['evaluated_case']['checkpoint_events'] = [{'kind': 'FRESH', 'generation': 5, 'age': 0}]; changed.append(('replace_empty_input', item))
    item = copy.deepcopy(raw); item['rows'][0]['output']['base_no_loss_horizon'] = 5.0; changed.append(('numeric_type_alias', item))
    item = copy.deepcopy(raw); item['rows'][0]['owner_thread_id'] += 1; changed.append(('wrong_thread', item))
    item = copy.deepcopy(raw); item['source_map_sha256'] = '0' * 64; changed.append(('wrong_source', item))
    results = []
    for label, item in changed:
        try:
            audit(item)
        except ValueError as exc:
            results.append({'control': label, 'rejected': True, 'reason': str(exc)})
        else:
            raise ValueError('corruption was accepted: ' + label)
    return results

if __name__ == '__main__':
    raw = json.loads(pathlib.Path(sys.argv[1]).read_bytes())
    result = audit(raw)
    result['copied_raw_controls'] = controls(raw)
    print(json.dumps(result, sort_keys=True, indent=2))
