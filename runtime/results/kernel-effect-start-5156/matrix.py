"""Ordinary construction comparison over exact inert source snapshots."""
from dataclasses import asdict, is_dataclass
from enum import Enum
import hashlib
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def load_package(name, directory):
    spec = spec_from_loader(name, loader=None, is_package=True)
    package = module_from_spec(spec)
    package.__path__ = [str(directory)]
    sys.modules[name] = package
    for part in ('contracts', 'backend', 'lifecycle'):
        fullname = name + '.' + part
        loader = SourceFileLoader(fullname, str(directory / (part + '.py.txt')))
        module = module_from_spec(spec_from_loader(fullname, loader))
        sys.modules[fullname] = module
        loader.exec_module(module)
    SourceFileLoader(name, str(directory / '__init__.py.txt')).exec_module(package)
    return package


def normalize(value):
    if isinstance(value, Enum): return value.value
    if is_dataclass(value): return normalize(asdict(value))
    if isinstance(value, dict): return {k: normalize(v) for k,v in value.items()}
    if isinstance(value, (tuple, list)): return [normalize(v) for v in value]
    if isinstance(value, frozenset): return sorted(normalize(v) for v in value)
    if value is None or type(value) in (str, bool, int): return value
    raise TypeError(type(value))


def make_flow(k, fixture):
    f = fixture['before']
    flow = k.RequestLifecycle()
    observation = k.Observation(**f['observation'])
    binding = k.TargetBinding(**f['binding'])
    lease_fields = dict(f['lease'])
    lease_fields['allowed_actions'] = frozenset(k.ActionKind(v) for v in lease_fields['allowed_actions'])
    lease = k.AuthorityLease(**lease_fields)
    action = k.Action('action', k.ActionKind.KEY, 'press-release')
    request = k.ExecutionRequest('command', 'b' * 64, binding, lease, (action,))
    flow.record_observation(observation)
    flow.bind(binding)
    flow.authorize(lease, now_ns=200)
    flow.begin_execution(request, now_ns=400)
    flow.record_execution(k.ExecutionReceipt(
        'command', 'backend', 'b' * 64, 'lease', 7, 'surface', 600, 800, 1,
        k.EffectOccurrence.OBSERVED, k.ReleaseReceipt(900, True),
    ))
    return flow


def main():
    target = HERE / 'raw.json'
    if target.exists(): raise FileExistsError('ordinary matrix already retained')
    freeze = json.loads((HERE / 'MATRIX_FREEZE.json').read_bytes())
    for name, digest in freeze['inputs_sha256'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
            raise ValueError(('input changed', name))
    fixture = json.loads((HERE / 'fixture.json').read_bytes())
    rows = []
    for arm, relative in [('baseline', 'retained/kernel'), ('candidate', 'retained/candidate-kernel')]:
        k = load_package('_effect_start_' + arm, HERE / relative)
        for status in fixture['statuses']:
            for observed_ns in fixture['effect_times_ns']:
                for identity in fixture['identities']:
                    flow = make_flow(k, fixture)
                    before = normalize(vars(flow))
                    receipt = k.EffectReceipt(
                        'other' if identity == 'wrong_command' else 'command',
                        'a' * 64 if identity == 'wrong_manifest' else 'b' * 64,
                        observed_ns, k.EffectStatus(status), 'd' * 64,
                    )
                    error = None
                    try:
                        flow.record_effect(receipt)
                        accepted = True
                    except k.ContractError as e:
                        accepted = False
                        error = str(e)
                    after = normalize(vars(flow))
                    outcome = normalize(flow.outcome()) if accepted else None
                    rows.append({'arm': arm, 'status': status, 'observed_ns': observed_ns,
                                 'identity': identity, 'attempt': normalize(receipt),
                                 'before': before, 'accepted': accepted, 'error': error,
                                 'after': after, 'outcome': outcome})
    data = {'schema': 'kernel-effect-start-ordinary-v1', 'id': freeze['id'],
            'source_sha256': freeze['source_sha256'], 'rows': rows}
    with target.open('x', encoding='utf8', newline='\n') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print(json.dumps({'rows': len(rows), 'arms': ['baseline', 'candidate']}))


if __name__ == '__main__': main()
