"""Finite real-core/compiled-runtime checks through explicitly inert glue."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def scalar(value):
    if type(value) is float:
        return {'type': 'float', 'repr': repr(value)}
    return {'type': type(value).__name__, 'value': value}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()

def interface():
    return {'format': 'compiled-gui-interface-v1', 'interface_id': 'composition',
        'session_scope': 'inert-only', 'surface': 'synthetic', 'predicates': ['phase'],
        'symbols': {'target': {'kind': 'target_reference', 'target_reference': 'inert',
            'identity_predicate': 'phase', 'dependencies': ['phase']}},
        'actions': {'once': {'target_symbol': 'target', 'operation': 'metadata-only',
                            'expected_effect': {'phase': 1}}},
        'method': {'name': 'one-action', 'version': '1', 'initial_state': 'ready',
            'max_transitions': 1, 'max_runtime_ms': 1,
            'states': {
                'ready': {'branches': [{'when': {'phase': 0}, 'outcome': 'action',
                    'action': 'once', 'next_state': 'done', 'reason': None}]},
                'done': {'branches': [{'when': {'phase': 1}, 'outcome': 'complete',
                    'action': None, 'next_state': None, 'reason': None}]}}}}

def inputs(case):
    program = {'schema': 'agent-interface/program-v1', 'program_id': 'inert-one',
        'source': {'observation_seq': 1, 'binding_revision': 1},
        'authority': {'lease_id': 'inert', 'expires_at_ns': 100},
        'terminal': {'release_all_required': True}, 'ops': [{'op': 'release_all'}]}
    manifest = {'schema': 'agent-interface/backend-v1', 'backend_id': 'inert',
        'platform': {'os': 'linux', 'backend': 'metadata-only'},
        'capabilities': {'input.release_all': {'state': 'supported'}},
        'coordinate_frames': ['screen_physical_px'],
        'clock': {'unit': 'ns', 'monotonic': True}, 'permissions': []}
    profile = case['manifest']
    if profile == 'os-list': manifest['platform']['os'] = []
    elif profile == 'state-dict': manifest['capabilities']['input.release_all']['state'] = {}
    elif profile == 'frame-list': manifest['coordinate_frames'] = [[]]
    elif profile == 'unsupported': manifest['capabilities']['input.release_all']['state'] = 'unsupported'
    elif profile == 'permission': manifest['capabilities']['input.release_all']['state'] = 'permission_required'
    elif profile == 'os-unknown': manifest['platform']['os'] = 'other'
    elif profile == 'frame-unknown': manifest['coordinate_frames'] = ['other']
    elif profile != 'valid': raise ValueError(profile)
    now = {'zero': 0, 'equality': 100, 'expired': 101, 'nan': float('nan'),
           'bool': True, 'float': 100.0}[case['now']]
    generations = {'match': 1, 'stale': 2, 'bool': True, 'float': 1.0}
    context = dict(now_ns=now, current_observation_seq=generations[case['observation']],
                   current_binding_revision=generations[case['binding']])
    sequence = {'match': 1, 'mismatch': 2, 'bool': True, 'float': 1.0}[case['compiled_sequence']]
    return program, manifest, context, sequence

def run_case(case, contract, compiled):
    program, manifest, context, sequence = inputs(case)
    def snapshot():
        return {'program': copy.deepcopy(program), 'manifest': copy.deepcopy(manifest),
                'context': {key: scalar(value) for key, value in context.items()},
                'compiled_sequence': scalar(sequence)}
    before = snapshot()
    trace, journals = [], []
    core_result = None
    observes = 0
    def observe(payload):
        nonlocal observes
        observes += 1
        trace.append({'call': 'observe', 'sequence': observes})
        return {'sequence': observes, 'captured_ns': 0, 'surface': 'synthetic',
            'predicates': {'phase': observes - 1}, 'evidence_ref': f'e{observes}',
            'evidence_digest': f'd{observes}'}
    def admit(payload):
        nonlocal core_result
        trace.append({'call': 'admit'})
        try:
            result = contract.admit_program(program, manifest, **context)
        except Exception as error:
            trace.append({'call': 'core_exception', 'type': type(error).__name__})
            raise
        core_result = {'accepted': result.accepted, 'error': result.error,
                       'required_capabilities': list(result.required_capabilities)}
        trace.append({'call': 'core_result', **core_result})
        return {'eligible': result.accepted,
            'status': 'revalidated' if result.accepted else result.error,
            'authorization': 'inert-token' if result.accepted else None,
            'expected_sequence': sequence, 'valid_until_ns': 1_000_000}
    def execute(payload):
        trace.append({'call': 'execute', 'expected_sequence': scalar(payload['expected_sequence'])})
        return {'status': 'completed', 'action_id': 'inert-action', 'effect_ref': 'inert-effect',
                'release': {'verified': True, 'keys_down': [], 'buttons_down': []}}
    def verify(payload):
        trace.append({'call': 'verify_effect', 'sequence': payload['observation']['sequence']})
        return {'status': 'succeeded', 'evidence_ref': payload['observation']['evidence_ref']}
    exception, terminal = None, None
    try:
        result = compiled.run(interface(), {'observe': observe, 'admit': admit,
            'execute': execute, 'verify_effect': verify, 'cancelled': lambda: False,
            'journal': lambda row: journals.append(copy.deepcopy(row))}, clock=lambda: 0)
        terminal = {key: result[key] for key in ('outcome', 'reason', 'completed_transitions',
                    'pending_effect', 'frontier_model_resumptions')}
    except Exception as error:
        exception = {'type': type(error).__name__, 'message': str(error)}
    after = snapshot()
    return {'case': case, 'input_before': before, 'input_after': after,
            'input_before_sha256': digest(before), 'input_after_sha256': digest(after),
            'core_admission': core_result, 'trace': trace, 'journal': journals,
            'terminal': terminal, 'exception': exception}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=['baseline', 'combined'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    source = args.source or ROOT / 'source' / args.arm
    sys.path.insert(0, str(source))
    from runtime.core_v1 import contract, compiled_gui
    assert Path(contract.__file__).resolve().is_relative_to(source.resolve())
    assert Path(compiled_gui.__file__).resolve().is_relative_to(source.resolve())
    cases = [json.loads(line) for line in (ROOT / 'cases.jsonl').read_text().splitlines()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        for case in cases:
            row = {'arm': args.arm, **run_case(case, contract, compiled_gui)}
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'arm': args.arm, 'rows': len(cases),
        'raw_bytes': args.output.stat().st_size, 'raw_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))

if __name__ == '__main__': main()
