"""Raw-only finite oracle. Imports neither the runner nor either runtime."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AXES = {'manifest': ('valid', 'os-list', 'state-dict', 'frame-list', 'unsupported',
                    'permission', 'os-unknown', 'frame-unknown'),
        'now': ('zero', 'equality', 'expired', 'nan', 'bool', 'float'),
        'observation': ('match', 'stale', 'bool', 'float'),
        'binding': ('match', 'stale', 'bool', 'float'),
        'compiled_sequence': ('match', 'mismatch', 'bool', 'float')}

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()

def expected_input(case):
    # Independently authored literal reference objects; no runtime/candidate import.
    profile = case['manifest']
    operating_system = [] if profile == 'os-list' else 'other' if profile == 'os-unknown' else 'linux'
    state = {} if profile == 'state-dict' else 'unsupported' if profile == 'unsupported' \
        else 'permission_required' if profile == 'permission' else 'supported'
    frame = [] if profile == 'frame-list' else 'other' if profile == 'frame-unknown' else 'screen_physical_px'
    times = {'zero': {'type': 'int', 'value': 0}, 'equality': {'type': 'int', 'value': 100},
        'expired': {'type': 'int', 'value': 101}, 'nan': {'type': 'float', 'repr': 'nan'},
        'bool': {'type': 'bool', 'value': True}, 'float': {'type': 'float', 'repr': '100.0'}}
    generations = {'match': {'type': 'int', 'value': 1}, 'stale': {'type': 'int', 'value': 2},
        'mismatch': {'type': 'int', 'value': 2}, 'bool': {'type': 'bool', 'value': True},
        'float': {'type': 'float', 'repr': '1.0'}}
    return {'program': {'schema': 'agent-interface/program-v1', 'program_id': 'inert-one',
        'source': {'observation_seq': 1, 'binding_revision': 1},
        'authority': {'lease_id': 'inert', 'expires_at_ns': 100},
        'terminal': {'release_all_required': True}, 'ops': [{'op': 'release_all'}]},
        'manifest': {'schema': 'agent-interface/backend-v1', 'backend_id': 'inert',
            'platform': {'os': operating_system, 'backend': 'metadata-only'},
            'capabilities': {'input.release_all': {'state': state}},
            'coordinate_frames': [frame], 'clock': {'unit': 'ns', 'monotonic': True},
            'permissions': []},
        'context': {'now_ns': times[case['now']],
            'current_observation_seq': generations[case['observation']],
            'current_binding_revision': generations[case['binding']]},
        'compiled_sequence': generations[case['compiled_sequence']]}

def expected_core(case):
    if case['manifest'] in ('os-list', 'state-dict', 'frame-list', 'os-unknown', 'frame-unknown'):
        return False, 'INVALID_PROGRAM'
    if case['now'] in ('nan', 'bool', 'float') or any(
            case[key] in ('bool', 'float') for key in ('observation', 'binding')):
        return False, 'INVALID_PROGRAM'
    if case['now'] == 'expired': return False, 'LEASE_EXPIRED'
    if case['observation'] == 'stale': return False, 'STALE_OBSERVATION'
    if case['binding'] == 'stale': return False, 'STALE_BINDING'
    if case['manifest'] == 'unsupported': return False, 'UNSUPPORTED_CAPABILITY'
    if case['manifest'] == 'permission': return False, 'PERMISSION_DENIED'
    return True, None

def check(rows, expected_arm):
    errors, mismatches, execution_entries, successes = [], [], 0, 0
    products = list(itertools.product(*AXES.values()))
    expected_cases = [{'case_id': f'c{i:04d}', **dict(zip(AXES, values))}
                      for i, values in enumerate(products)]
    if len(rows) != len(expected_cases): errors.append('complete denominator missing')
    seen = set()
    for ordinal, row in enumerate(rows):
        case = row.get('case', {})
        identity = case.get('case_id')
        if identity in seen: errors.append(f'{identity}: duplicate')
        seen.add(identity)
        if ordinal >= len(expected_cases) or case != expected_cases[ordinal]:
            errors.append(f'{identity}: frozen case/order mismatch')
            continue
        if row.get('arm') != expected_arm: errors.append(f'{identity}: arm mismatch')
        before, after = row.get('input_before'), row.get('input_after')
        if canonical_hash(before) != canonical_hash(after) or \
                canonical_hash(before) != canonical_hash(expected_input(case)) or \
                row.get('input_before_sha256') != canonical_hash(before) or \
                row.get('input_after_sha256') != canonical_hash(after):
            errors.append(f'{identity}: mutated or unbound input')
        calls = [entry.get('call') for entry in row.get('trace', [])]
        execute_count, verify_count = calls.count('execute'), calls.count('verify_effect')
        execution_entries += execute_count
        core = row.get('core_admission')
        accepted, error = expected_core(case)
        local = []
        if core is None or type(core.get('accepted')) is not bool or \
                (core.get('accepted'), core.get('error')) != (accepted, error):
            local.append('core typed verdict')
        elif core.get('required_capabilities') != ([] if error == 'INVALID_PROGRAM' else ['input.release_all']):
            local.append('required capability contract')
        exception, terminal = row.get('exception'), row.get('terminal')
        if not accepted:
            if exception is not None or terminal != {'outcome': 'SAFE_YIELD',
                    'reason': 'authority_unavailable', 'completed_transitions': 0,
                    'pending_effect': None, 'frontier_model_resumptions': 0}:
                local.append('core refusal propagation')
            if execute_count or verify_count: local.append('dispatch after core refusal')
        elif case['compiled_sequence'] != 'match':
            if exception is None or exception.get('type') != 'ValueError' or terminal is not None:
                local.append('compiled type/identity rejection')
            if execute_count or verify_count: local.append('dispatch after compiled refusal')
        else:
            if exception is not None or terminal != {'outcome': 'TASK_SUCCEEDED',
                    'reason': 'method_complete', 'completed_transitions': 1,
                    'pending_effect': None, 'frontier_model_resumptions': 0}:
                local.append('normal terminal')
            if execute_count != 1 or verify_count != 1 or calls.count('observe') != 2:
                local.append('normal exact call counts')
            verifies = [entry for entry in row['trace'] if entry['call'] == 'verify_effect']
            if verifies and verifies[0].get('sequence') != 2: local.append('effect observation')
        if calls[:2] != ['observe', 'admit']: errors.append(f'{identity}: entry trace')
        if execute_count and ('core_result' not in calls or calls.index('core_result') > calls.index('execute')):
            errors.append(f'{identity}: missing admission before execute')
        action_events = [entry for entry in row.get('journal', []) if entry.get('event') == 'action_terminal']
        if len(action_events) != execute_count or any(entry.get('release_verified') is not True
                                                    for entry in action_events):
            errors.append(f'{identity}: inert release journal')
        if terminal is not None and terminal.get('outcome') == 'TASK_SUCCEEDED': successes += 1
        if local: mismatches.append({'case_id': identity, 'violations': local})
    return {'arm': expected_arm, 'rows': len(rows), 'execution_entries': execution_entries,
            'successes': successes, 'errors': errors, 'mismatch_count': len(mismatches),
            'mismatches': mismatches}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--arm', choices=['baseline', 'combined'], required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.raw.read_text(encoding='utf-8').splitlines()]
    result = check(rows, args.arm)
    result.update(raw_sha256=hashlib.sha256(args.raw.read_bytes()).hexdigest(),
                  disposition='PASS_SCOPED' if not result['errors'] and not result['mismatch_count']
                    else 'RETAINED_BASELINE_GAPS' if args.arm == 'baseline' and not result['errors']
                    else 'FAIL_SCOPED')
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if not result['errors'] and (args.arm == 'baseline' or not result['mismatch_count']) else 1

if __name__ == '__main__': raise SystemExit(main())
