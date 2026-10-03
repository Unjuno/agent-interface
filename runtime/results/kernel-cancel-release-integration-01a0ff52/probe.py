"""Explicit-only isolated construction: reconstruct immutable kernel copies."""
import importlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def load_kernel(candidate=False):
    name = 'cancel_integration_candidate' if candidate else 'cancel_integration_baseline'
    if name in sys.modules:
        return sys.modules[name]
    temp = tempfile.TemporaryDirectory(prefix='kernel-cancel-')
    directory = Path(temp.name) / name
    directory.mkdir()
    for source in (ROOT / 'source').glob('*.py.txt'):
        (directory / source.name[:-4]).write_bytes(source.read_bytes())
    if candidate:
        (directory / 'lifecycle.py').write_bytes((ROOT / 'candidate_lifecycle.py.txt').read_bytes())
    sys.path.insert(0, temp.name)
    module = importlib.import_module(name)
    module._temporary_directory = temp
    return module


def make_flow(k, state):
    f = k.RequestLifecycle()
    h = 'a' * 64
    obs = k.Observation(7, 100, 'surface', h, 10, 10, 'rgb')
    binding = k.TargetBinding('target', 7, 'surface', h)
    lease = k.AuthorityLease('lease', 7, 'surface', 1000, frozenset({k.ActionKind.KEY}))
    request = k.ExecutionRequest('command', h, binding, lease,
                                 (k.Action('key', k.ActionKind.KEY, 'A'),))
    if state == 'new':
        return f
    f.record_observation(obs)
    if state == 'observed':
        return f
    f.bind(binding)
    if state == 'bound':
        return f
    f.authorize(lease, now_ns=200)
    if state == 'authorized':
        return f
    if state == 'invalid_first_begin':
        try:
            f.begin_execution(request, now_ns=1000)
        except k.ContractError:
            return f
        raise AssertionError('expired begin unexpectedly accepted')
    f.begin_execution(request, now_ns=300)
    if state == 'begun':
        return f
    if state == 'duplicate_begin':
        try:
            f.begin_execution(request, now_ns=400)
        except k.ContractError:
            return f
        raise AssertionError('merged single-start guard missing')
    receipt = k.ExecutionReceipt('command', 'backend', h, 'lease', 7,
                                 'surface', 500, 700, 1,
                                 k.EffectOccurrence.POSSIBLE, k.ReleaseReceipt(800, True))
    f.record_execution(receipt)
    if state == 'executed':
        return f
    if state == 'stopped':
        f.stop('already_stopped')
        return f
    status = {'verified': k.EffectStatus.VERIFIED,
              'contradicted': k.EffectStatus.CONTRADICTED,
              'unavailable': k.EffectStatus.UNAVAILABLE}[state]
    f.record_effect(k.EffectReceipt('command', h, 900, status, h))
    return f


def release_for(k, kind, ns):
    if kind == 'missing':
        return None
    return k.ReleaseReceipt(ns, kind == 'empty', ('A',) if kind == 'held' else ())


def snapshot(flow):
    return {'stage': flow.stage.value,
            'command_id': flow.request.command_id if flow.request else None,
            'stop_reason': flow.stop_reason,
            'effect_status': flow.effect.status.value if flow.effect else None}


def run(mode):
    k = load_kernel(mode == 'candidate')
    spec = json.loads((ROOT / 'FREEZE.json').read_text())
    rows = []
    for state in spec['states']:
        for kind in spec['release_kinds']:
            for ns in ([None] if kind == 'missing' else spec['release_times_ns']):
                flow = make_flow(k, state)
                before = snapshot(flow)
                accepted, error, release_verified = False, None, None
                try:
                    flow.stop('cancelled', release=release_for(k, kind, ns))
                    accepted = True
                    release_verified = flow.outcome().release_verified
                except k.ContractError as exc:
                    error = str(exc)
                rows.append({'mode': mode, 'state': state, 'release_kind': kind,
                             'release_ns': ns, 'before': before, 'accepted': accepted,
                             'after': snapshot(flow), 'error': error,
                             'release_verified': release_verified})
    return rows


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('baseline', 'candidate'):
        raise SystemExit('usage: probe.py baseline|candidate')
    print(json.dumps(run(sys.argv[1]), indent=2))
