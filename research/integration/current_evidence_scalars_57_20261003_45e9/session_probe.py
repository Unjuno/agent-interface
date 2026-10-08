"""Exercise exact production session code with an input-free recording backend.

Native backend imports are replaced by a private module. Session source is not
transformed; no native backend object, display, device or input API is opened.
"""
import hashlib
import importlib.util
import json
import platform
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from runtime.core_v1.contract import capability_manifest, KNOWN_CAPABILITIES


class RecordingBackend:
    def __init__(self, clock):
        self.clock = clock
        self.emissions = 0
        self.calls = []

    def manifest(self):
        return capability_manifest('test-only', 'linux', 'no-device', KNOWN_CAPABILITIES)

    def monotonic_ns(self):
        self.calls.append('clock')
        return self.clock

    def preflight(self, program):
        self.calls.append('preflight')

    def execute(self, program):
        self.calls.append('execute')
        self.emissions += 1  # logical spy count, not physical input
        return {'releases': [{'verified': True, 'keys_down': [], 'buttons_down': []}]}

    def release_all(self):
        self.calls.append('release_all')
        return {'verified': True, 'keys_down': [], 'buttons_down': []}


def load_session(route, names):
    package_name = f'_scalar_probe_{route}'
    package = types.ModuleType(package_name)
    package.__path__ = []
    sys.modules[package_name] = package
    backend = types.ModuleType(package_name + '.backend')
    for name in names:
        setattr(backend, name, RecordingBackend if name.endswith('Backend') else type(name, (Exception,), {}))
    sys.modules[backend.__name__] = backend
    path = ROOT / 'runtime/backends' / route / 'session.py'
    spec = importlib.util.spec_from_file_location(package_name + '.session', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    session_name = {'win32_v1': 'Win32RuntimeSession', 'x11_v1': 'X11RuntimeSession',
                    'quartz_v1': 'QuartzRuntimeSession'}[route]
    return getattr(module, session_name), hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    routes = [('win32_v1', ('Win32Backend', 'Win32BackendError')),
              ('x11_v1', ('X11Backend', 'X11BackendError', 'X11ExecutionError')),
              ('quartz_v1', ('QuartzBackend', 'QuartzBackendError'))]
    cases = [('valid', 99, {}), ('expired', 101, {}), ('nan_clock', float('nan'), {}),
             ('negative_clock', -1, {}), ('bool_clock', True, {}),
             ('bool_sequence', 99, {'current_observation_seq': True}),
             ('float_revision', 99, {'current_binding_revision': 1.0})]
    rows, sources = [], {}
    for route, names in routes:
        session_type, sources[route] = load_session(route, names)
        for label, clock, changes in cases:
            backend = RecordingBackend(clock)
            session = session_type(backend)
            program = {'schema': 'agent-interface/program-v1', 'program_id': 'spy-test',
                       'source': {'observation_seq': 1, 'binding_revision': 1},
                       'authority': {'lease_id': 'test-only', 'expires_at_ns': 100},
                       'terminal': {'release_all_required': True}, 'ops': [{'op': 'release_all'}]}
            args = dict(current_observation_seq=1, current_binding_revision=1)
            args.update(changes)
            result = session.dispatch(program, **args)
            rows.append(dict(route=route, case=label, status=result['status'],
                             error=result.get('error'), calls=backend.calls,
                             spy_execution_count=backend.emissions))
    return {'scope': 'host engineering integration check with recording backend; no native effect',
            'python': sys.version, 'platform': platform.platform(),
            'session_source_sha256': sources,
            'core_sha256': hashlib.sha256((ROOT / 'runtime/core_v1/contract.py').read_bytes()).hexdigest(),
            'rows': rows}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, allow_nan=False))
