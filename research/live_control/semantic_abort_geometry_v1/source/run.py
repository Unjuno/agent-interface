"""Finite native experiment. Formal output is exclusive-create, never resumed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
POLICIES = ['RELEASE_ONLY', 'CACHED_OUTSIDE', 'FRESH_OUTSIDE']
SCENARIOS = ['STABLE', 'MOVE_BEFORE_REFRESH', 'MOVE_AFTER_REFRESH']
ESCAPE = [420, 140]
ALTERNATIVE = [30, 40]


def inside(point, box):
    x, y, w, h = box
    return x <= point[0] < x + w and y <= point[1] < y + h


def schedule():
    rows = []
    for rep in range(3):
        for scenario in SCENARIOS:
            for policy in POLICIES[rep:] + POLICIES[:rep]:
                rows.append({'case': len(rows), 'rep': rep, 'policy': policy, 'scenario': scenario})
        rows.append({'case': len(rows), 'rep': rep, 'policy': 'NO_INPUT', 'scenario': 'STABLE'})
    return rows


class Pipe:
    def __init__(self, argv, env, stderr, log):
        self.p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=stderr, env=env, bufsize=0)
        self.log = log
        self.buffer = b''
        self.counter = 0
        self.ready = None

    def read(self):
        deadline = time.monotonic() + 3
        while b'\n' not in self.buffer:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self.p.stdout], [], [], max(left, 0))[0]:
                raise TimeoutError('actor response deadline')
            chunk = os.read(self.p.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError('actor EOF')
            self.buffer += chunk
        line, self.buffer = self.buffer.split(b'\n', 1)
        obj = json.loads(line)
        self.log.append({'direction': 'response', 'actor': self.p.pid,
                         'ns': time.monotonic_ns(), 'raw': line.decode()})
        if 'error' in obj:
            raise RuntimeError(str(obj))
        return obj

    def call(self, op, **data):
        self.counter += 1
        req = {'id': self.counter, 'op': op, **data}
        raw = json.dumps(req, sort_keys=True)
        self.log.append({'direction': 'request', 'actor': self.p.pid,
                         'ns': time.monotonic_ns(), 'raw': raw})
        self.p.stdin.write((raw + '\n').encode())
        answer = self.read()
        if answer['id'] != self.counter:
            raise RuntimeError('response identity mismatch')
        return answer


def case_run(spec, out):
    from Xlib import X, display
    from Xlib.ext import xtest
    out.mkdir()
    row = {'spec': spec, 'steps': [], 'ipc': [], 'exits': {}, 'errors': []}
    env = {'PATH': os.environ['PATH'], 'HOME': str(out), 'PYTHONDONTWRITEBYTECODE': '1',
           'LC_ALL': 'C.UTF-8'}
    xvfb = app = obs = d = None
    previous_auth = os.environ.get('XAUTHORITY')
    auth_path = out / '.Xauthority'
    cookie = os.urandom(16)
    def write_auth(number):
        fields = [socket.gethostname().encode(), number.encode(), b'MIT-MAGIC-COOKIE-1', cookie]
        auth_path.write_bytes(struct.pack('>H', 256) + b''.join(struct.pack('>H', len(x)) + x for x in fields))
        auth_path.chmod(0o600)
    write_auth('0')
    env['XAUTHORITY'] = str(auth_path)
    handles = []
    def log_file(name):
        f = (out / name).open('xb')
        handles.append(f)
        return f
    def snap(label, state):
        observation = obs.call('observe', button=state['button'], marker=state['marker'])
        row['steps'].append({'label': label, 'app': state, 'observer': observation})
        return observation
    def native(kind, point=None):
        entry = {'kind': kind, 'point': point, 'ns': time.monotonic_ns()}
        row['steps'].append({'input': entry})
        if kind == 'motion':
            xtest.fake_input(d, X.MotionNotify, x=point[0], y=point[1])
        else:
            xtest.fake_input(d, X.ButtonPress if kind == 'press' else X.ButtonRelease, detail=1)
        d.sync()
    try:
        rd, wr = os.pipe()
        xvfb = subprocess.Popen(['Xvfb', '-displayfd', str(wr), '-screen', '0',
                                 '640x360x24', '-nolisten', 'tcp', '-noreset', '-auth', str(auth_path)],
                                pass_fds=(wr,), stdout=log_file('xvfb.stdout'),
                                stderr=log_file('xvfb.stderr'), env=env)
        os.close(wr)
        try:
            if not select.select([rd], [], [], 3)[0]:
                raise TimeoutError('Xvfb display allocation')
            display_name = ':' + os.read(rd, 32).decode().strip()
        finally:
            os.close(rd)
        env['DISPLAY'] = display_name
        write_auth(display_name[1:])
        os.environ['XAUTHORITY'] = str(auth_path)
        row['display'] = display_name
        row['xvfb_pid'] = xvfb.pid
        app = Pipe([sys.executable, str(HERE / 'actors.py'), 'fixture', str(out)],
                   env, log_file('app.stderr'), row['ipc'])
        app.ready = app.read()
        obs = Pipe([sys.executable, str(HERE / 'actors.py'), 'observer'],
                   env, log_file('observer.stderr'), row['ipc'])
        obs.ready = obs.read()
        row['actors'] = {'fixture': app.p.pid, 'observer': obs.p.pid}
        row['bindings'] = app.ready['bindings']
        if (HERE / 'ENVIRONMENT.json').exists():
            expected_bindings = json.loads((HERE / 'ENVIRONMENT.json').read_text())['bindings']
            if app.ready['bindings'] != expected_bindings:
                raise RuntimeError('Tk binding mismatch before input')
        state = app.ready['ready']
        initial = snap('initial', state)
        d = display.Display(display_name)
        if initial['mask'] & 0x1f00 or any(initial['keymap']):
            raise RuntimeError('non-neutral initial input')
        if spec['policy'] != 'NO_INPUT':
            native('motion', [150, 140])
            app.call('barrier')
            native('press')
            state = app.call('barrier', counts={'press': 1})['state']
            snap('pressed', state)
            if spec['scenario'] == 'MOVE_BEFORE_REFRESH':
                state = app.call('move')['state']
                snap('layout_change', state)
            state = app.call('barrier')['state']
            current = snap('refresh', state)
            if spec['policy'] == 'RELEASE_ONLY':
                point = None
            elif spec['policy'] == 'CACHED_OUTSIDE':
                point = list(ESCAPE)
            else:
                point = list(ALTERNATIVE if inside(ESCAPE, current['geometry']) else ESCAPE)
            row['decision'] = {'point': point, 'geometry_used': current['geometry']
                               if spec['policy'] == 'FRESH_OUTSIDE' else initial['geometry'],
                               'ns': time.monotonic_ns()}
            if spec['scenario'] == 'MOVE_AFTER_REFRESH':
                state = app.call('move')['state']
                snap('layout_change', state)
            if point is not None:
                native('motion', point)
                state = app.call('barrier')['state']
            snap('before_release', state)
            native('release')
            state = app.call('barrier', counts={'release': 1})['state']
        else:
            state = app.call('barrier')['state']
        terminal = snap('terminal', state)
        if terminal['mask'] & 0x1f00 or any(terminal['keymap']):
            raise RuntimeError('unverified release')
    except Exception as exc:
        row['errors'].append(type(exc).__name__ + ': ' + str(exc))
    finally:
        if d is not None:
            # On normal completion this does not inject another release.
            try:
                mask = d.screen().root.query_pointer().mask
                if mask & 0x100:
                    native('emergency_release')
                    row['errors'].append('emergency release required')
                row['final_mask'] = d.screen().root.query_pointer().mask
                row['final_keymap'] = list(d.query_keymap())
                d.close()
            except Exception as exc:
                row['errors'].append('cleanup: ' + repr(exc))
        for name, actor in [('fixture', app), ('observer', obs)]:
            if actor is not None:
                try:
                    actor.call('quit')
                    row['exits'][name] = actor.p.wait(timeout=3)
                except Exception as exc:
                    row['errors'].append(name + ' cleanup: ' + repr(exc))
                    actor.p.kill()
                    row['exits'][name] = actor.p.wait(timeout=3)
        if xvfb is not None:
            xvfb.terminate()
            try:
                row['exits']['xvfb'] = xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                row['exits']['xvfb'] = xvfb.wait(timeout=3)
                row['errors'].append('Xvfb required kill')
        for f in handles:
            f.close()
        if previous_auth is None:
            os.environ.pop('XAUTHORITY', None)
        else:
            os.environ['XAUTHORITY'] = previous_auth
        auth_path.unlink(missing_ok=True)
        (out / 'row.json').write_text(json.dumps(row, sort_keys=True, indent=2) + '\n')
    return row


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--construction', action='store_true')
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rows = schedule()
    if args.construction:
        rows = rows[:10]
    else:
        freeze = json.loads((HERE / 'FREEZE.json').read_text())
        if str(args.out.resolve()) != freeze['formal_output']:
            raise SystemExit('frozen output mismatch; formal not invoked')
        for name, digest in freeze['source_sha256'].items():
            if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
                raise SystemExit('source mismatch: ' + name)
    if not args.construction:
        environment = json.loads((HERE / 'ENVIRONMENT.json').read_text())
        for name, digest in environment['binary_or_library_sha256'].items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
                raise SystemExit('environment binary mismatch: ' + name)
    for spec in rows:
        row = case_run(spec, args.out / ('case-%02d' % spec['case']))
        print(json.dumps({'case': spec, 'errors': row['errors'],
                          'terminal': next((s['app']['counts'] for s in row['steps']
                                            if s.get('label') == 'terminal'), None)}), flush=True)
        if row['errors']:
            raise SystemExit(2)


if __name__ == '__main__':
    main()
