"""Versioned raw-only two-step prefix oracle; no runtime or producer imports."""
import hashlib
import json
from pathlib import Path
import sys
import audit as v2

STATES = ('empty', 'filled', 'done')
ACTIONS = ('enter', 'save')

def observation(sequence):
    return {'sequence': sequence, 'captured_ns': 0, 'surface': 'form',
            'predicates': {'phase': sequence - 1}, 'evidence_ref': f'frame{sequence}',
            'evidence_digest': f'digest{sequence}'}

def audit(record):
    checked = v2.audit(record)
    errors = checked['errors']
    for row in record.get('rows', []):
        status, index, stage = row.get('status'), row.get('ref_index'), row.get('stage')
        if status not in v2.LABELS or type(index) is not int or not 0 <= index < 12 or type(stage) is not int or stage not in (1, 2):
            continue  # v2 retains malformed case diagnostics.
        reject = status == 'succeeded' and index < 9 and record['arm'] == 'repaired'
        steps = stage if reject or status != 'succeeded' else 2
        expected_events = [{'event': 'observation_recorded', 'state': 'empty',
                            'sequence': 1, 'evidence_ref': 'frame1'}]
        expected_calls = {'observe': [{'required_predicates': ['phase'], 'state': STATES[j]}
                                      for j in range(steps + 1)],
                          'admit': [], 'execute': [], 'verify_effect': []}
        transitions = []
        for sequence in range(1, steps + 1):
            action = ACTIONS[sequence - 1]
            expected_calls['admit'].append({'interface_id': 'effect-evidence', 'session_scope': 'private',
                'action': action, 'operation': action, 'observation': observation(sequence),
                'symbol': {'kind': 'target_reference', 'target_reference': 'field',
                           'identity_predicate': 'phase', 'dependencies': ['phase']}})
            expected_calls['execute'].append({'action': action, 'operation': action,
                'authorization': 'one-use', 'expected_sequence': sequence, 'valid_until_ns': 10_000_000})
            expected_calls['verify_effect'].append({'action': action, 'effect_ref': 'effect',
                'expected_effect': {'phase': sequence}, 'observation': observation(sequence + 1)})
            expected_events.extend([
                {'event': 'branch_selected', 'state': STATES[sequence - 1], 'action': action,
                 'outcome': 'action', 'matched_conditions': {'phase': sequence - 1},
                 'evidence_ref': f'frame{sequence}'},
                {'event': 'action_terminal', 'action': action, 'status': 'completed',
                 'action_id': str(sequence), 'release_verified': True},
                {'event': 'observation_recorded', 'state': STATES[sequence],
                 'sequence': sequence + 1, 'evidence_ref': f'frame{sequence + 1}'},
            ])
            transitions.append({'from_state': STATES[sequence - 1], 'to_state': STATES[sequence],
                'action': action, 'matched_conditions': {'phase': sequence - 1},
                'observation_sequence': sequence, 'evidence_ref': f'frame{sequence}',
                'action_id': str(sequence), 'effect_ref': 'effect', 'release_verified': True})
            if reject and sequence == stage:
                break
            expected_events.append({'event': 'effect_checked', 'action': action,
                'status': status if sequence == stage else 'succeeded',
                'evidence_ref': v2.VALUES[index] if sequence == stage else f'frame{sequence + 1}'})
        if not reject:
            if status == 'succeeded':
                expected_events.append({'event': 'branch_selected', 'state': 'done', 'action': None,
                    'outcome': 'complete', 'matched_conditions': {'phase': 2}, 'evidence_ref': 'frame3'})
            reason = {'succeeded': 'method_complete', 'failed': 'effect_failed', 'unavailable': 'effect_unavailable'}[status]
            expected_events.append({'event': 'runtime_finished', 'completed_transitions': steps,
                'outcome': 'TASK_SUCCEEDED' if status == 'succeeded' else 'SAFE_YIELD', 'reason': reason})
        if not v2.same(row.get('events'), expected_events):
            errors.append('literal_event_prefix:' + row['id'])
        if not v2.same(row.get('calls'), expected_calls):
            errors.append('literal_request_prefix:' + row['id'])
        result = row.get('result')
        if type(result) is dict:
            critical = [event for event in expected_events if event['event'] != 'observation_recorded']
            if not v2.same(result.get('critical_events'), critical):
                errors.append('literal_critical_prefix:' + row['id'])
            if not v2.same(result.get('transitions'), transitions):
                errors.append('literal_transition_prefix:' + row['id'])
            pending = None if status == 'succeeded' else {
                'action': ACTIONS[steps - 1], 'expected_effect': {'phase': steps}, 'effect_ref': 'effect'}
            if not v2.same(result.get('pending_effect'), pending):
                errors.append('literal_pending_effect:' + row['id'])
    return checked

if __name__ == '__main__':
    before, after, output = map(Path, sys.argv[1:4])
    result = {'schema': 'compiled-success-evidence-audit-v3',
              'baseline': audit(json.loads(before.read_bytes())),
              'repaired': audit(json.loads(after.read_bytes())),
              'baseline_raw_sha256': hashlib.sha256(before.read_bytes()).hexdigest(),
              'repaired_raw_sha256': hashlib.sha256(after.read_bytes()).hexdigest()}
    ok = (not result['baseline']['errors'] and not result['repaired']['errors'] and
          len(result['baseline']['contract_violations']) == 18 and not result['repaired']['contract_violations'])
    result['status'] = 'PASS_REFERENCE_AND_LITERAL_PREFIX_SCOPED' if ok else 'FAIL_AUDIT'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps(result))
    sys.exit(0 if ok else 1)
