"""One-shot finite engineering matrix; never dispatches input or captures images."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source'))
from test_elapsed import fixture
from action_validity_admission_v1 import evaluate_action_validity

TOKENS = ['10', '10.0', '10.0000000005', '10.000000002', 'NaN',
          'Infinity', '-Infinity', 'null', 'true', '"10"', '[]', '{}']


def reject_constant(value):
    raise ValueError('nonstandard numeric constant: ' + value)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_check():
    freeze = json.loads((ROOT / 'FREEZE.json').read_text())
    for name, digest in freeze['sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('source changed: ' + name)
    return freeze


def run():
    freeze = source_check()
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    stream = output.open('x', encoding='utf-8')
    subjects = {'original': load(ROOT / 'source/doom_typed_observation_v1.py', 'old'),
                'candidate': load(ROOT / 'candidate/doom_typed_observation_v1.py', 'new')}
    rows = []
    for decoder in ('default', 'strict'):
        for age_ms in (50, 200):
            for token in TOKENS:
                event, contract, action = fixture()
                event['capture_to_typed_ready_ms'] = '__WIRE_TOKEN__'
                wire = json.dumps(event, sort_keys=True).replace('"__WIRE_TOKEN__"', token)
                row = {'ordinal': len(rows), 'decoder': decoder, 'age_ms': age_ms,
                       'token': token, 'wire': wire, 'input_sha256': hashlib.sha256(wire.encode()).hexdigest(),
                       'contract': contract, 'action': action, 'outcomes': {}}
                try:
                    packet = json.loads(wire, **({'parse_constant': reject_constant} if decoder == 'strict' else {}))
                    row['decode'] = 'accepted'
                except ValueError as exc:
                    row['decode'] = 'rejected'
                    row['decoder_error'] = type(exc).__name__
                    packet = None
                if packet is not None:
                    for name, module in subjects.items():
                        current = deepcopy(packet)
                        before = json.dumps(current, sort_keys=True)
                        try:
                            snapshot = module.build_action_snapshot(current, deepcopy(contract))
                            validity = evaluate_action_validity(action, contract, snapshot,
                                                               packet['capture_ns'] + age_ms * 1_000_000)
                            outcome = {'snapshot': 'accepted', 'value': snapshot,
                                       'validity_status': validity['status'],
                                       'grants_input_authority': validity['grants_input_authority']}
                        except ValueError as exc:
                            outcome = {'snapshot': 'rejected', 'error_type': type(exc).__name__,
                                       'error': str(exc)}
                        outcome['input_unchanged'] = json.dumps(current, sort_keys=True) == before
                        row['outcomes'][name] = outcome
                rows.append(row)
    source_check()
    raw = {'schema': 'typed-elapsed-matrix-a17-v1', 'allocation': 'a17-20261007-01',
           'source_sha256': freeze['sha256'], 'pid': os.getpid(), 'rows': rows}
    json.dump(raw, stream, sort_keys=True, indent=2, allow_nan=False)
    stream.write('\n'); stream.flush(); os.fsync(stream.fileno()); stream.close()
    print(json.dumps({'rows': len(rows), 'module_calls': sum(len(r['outcomes']) for r in rows),
                      'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, sort_keys=True))

if __name__ == '__main__':
    run()
