"""Run real V12/V15 source selection and stop before session construction."""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import threading
import types
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('route', choices=('v12-perkey', 'v15-default', 'v15-perkey'))
    args = parser.parse_args()
    source = args.source.resolve()
    args.output.mkdir(exist_ok=False, parents=True)
    sys.path.insert(0, str(source))
    for directory in ('observation_tiles', 'observation_gating', 'live_control', 'doom'):
        sys.path.insert(0, str(source / 'research' / directory))
    forbidden = []
    def refuse(*unused_args, **unused_kwargs):
        forbidden.append('native/process/thread construction attempted')
        raise AssertionError(forbidden[-1])
    xlib = types.ModuleType('Xlib')
    xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
        ButtonRelease=5, Button1Mask=256, AnyPropertyType=0, IsViewable=2)
    xlib.XK = types.SimpleNamespace(string_to_keysym=refuse)
    xlib.error = types.SimpleNamespace(BadWindow=type('BadWindow', (Exception,), {}),
        BadDrawable=type('BadDrawable', (Exception,), {}))
    xlib.display = types.ModuleType('Xlib.display')
    xlib.display.Display = refuse
    ext = types.ModuleType('Xlib.ext')
    ext.xtest = types.ModuleType('Xlib.ext.xtest')
    ext.xtest.fake_input = refuse
    vd = types.ModuleType('vizdoom')
    vd.DoomGame = refuse
    vd.GameVariable = types.SimpleNamespace()
    sys.modules.update({'Xlib': xlib, 'Xlib.display': xlib.display,
        'Xlib.ext': ext, 'Xlib.ext.xtest': ext.xtest, 'vizdoom': vd})
    observed = {}
    class BoundaryReached(Exception):
        pass
    def session_boundary():
        # The caller is the unchanged base.main(), after its backend selection.
        state = inspect.currentframe().f_back.f_locals
        backend = state['selected_backend']
        globals_ = backend.__init__.__globals__
        owner = globals_['InputOwner']
        owner_path = Path(inspect.getfile(owner)).resolve()
        bridge = state.get('bridge_module')
        expected_owner = source / 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py'
        observed.update({
            'route': args.route,
            'backend_name': backend.__qualname__,
            'backend_module': backend.__module__,
            'backend_file': str(Path(inspect.getfile(backend)).relative_to(source)) if bridge is None else str(Path(bridge.__file__).relative_to(source)),
            'owner_module': owner.__module__,
            'owner_file': str(owner_path.relative_to(source)),
            'owner_sha256': hashlib.sha256(owner_path.read_bytes()).hexdigest(),
            'expected_a01_owner_file': str(expected_owner.relative_to(source)),
            'expected_a01_owner_sha256': hashlib.sha256(expected_owner.read_bytes()).hexdigest(),
            'owner_matches_a01': owner_path == expected_owner,
            'owner_has_a01_classifier': hasattr(owner, '_run') and '_classify_press' in owner._run.__globals__,
            'cached_owner_file': str(Path(sys.modules['input_owner_v12'].__file__).relative_to(source)) if 'input_owner_v12' in sys.modules else None,
            'source_selection_finished': True,
            'session_started': False,
            'owner_instantiated': False,
        })
        raise BoundaryReached()
    with patch.object(subprocess, 'Popen', refuse), patch.object(threading.Thread, 'start', refuse):
        import session_map01_v12 as base
        base.suite.Session = session_boundary
        output = args.output / 'runtime'
        sys.argv = ['session_map01_' + ('v12.py' if args.route.startswith('v12') else 'v15.py'), '--out', str(output), '--seed', '17']
        if args.route.endswith('perkey'):
            sys.argv.append('--per-key-input-measurement')
        try:
            if args.route.startswith('v15'):
                import session_map01_v15
                session_map01_v15.main()
            else:
                base.main()
        except BoundaryReached:
            pass
        else:
            raise AssertionError('session construction boundary was not reached')
    manifest = json.loads((output / 'sources.json').read_text())
    expected_key = observed['expected_a01_owner_file'].removeprefix('research/')
    observed['recorded_a01_owner_sha256'] = manifest.get(expected_key)
    observed['forbidden_calls'] = forbidden
    observed['actual_import_files'] = {
        name: str(Path(module.__file__).resolve().relative_to(source))
        for name, module in tuple(sys.modules.items())
        if getattr(module, '__file__', None) and Path(module.__file__).resolve().is_relative_to(source)
    }
    (args.output / 'result.json').write_text(json.dumps(observed, indent=2, sort_keys=True) + '\n')
    print(json.dumps(observed, sort_keys=True))


if __name__ == '__main__':
    main()
