"""Public dispatch + real guarded backend/release, with memory-only X doubles."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from Xlib import X
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.cli_v1.api import dispatch_in_session
from runtime.core_v1.contract import SCHEMA_PROGRAM
from runtime.guarded_x11_v1.bridge import _GuardedBackend

ROOT = Path(__file__).resolve().parents[3]


def run_case(mode):
    now = [1_000_000]
    deadline = 11_000_000
    entered, resume = threading.Event(), threading.Event()
    down, emissions, returned, failures = set(), [], [], []
    focus_calls = [0]

    def wait_boundary():
        entered.set()
        if not resume.wait(5):
            raise TimeoutError('harness did not unblock fake boundary')

    def focus():
        focus_calls[0] += 1
        if focus_calls[0] == 2 and mode == 'focus_query':
            wait_boundary()
        elif focus_calls[0] == 2 and mode == 'release_sync':
            now[0] = deadline
        return True

    def emit(_connection, kind, code):
        emissions.append({'kind': kind, 'code': code, 'clock_ns': now[0]})
        if kind == X.KeyPress:
            down.add(code)
        elif kind == X.KeyRelease:
            down.discard(code)
        else:
            raise AssertionError('unexpected task input')

    def sync():
        if mode == 'release_sync' and emissions and emissions[-1]['kind'] == X.KeyRelease:
            wait_boundary()

    def keymap():
        bitmap = bytearray(32)
        for code in down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bitmap

    backend = object.__new__(_GuardedBackend)
    backend.owner = SimpleNamespace(active=('field', [0, 0]), deadline=deadline,
                                    _focus_within_target=focus)
    backend.d = SimpleNamespace(sync=sync, query_keymap=keymap)
    backend.root = SimpleNamespace(query_pointer=lambda: SimpleNamespace(mask=0))
    backend.held_keycodes, backend.held_buttons, backend.emissions = {}, set(), 0
    backend._keycode = {'CTRL': 1, 'a': 2}.__getitem__
    backend._activation_supported = lambda: False
    backend.preflight = lambda _program: None
    backend._refresh_keyboard_mapping = lambda: False
    session = X11RuntimeSession(backend)
    program = {
        'schema': SCHEMA_PROGRAM, 'program_id': 'public-fake-' + mode,
        'source': {'observation_seq': 1, 'binding_revision': 1},
        'authority': {'lease_id': 'fake-only', 'expires_at_ns': deadline},
        'terminal': {'release_all_required': True},
        'ops': [{'op': 'key_chord', 'keys': ['CTRL', 'a']}, {'op': 'release_all'}],
    }

    def dispatch():
        try:
            returned.append(dispatch_in_session(session, program,
                current_observation_seq=1, current_binding_revision=1))
        except BaseException as error:
            failures.append(repr(error))

    with patch('time.monotonic_ns', side_effect=lambda: now[0]), \
            patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit), \
            patch('Xlib.display.Display', side_effect=AssertionError('real X connection forbidden')):
        worker = threading.Thread(target=dispatch, name='fake-public-dispatch')
        worker.start()
        try:
            if mode == 'healthy':
                worker.join(5)
                blocked = None
            else:
                if not entered.wait(5):
                    raise RuntimeError('named fake boundary was not reached: ' + repr(returned))
                now[0] = deadline
                blocked = {'fake_keys_down': sorted(down), 'dispatch_returned': bool(returned),
                           'worker_alive': worker.is_alive(), 'clock_ns': now[0],
                           'deadline_ns': deadline, 'emissions': list(emissions)}
        finally:
            resume.set()
            worker.join(5)
        if worker.is_alive() or failures or len(returned) != 1:
            raise RuntimeError('harness did not terminate cleanly: ' + repr(failures))
    return {'mode': mode, 'program': program, 'blocked': blocked,
            'final_fake_keys_down': sorted(down), 'emissions': emissions,
            'public_result': returned[0], 'worker_stopped': not worker.is_alive(),
            'session_recovery_required': session.recovery_required}


def freeze(path):
    if path.exists():
        raise FileExistsError(path)
    files = [*sorted(Path(__file__).parent.glob('*.py')),
             Path(__file__).parent / 'PLAN.md', *sorted((ROOT / 'runtime').rglob('*.py'))]
    source = {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in files}
    row = {'baseline': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
           'files': source, 'modes': ['healthy', 'focus_query', 'release_sync'],
           'fake_clock_start_ns': 1_000_000, 'deadline_ns': 11_000_000,
           'harness_wait_cap_s': 5, 'physical_time_bound_claimed': False,
           'preflight_and_observation_binding': 'stubbed; no fresh-target claim',
           'actual_paths': ['dispatch_in_session', 'X11RuntimeSession.dispatch',
                            '_GuardedBackend.key_state', 'X11Backend.execute', 'X11Backend.release_all'],
           'cancellation': 'No cancel method is invoked or simulated; expiry only.',
           'live_allocation_invocations': 0}
    path.write_bytes((json.dumps(row, indent=2) + '\n').encode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
        return
    if args.output is None or args.output.exists():
        parser.error('provide a fresh --output path')
    freeze_path = Path(__file__).parent / 'SOURCE_FREEZE.json'
    frozen = json.loads(freeze_path.read_bytes())
    for name, expected in frozen['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('source changed after freeze: ' + name)
    report = {'scope': 'FAKE_X_PUBLIC_PATH_CHARACTERIZATION', 'python': sys.version,
              'platform': platform.platform(), 'optimized': sys.flags.optimize,
              'freeze_sha256': hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
              'cases': [run_case(mode) for mode in ('healthy', 'focus_query', 'release_sync')],
              'real_x_connection': False, 'live_allocation_invocations': 0}
    args.output.write_bytes((json.dumps(report, indent=2) + '\n').encode())
    print('saved three Fake X cases to', args.output)


if __name__ == '__main__':
    main()
