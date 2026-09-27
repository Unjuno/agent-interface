"""Four bounded, first-outcome private-X11 batches for Issue 4003."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import select
import subprocess as sp
import sys
import tempfile
import time
from backend_loader import load_backend, lock_clear

HERE = Path(__file__).resolve().parent
POLICIES = ['EXACT_BACKEND', 'PREFLIGHT_LOCK_GUARD', 'DISPATCH_LOCK_GUARD']
SCHEDULE = [(0, 0), (1, 1), (0, 1), (1, 0)]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def command(argv, env, records):
    start = time.monotonic_ns()
    p = sp.run(argv, env=env, capture_output=True, timeout=3)
    row = {'argv': argv, 'start_ns': start, 'end_ns': time.monotonic_ns(),
           'exit': p.returncode, 'stdout': p.stdout.decode(), 'stderr': p.stderr.decode()}
    records.append(row)
    if p.returncode:
        raise RuntimeError(row)
    return p.stdout.decode()


def read_line(p, records, request=None):
    if request is not None:
        sent = json.dumps(request, sort_keys=True) + '\n'
        p.stdin.write(sent.encode())
        p.stdin.flush()
    else:
        sent = None
    if not select.select([p.stdout], [], [], 3)[0]:
        raise TimeoutError('app response')
    raw = p.stdout.readline()
    records.append({'request': sent, 'response': raw.decode(), 'received_ns': time.monotonic_ns()})
    if not raw:
        raise RuntimeError('app stdout ended')
    return json.loads(raw)


class PrivateDisplay:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix='issue4003-')
        self.auth = Path(self.temp.name) / 'auth'
        cookie = secrets.token_hex(16)
        self.env = dict(os.environ, XAUTHORITY=str(self.auth), HOME=self.temp.name,
                        LC_ALL='C.UTF-8')
        sp.run(['xauth', '-f', str(self.auth), 'add', ':0', 'MIT-MAGIC-COOKIE-1', cookie],
               env=self.env, capture_output=True, check=True, timeout=3)
        r, w = os.pipe()
        self.argv = ['Xvfb', '-displayfd', str(w), '-auth', str(self.auth),
                     '-nolisten', 'tcp', '-noreset', '-screen', '0', '640x240x24']
        self.p = sp.Popen(self.argv, pass_fds=(w,), env=self.env, stdout=sp.PIPE, stderr=sp.PIPE)
        os.close(w)
        try:
            if not select.select([r], [], [], 3)[0]:
                raise TimeoutError('Xvfb readiness')
            self.display = ':' + os.read(r, 64).decode().strip()
            if not self.display[1:].isdigit():
                raise RuntimeError('invalid private display')
        except BaseException:
            self.p.terminate()
            self.p.communicate(timeout=3)
            self.temp.cleanup()
            raise
        finally:
            os.close(r)
        self.env['DISPLAY'] = self.display
        self.old_auth = os.environ.get('XAUTHORITY')
        os.environ['XAUTHORITY'] = str(self.auth)
        sp.run(['xauth', '-f', str(self.auth), 'add', self.display, 'MIT-MAGIC-COOKIE-1', cookie],
               env=self.env, capture_output=True, check=True, timeout=3)
        self.setup = []
        command(['setxkbmap', '-display', self.display, '-layout', 'us', '-option', ''], self.env, self.setup)
        command(['setxkbmap', '-display', self.display, '-query'], self.env, self.setup)

    def close(self):
        self.p.terminate()
        out, err = self.p.communicate(timeout=3)
        result = {'pid': self.p.pid, 'exit': self.p.returncode,
                  'stdout': out.decode(), 'stderr': err.decode(),
                  'socket_absent': not Path('/tmp/.X11-unix/X' + self.display[1:]).exists()}
        self.temp.cleanup()
        if self.old_auth is None:
            os.environ.pop('XAUTHORITY', None)
        else:
            os.environ['XAUTHORITY'] = self.old_auth
        return result


def run_case(server, before, after, policy, repetition, payload='aB2'):
    row = {'before': before, 'after': after, 'policy': policy, 'repetition': repetition,
           'payload': payload, 'native': [], 'app_wire': [], 'public_admission': False,
           'start_ns': time.monotonic_ns()}
    native = lambda mode: json.loads(command([str(HERE / 'lockctl'), server.display, str(mode)],
                                             server.env, row['native']))
    row['configured_pre'] = native(before)
    app = sp.Popen([sys.executable, '-B', str(HERE / 'app.py')], env=server.env,
                   stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, bufsize=0)
    row['app_pid'] = app.pid
    backend = None
    try:
        ready = read_line(app, row['app_wire'])
        row['ready'] = ready
        backend = load_backend()(server.display, {'entry': ready['entry']})
        backend.focus('entry')
        row['pre'] = native('query')
        program = {'ops': [{'op': 'focus', 'target': 'entry'}, {'op': 'text', 'text': payload},
                           {'op': 'release_all'}]}
        backend.preflight(program)
        row['preflight_plan'] = backend._text_plan(payload)
        row['preflight_mask'] = int(backend.root.query_pointer().mask)
        predecision = lock_clear(row['preflight_mask'])
        row['preflight_clear'] = predecision
        try:
            backend.preflight({'ops': [{'op': 'text', 'text': payload + '\u20ac'}]})
        except Exception as error:
            row['unsupported'] = {'error': repr(error), 'emissions': backend.emissions}
        else:
            raise AssertionError('unsupported character did not refuse')
        row['before_effect'] = read_line(app, row['app_wire'], {'op': 'snapshot'})
        row['configured_dispatch'] = native(after)
        row['dispatch_mask'] = int(backend.root.query_pointer().mask)
        if policy == 'EXACT_BACKEND':
            allowed = True
        elif policy == 'PREFLIGHT_LOCK_GUARD':
            allowed = predecision
        elif policy == 'DISPATCH_LOCK_GUARD':
            allowed = lock_clear(row['dispatch_mask'])
        else:
            raise ValueError('unknown policy')
        row['allowed'] = allowed
        row['decision_ns'] = time.monotonic_ns()
        row['program'] = program
        if allowed:
            row['execution'] = backend.execute(program)
            row['disposition'] = 'EXECUTED_NOT_SCORED_BY_BACKEND'
        else:
            row['execution'] = None
            row['release'] = backend.release_all()
            row['disposition'] = 'REFUSE_LOCKED_MODIFIER'
        row['backend_emissions'] = backend.emissions
        row['post'] = native('query')
        row['effect'] = read_line(app, row['app_wire'], {'op': 'snapshot'})
        row['terminal'] = read_line(app, row['app_wire'], {'op': 'finish'})
        out, err = app.communicate(timeout=3)
        row['app_exit'] = app.returncode
        row['app_stdout_tail'] = out.decode()
        row['app_stderr'] = err.decode()
        if app.returncode:
            raise RuntimeError('app exit')
    except BaseException as error:
        row['error'] = repr(error)
        if app.poll() is None:
            app.terminate()
        out, err = app.communicate(timeout=3)
        row.update(app_exit=app.returncode, app_stdout_tail=out.decode(), app_stderr=err.decode())
    finally:
        if backend is not None:
            row['finally_release'] = backend.release_all()
            backend.close()
        row['end_ns'] = time.monotonic_ns()
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--batch', type=int, choices=range(4))
    ap.add_argument('--construction', action='store_true')
    args = ap.parse_args()
    if args.construction == (args.batch is not None):
        ap.error('choose construction or batch')
    if not args.construction:
        frozen = json.loads((HERE / 'FREEZE.json').read_text())
        for name, expected in frozen['sources'].items():
            if digest(HERE / name) != expected:
                raise RuntimeError('source drift: ' + name)
        for earlier in range(args.batch):
            receipt = json.loads((args.out.parent / f'batch-{earlier}.exit.json').read_text())
            if receipt['returncode'] != 0 or receipt['timed_out']:
                raise RuntimeError('earlier batch did not complete')
    args.out.mkdir(parents=True, exist_ok=False)
    report = {'schema': 'x11-text-lock-state-v1', 'batch': args.batch,
              'construction': args.construction, 'pid': os.getpid(), 'rows': [],
              'started_ns': time.monotonic_ns(), 'source_backend': digest(HERE / 'source/backend.py')}
    server = None
    try:
        server = PrivateDisplay()
        report.update(display=server.display, server_pid=server.p.pid, setup=server.setup,
                      server_argv=[x if x != str(server.auth) else '<private-auth>' for x in server.argv])
        before, after = (0, 0) if args.construction else SCHEDULE[args.batch]
        reps = range(1) if args.construction else range(2)
        for rep in reps:
            order = POLICIES if rep == 0 else list(reversed(POLICIES))
            if args.construction:
                order = ['EXACT_BACKEND']
            for policy in order:
                row = run_case(server, before, after, policy, rep, 'cD3' if args.construction else 'aB2')
                report['rows'].append(row)
                save(args.out / f'row-{len(report["rows"]):02}.json', row)
                if 'error' in row:
                    raise RuntimeError(row['error'])
        report['lock_controls'] = []
        for mode in ('1', '0'):
            command([str(HERE / 'lockctl'), server.display, mode], server.env, report['lock_controls'])
        report['completed'] = True
    except BaseException as error:
        report['completed'] = False
        report['error'] = repr(error)
    finally:
        if server is not None:
            report['server_cleanup'] = server.close()
        report['finished_ns'] = time.monotonic_ns()
        save(args.out / 'raw.json', report)
    print(json.dumps({'rows': len(report['rows']), 'completed': report['completed'],
                      'raw_sha256': digest(args.out / 'raw.json')}), flush=True)
    return 0 if report['completed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
