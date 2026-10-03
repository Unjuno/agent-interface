"""Finite, input-free check of the real compiled runtime, independent of its tests."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys


class IntAlias(int):
    pass


def specification():
    return {
        'format': 'compiled-gui-interface-v1', 'interface_id': 'sequence-probe',
        'session_scope': 'no-input', 'surface': 'fixture', 'predicates': ['done'],
        'symbols': {'target': {'kind': 'target_reference', 'target_reference': 'fixture',
            'identity_predicate': 'done', 'dependencies': ['done']}},
        'actions': {'mark': {'target_symbol': 'target', 'operation': 'no-input-mark',
            'expected_effect': {'done': True}}},
        'method': {'name': 'one-action', 'version': '1', 'initial_state': 'start',
            'max_transitions': 1, 'max_runtime_ms': 1,
            'states': {
                'start': {'branches': [{'when': {'done': False}, 'outcome': 'action',
                    'action': 'mark', 'next_state': 'end', 'reason': None}]},
                'end': {'branches': [{'when': {'done': True}, 'outcome': 'complete',
                    'action': None, 'next_state': None, 'reason': None}]}}}}


def exercise(run, sequence, value, profile):
    calls = {'observe': 0, 'execute': 0, 'verify_effect': 0}
    dispatched = []
    journal = []

    def observe(_):
        index = calls['observe']
        calls['observe'] += 1
        return dict(sequence=sequence + index, captured_ns=0, surface='fixture',
                    predicates={'done': bool(index)}, evidence_ref=f'frame-{index}',
                    evidence_digest=f'digest-{index}')

    def admit(_):
        return dict(eligible=profile != 'ineligible',
                    status='stale' if profile == 'ineligible' else 'revalidated',
                    authorization='fixture-only', expected_sequence=value,
                    valid_until_ns=0 if profile == 'expired' else 1000)

    def execute(payload):
        calls['execute'] += 1
        dispatched.append({'type': type(payload['expected_sequence']).__name__,
                           'repr': repr(payload['expected_sequence'])})
        return dict(status='completed', action_id='fixture-action', effect_ref='fixture-effect',
                    release=dict(verified=True, keys_down=[], buttons_down=[]))

    def verify(_):
        calls['verify_effect'] += 1
        return dict(status='succeeded', evidence_ref='fixture-effect')

    result, exception = None, None
    try:
        receipt = run(specification(), dict(observe=observe, admit=admit, execute=execute,
            verify_effect=verify, cancelled=lambda: False, journal=journal.append), clock=lambda: 0)
        result = {key: receipt[key] for key in ('outcome', 'reason', 'completed_transitions')}
    except Exception as error:
        exception = {'type': type(error).__name__, 'message': str(error)}
    return dict(result=result, exception=exception, calls=calls, dispatched=dispatched,
                critical_events=[row for row in journal if row['event'] in
                    ('admission_refused', 'action_terminal', 'effect_checked', 'runtime_finished')])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.root.resolve()))
    from runtime.core_v1.compiled_gui import run
    import runtime.core_v1.compiled_gui as module
    rows = []
    for sequence in (0, 1, 2, 7, 2**63 - 1):
        values = [('equal_int', sequence), ('wrong_int', sequence + 1),
                  ('false', False), ('true', True), ('equal_float', float(sequence)),
                  ('string', str(sequence)), ('null', None), ('int_subclass', IntAlias(sequence)),
                  ('nan', float('nan')), ('infinity', float('inf'))]
        for label, value in values:
            for profile in ('valid', 'ineligible', 'expired'):
                rows.append(dict(case_id=f'{sequence}:{label}:{profile}', observation_sequence=sequence,
                    admission_label=label, admission_type=type(value).__name__, admission_repr=repr(value),
                    profile=profile, **exercise(run, sequence, value, profile)))
    raw = dict(format='compiled-admission-sequence-finite-v1', python=platform.python_version(),
        platform=platform.platform(), module_sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        scope='finite analytical/engineering check; no physical input, backend, model or timing measurement',
        rows=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(raw, output, sort_keys=True, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps({'rows': len(rows), 'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
