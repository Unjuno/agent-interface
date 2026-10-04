import argparse
import hashlib
import importlib.util
import itertools
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

SEQUENCES = (0, 1, 2, 2**53, 2**63 - 1)
KINDS = ('exact', 'wrong', 'false', 'true', 'float', 'string', 'null',
         'subclass', 'decimal', 'fraction', 'equality_object', 'list')
PROFILES = ('valid', 'expired', 'ineligible')

class Subclass(int):
    pass

class EqualityObject:
    def __init__(self, counts):
        self.counts = counts
    def __ne__(self, other):
        self.counts['equality'] += 1
        return False
    def __repr__(self):
        return 'EqualityObject(always_equal)'

def value_for(kind, sequence, counts):
    return {
        'exact': lambda: sequence, 'wrong': lambda: sequence + 1,
        'false': lambda: False, 'true': lambda: True,
        'float': lambda: float(sequence), 'string': lambda: str(sequence),
        'null': lambda: None, 'subclass': lambda: Subclass(sequence),
        'decimal': lambda: Decimal(sequence), 'fraction': lambda: Fraction(sequence, 1),
        'equality_object': lambda: EqualityObject(counts), 'list': lambda: [sequence],
    }[kind]()

def specimen():
    return {
        'format': 'compiled-gui-interface-v1', 'interface_id': 'review',
        'session_scope': 'inert', 'surface': 'fixture', 'predicates': ['phase'],
        'symbols': {'target': {'kind': 'target_reference', 'target_reference': 'inert',
                               'identity_predicate': 'phase', 'dependencies': ['phase']}},
        'actions': {'step': {'target_symbol': 'target', 'operation': 'inert',
                             'expected_effect': {'phase': 'done'}}},
        'method': {'name': 'single', 'version': '1', 'initial_state': 'first',
                   'max_transitions': 1, 'max_runtime_ms': 1,
                   'states': {
                       'first': {'branches': [{'when': {'phase': 'ready'}, 'outcome': 'action',
                                              'action': 'step', 'next_state': 'last', 'reason': None}]},
                       'last': {'branches': [{'when': {'phase': 'done'}, 'outcome': 'complete',
                                             'action': None, 'next_state': None, 'reason': None}]},
                   }},
    }

def run_case(module, sequence, kind, profile):
    counts = {'observe': 0, 'admit': 0, 'execute': 0, 'verify': 0, 'equality': 0}
    value = value_for(kind, sequence, counts)
    dispatched = []
    def observe(_):
        counts['observe'] += 1
        step = counts['observe'] - 1
        return {'sequence': sequence + step, 'captured_ns': 0, 'surface': 'fixture',
                'predicates': {'phase': 'ready' if step == 0 else 'done'},
                'evidence_ref': f'frame{step}', 'evidence_digest': f'digest{step}'}
    def admit(_):
        counts['admit'] += 1
        return {'eligible': profile != 'ineligible',
                'status': 'stale' if profile == 'ineligible' else 'revalidated',
                'authorization': None if profile == 'ineligible' else 'inert-permit',
                'expected_sequence': value, 'valid_until_ns': 0 if profile == 'expired' else 1000}
    def execute(payload):
        counts['execute'] += 1
        dispatched.append({'type': type(payload['expected_sequence']).__name__,
                           'repr': repr(payload['expected_sequence'])})
        return {'status': 'completed', 'action_id': 'inert-1', 'effect_ref': 'effect-1',
                'release': {'verified': True, 'keys_down': [], 'buttons_down': []}}
    def verify(_):
        counts['verify'] += 1
        return {'status': 'succeeded', 'evidence_ref': 'frame1'}
    result = None
    exception = None
    try:
        receipt = module.run(specimen(), {'observe': observe, 'admit': admit, 'execute': execute,
                                         'verify_effect': verify, 'cancelled': lambda: False},
                             clock=lambda: 0)
        result = {k: receipt[k] for k in ('outcome', 'reason', 'completed_transitions')}
    except Exception as error:
        exception = {'type': type(error).__name__, 'message': str(error)}
    return {'case_id': f'{sequence}:{kind}:{profile}', 'sequence': sequence, 'kind': kind,
            'profile': profile, 'input_type': type(value).__name__, 'input_repr': repr(value),
            'counts': counts, 'dispatched': dispatched, 'result': result, 'exception': exception}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=('base', 'head'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.root / 'runtime/core_v1/compiled_gui.py'
    spec = importlib.util.spec_from_file_location('review_compiled', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = [run_case(module, *case) for case in itertools.product(SEQUENCES, KINDS, PROFILES)]
    raw = {'schema': 'pr6863-independent-boundary-v1', 'arm': args.arm,
           'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'rows': rows}
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(raw, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'arm': args.arm, 'rows': len(rows),
                      'execute_entries': sum(r['counts']['execute'] for r in rows),
                      'equality_calls': sum(r['counts']['equality'] for r in rows)}))

if __name__ == '__main__':
    main()
