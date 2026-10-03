"""Explicit-only reconstruction of exact evidence copies for ordinary checks."""
import dataclasses
import enum
import importlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
ARMS = ('baseline', 'observation_floor', 'authorization_floor')
GRANTS = (200, 400)
BEGINS = (0, 99, 100, 199, 200, 300, 399, 400, 1000)
H = 'a' * 64
_COPIES = {}


def canonical(value):
    if isinstance(value, enum.Enum):
        return value.value
    if dataclasses.is_dataclass(value):
        return {f.name: canonical(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, (tuple, list)):
        return [canonical(v) for v in value]
    if isinstance(value, frozenset):
        return sorted(canonical(v) for v in value)
    return value


def load_kernel(arm):
    if arm not in ARMS:
        raise ValueError('unknown arm')
    if arm in _COPIES:
        return _COPIES[arm]
    temp = tempfile.TemporaryDirectory(prefix='kernel-authority-order-')
    name = 'authority_order_' + arm
    destination = Path(temp.name) / name
    destination.mkdir()
    for path in (ROOT / 'source').glob('*.py.txt'):
        (destination / path.name[:-4]).write_bytes(path.read_bytes())
    if arm != 'baseline':
        (destination / 'lifecycle.py').write_bytes((ROOT / (arm + '_lifecycle.py.txt')).read_bytes())
    sys.path.insert(0, temp.name)
    module = importlib.import_module(name)
    module._owned_temporary_copy = temp
    _COPIES[arm] = module
    return module


def bound_flow(k):
    flow = k.RequestLifecycle()
    observation = k.Observation(7, 100, 'clock-surface', H, 10, 10, 'rgb')
    binding = k.TargetBinding('clock-target', 7, 'clock-surface', H)
    lease = k.AuthorityLease('clock-lease', 7, 'clock-surface', 1000,
                             frozenset({k.ActionKind.POINTER}))
    flow.record_observation(observation)
    flow.bind(binding)
    return flow, binding, lease


def authorized_flow(k, grant):
    flow, binding, lease = bound_flow(k)
    flow.authorize(lease, now_ns=grant)
    return flow, binding, lease


def request_for(k, binding, lease, matches=True):
    if not matches:
        binding = k.TargetBinding('other-target', 7, 'clock-surface', H)
    return k.ExecutionRequest('clock-command', H, binding, lease,
                              (k.Action('clock-action', k.ActionKind.POINTER, 'click'),))


def snapshot(flow):
    return {name: canonical(value) for name, value in vars(flow).items()}


def execute_matrix():
    rows = []
    for arm in ARMS:
        k = load_kernel(arm)
        for grant in GRANTS:
            for begin in BEGINS:
                for matches in (True, False):
                    flow, binding, lease = authorized_flow(k, grant)
                    req = request_for(k, binding, lease, matches)
                    before_objects, before = dict(vars(flow)), snapshot(flow)
                    accepted, error_type, error_message = False, None, None
                    try:
                        flow.begin_execution(req, now_ns=begin)
                        accepted = True
                    except k.ContractError as exc:
                        error_type, error_message = type(exc).__name__, str(exc)
                    after = snapshot(flow)
                    rows.append({'arm': arm, 'grant_ns': grant, 'begin_ns': begin,
                                 'request_matches': matches, 'before': before,
                                 'accepted': accepted, 'after': after,
                                 'error_type': error_type, 'error_message': error_message,
                                 'request_identity': flow.request is req if accepted else flow.request is before_objects['request'],
                                 'unchanged_on_refusal': None if accepted else all(vars(flow)[name] is value for name, value in before_objects.items()) and set(vars(flow)) == set(before_objects)})
    return {'schema': 'authority-begin-order-v1',
            'source_base': '2c0c1183b861519fde7c71462a589fb904c3451e', 'rows': rows}


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit('fixture.py takes no arguments; redirect to a NEW output')
    print(json.dumps(execute_matrix(), indent=2))
