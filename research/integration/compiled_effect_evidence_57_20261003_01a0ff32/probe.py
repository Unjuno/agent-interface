"""Finite input-free regression deck for the real compiled GUI graph."""
import copy
import hashlib
import json
from pathlib import Path
import platform
import sys
from datetime import datetime, timezone

REFS = [None, '', 0, True, False, 1.0, [], {}, 'x' * 65, 'w', 'x' * 64, 'independent-witness']
STATUSES = ['succeeded', 'failed', 'unavailable']

def spec():
    states = {}
    for phase, name in enumerate(['empty', 'filled', 'done']):
        states[name] = {'branches': [{'when': {'phase': phase},
            'outcome': 'action' if phase < 2 else 'complete',
            'action': ['enter', 'save', None][phase],
            'next_state': ['filled', 'done', None][phase], 'reason': None}]}
    return {'format': 'compiled-gui-interface-v1', 'interface_id': 'effect-evidence',
        'session_scope': 'private', 'surface': 'form', 'predicates': ['phase'],
        'symbols': {'field': {'kind': 'target_reference', 'target_reference': 'field',
                            'identity_predicate': 'phase', 'dependencies': ['phase']}},
        'actions': {'enter': {'target_symbol': 'field', 'operation': 'enter', 'expected_effect': {'phase': 1}},
                    'save': {'target_symbol': 'field', 'operation': 'save', 'expected_effect': {'phase': 2}}},
        'method': {'name': 'two-step', 'version': '1', 'initial_state': 'empty',
                   'max_transitions': 2, 'max_runtime_ms': 10, 'states': states}}

def run_case(runtime, status, value, stage):
    events, calls = [], {k: [] for k in ('observe', 'admit', 'execute', 'verify_effect')}
    verdicts = []
    def observe(payload):
        calls['observe'].append(copy.deepcopy(payload))
        i = len(calls['observe'])
        return {'sequence': i, 'captured_ns': 0, 'surface': 'form', 'predicates': {'phase': i - 1},
                'evidence_ref': 'frame' + str(i), 'evidence_digest': 'digest' + str(i)}
    def admit(payload):
        calls['admit'].append(copy.deepcopy(payload))
        return {'eligible': True, 'status': 'revalidated', 'authorization': 'one-use',
                'expected_sequence': payload['observation']['sequence'], 'valid_until_ns': 100_000_000}
    def execute(payload):
        calls['execute'].append(copy.deepcopy(payload))
        return {'status': 'completed', 'action_id': str(len(calls['execute'])), 'effect_ref': 'effect',
                'release': {'verified': True, 'keys_down': [], 'buttons_down': []}}
    def verify(payload):
        calls['verify_effect'].append(copy.deepcopy(payload))
        result = {'status': status, 'evidence_ref': copy.deepcopy(value)} if len(calls['verify_effect']) == stage else {
            'status': 'succeeded', 'evidence_ref': payload['observation']['evidence_ref']}
        verdicts.append((result, copy.deepcopy(result)))
        return result
    interface = spec()
    before = copy.deepcopy(interface)
    result, exception = None, None
    try:
        result = runtime['run'](interface, {'observe': observe, 'admit': admit, 'execute': execute,
            'verify_effect': verify, 'cancelled': lambda: False, 'journal': lambda e: events.append(copy.deepcopy(e))},
            clock=lambda: 0)
    except Exception as error:
        exception = type(error).__name__
    return {'result': result, 'exception': exception, 'events': events, 'calls': calls,
            'interface_unchanged': interface == before,
            'verdicts_unchanged': all(json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True) for a, b in verdicts)}

if __name__ == '__main__':
    source, arm, output = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
    runtime = {'__name__': 'frozen_graph'}
    source_bytes = source.read_bytes()
    started = datetime.now(timezone.utc).isoformat()
    exec(compile(source_bytes, str(source), 'exec'), runtime)
    rows = []
    for status in STATUSES:
        for ref_index, ref in enumerate(REFS):
            for stage in (1, 2):
                rows.append({'id': f'{status}-{ref_index}-{stage}', 'status': status,
                    'ref_index': ref_index, 'evidence_ref': ref, 'stage': stage,
                    **run_case(runtime, status, ref, stage)})
    record = {'schema': 'compiled-success-evidence-regression-v1', 'arm': arm,
        'source_sha256': hashlib.sha256(source_bytes).hexdigest(), 'rows': rows,
        'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(), 'platform': platform.platform(),
        'scope': 'ordinary input-free engineering regression; no native backend'}
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'arm': arm, 'rows': len(rows), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
