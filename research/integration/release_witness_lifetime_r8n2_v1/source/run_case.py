"""One fresh, bounded private-display case. Never resumes a consumed case."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import select
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path
from Xlib import X, display
from runtime.backends.x11_v1.backend import X11Backend

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ['LIVE_RELEASE', 'DESTROY_RELEASE', 'DESTROY_HELD', 'DESTROY_WITNESS_LOST']
SCHEDULE = [(rep, config, scenario) for rep in range(2) for config in ['bare', 'openbox'] for scenario in SCENARIOS]


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def one(index: int, destination: Path, formal: bool) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    rep, config, scenario = SCHEDULE[index]
    epoch, actuation = str(uuid.uuid4()), str(uuid.uuid4())
    raw = dict(index=index, repetition=rep, config=config, scenario=scenario, epoch=epoch,
               actuation=actuation, formal=formal, complete=False, processes=[], operations=[],
               source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted((ROOT / 'source').rglob('*.py'))})
    save(destination / 'CONSUMED.json', dict(index=index, epoch=epoch, started_ns=time.monotonic_ns()))
    if formal:
        freeze = json.loads((ROOT / 'FREEZE.json').read_text())
        for rel, expected in freeze['sha256'].items():
            if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected:
                raise RuntimeError('source-freeze mismatch: ' + rel)
    children: dict[str, subprocess.Popen] = {}
    handles = []
    backend = None
    q = None
    ipclog = (destination / 'driver.jsonl').open('x')
    private = destination / 'private'
    private.mkdir()
    auth = private / 'Xauthority'
    cookie = os.urandom(16)
    fields = [b'', b'', b'MIT-MAGIC-COOKIE-1', cookie]
    auth.write_bytes(struct.pack('>H', 65535) + b''.join(struct.pack('>H', len(x)) + x for x in fields))
    auth.chmod(0o600)
    env = {k: v for k, v in os.environ.items() if k not in ('DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY')}
    env.update(XAUTHORITY=str(auth), HOME=str(private), PYTHONDONTWRITEBYTECODE='1')

    def log(kind, **kw):
        row = dict(kind=kind, time_ns=time.monotonic_ns(), **kw)
        ipclog.write(json.dumps(row, sort_keys=True) + '\n')
        ipclog.flush()
        return row

    def spawn(name, command, **kw):
        err = (destination / (name + '.stderr')).open('wb')
        handles.append(err)
        p = subprocess.Popen(command, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=err, text=True, bufsize=1, **kw)
        children[name] = p
        raw['processes'].append(dict(name=name, pid=p.pid, command=command, returncode=None))
        return p

    def receive(name):
        p = children[name]
        if not select.select([p.stdout], [], [], 3)[0]:
            raise TimeoutError(name + ' response timeout')
        line = p.stdout.readline()
        if not line:
            raise RuntimeError(name + ' premature EOF')
        log('receive', actor=name, payload=line)
        return json.loads(line)

    def rpc(name, command, rid):
        message = json.dumps(dict(command=command, id=rid), sort_keys=True) + '\n'
        log('send', actor=name, payload=message)
        children[name].stdin.write(message)
        children[name].stdin.flush()
        return receive(name)

    def stop_actor(name):
        p = children[name]
        if p.poll() is None:
            rpc(name, 'exit', 'exit')
            p.wait(timeout=2)

    def state():
        start = time.monotonic_ns()
        keymap = list(q.query_keymap())
        mask = q.screen().root.query_pointer().mask
        return dict(start_ns=start, end_ns=time.monotonic_ns(), keymap=keymap,
                    pointer_mask=int(mask), key_down=bool(keymap[raw['keycode'] // 8] & (1 << (raw['keycode'] % 8))))

    def bounded_alarm(*_):
        raise TimeoutError('case soft bound exceeded')

    signal.signal(signal.SIGALRM, bounded_alarm)
    signal.alarm(15)
    try:
        readfd, writefd = os.pipe()
        spawn('xvfb', ['Xvfb', '-displayfd', str(writefd), '-screen', '0', '320x240x24',
                      '-nolisten', 'tcp', '-auth', str(auth), '-noreset'], pass_fds=(writefd,))
        os.close(writefd)
        buf = b''
        limit = time.monotonic() + 3
        while b'\n' not in buf:
            if not select.select([readfd], [], [], max(0, limit - time.monotonic()))[0]:
                raise TimeoutError('Xvfb display number missing')
            part = os.read(readfd, 64)
            if not part:
                raise RuntimeError('Xvfb display pipe EOF')
            buf += part
        os.close(readfd)
        env['DISPLAY'] = ':' + buf.decode().strip()
        raw['display'] = env['DISPLAY']
        fields = [socket.gethostname().encode(), buf.strip(), b'MIT-MAGIC-COOKIE-1', cookie]
        auth.write_bytes(struct.pack('>H', 256) + b''.join(struct.pack('>H', len(x)) + x for x in fields))
        if config == 'openbox':
            spawn('openbox', ['openbox', '--sm-disable'])
            time.sleep(0.2)
            if children['openbox'].poll() is not None:
                raise RuntimeError('Openbox failed')
        # Use the private cookie for this driver's explicitly named connection only.
        old_auth = os.environ.get('XAUTHORITY')
        os.environ['XAUTHORITY'] = str(auth)
        try:
            q = display.Display(env['DISPLAY'])
            for role in ('recipient', 'witness'):
                spawn(role, [sys.executable, '-B', str(ROOT / 'source/actors.py'), role,
                             str(destination), epoch, actuation])
                raw[role + '_ready'] = receive(role)
            wid = raw['recipient_ready']['window']
            raw['keycode'] = raw['witness_ready']['keycode']
            backend = X11Backend(env['DISPLAY'], {'fixture': wid})
        finally:
            if old_auth is None:
                os.environ.pop('XAUTHORITY', None)
            else:
                os.environ['XAUTHORITY'] = old_auth
        backend.d.change_keyboard_control(key=raw['keycode'], auto_repeat_mode=X.AutoRepeatModeOff)
        backend.d.sync()
        raw['map_readiness'] = []
        map_limit = time.monotonic() + 2
        while True:
            attrs = q.create_resource_object('window', wid).get_attributes()
            prop = q.screen().root.get_full_property(q.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
            listed = bool(prop is not None and wid in list(prop.value))
            raw['map_readiness'].append(dict(time_ns=time.monotonic_ns(), map_state=attrs.map_state, listed=listed))
            if attrs.map_state == X.IsViewable and (config == 'bare' or listed):
                break
            if time.monotonic() >= map_limit:
                raise TimeoutError('target mapping not ready')
            time.sleep(0.01)
        backend.focus('fixture')
        raw['before_input'] = state()
        assert not raw['before_input']['key_down']
        raw['operations'].append(log('key_down_request', key='F8'))
        backend.key_state('F8', True)
        raw['operations'].append(log('key_down_return', emissions=backend.emissions))
        raw['down'] = rpc('witness', 'sample', 'down')
        raw['app_down'] = rpc('recipient', 'snapshot', 'down_snapshot')
        assert raw['down']['key_down'] is True
        assert sum(e['event_type'] == X.KeyPress for e in raw['app_down']['events']) == 1
        if scenario != 'LIVE_RELEASE':
            raw['destroy'] = rpc('recipient', 'destroy', 'destroy')
            try:
                q.create_resource_object('window', wid).get_attributes()
                raw['target_exists_after_destroy'] = True
            except Exception as exc:
                raw['target_exists_after_destroy'] = False
                raw['destroy_probe_exception'] = type(exc).__name__
        if scenario == 'DESTROY_WITNESS_LOST':
            stop_actor('witness')
            raw['witness_closed_before_release'] = time.monotonic_ns()
        if scenario != 'DESTROY_HELD':
            raw['operations'].append(log('release_request'))
            raw['backend_release'] = backend.release_all()
            raw['operations'].append(log('release_return', emissions=backend.emissions))
        else:
            raw['operations'].append(log('release_withheld_until_measurement'))
        raw['post'] = None if scenario == 'DESTROY_WITNESS_LOST' else rpc('witness', 'sample', 'post')
        raw['app_post'] = rpc('recipient', 'snapshot', 'post_snapshot')
        raw['audit_measurement'] = state()
        raw['policy_request'] = dict(identity={k: raw['witness_ready'][k] for k in ('epoch', 'actuation', 'keycode', 'pid')},
            before=raw['down'], after=raw['post'], app_events=raw['app_post']['events'])
        raw['policy_request']['identity'].update(recipient_pid=raw['recipient_ready']['pid'], window=wid)
        cp = spawn('policy', [sys.executable, '-B', str(ROOT / 'source/policy.py')])
        policy_input = json.dumps(raw['policy_request'], sort_keys=True) + '\n'
        policy_out, _ = cp.communicate(policy_input, timeout=2)
        raw['policy_stdin'] = policy_input
        raw['policy_stdout'] = policy_out
        raw['policy_result'] = json.loads(policy_out)
        raw['policy_completed_ns'] = time.monotonic_ns()
        # A held-input negative control is measured first; cleanup is a different stage.
        raw['fixture_cleanup_started_ns'] = time.monotonic_ns()
        raw['fixture_cleanup_release'] = backend.release_all()
        raw['final_state'] = state()
        raw['complete'] = True
    except Exception as exc:
        raw['error'] = repr(exc)
    finally:
        signal.alarm(0)
        if backend is not None:
            try:
                backend.release_all()
                backend.close()
            except Exception as exc:
                raw['emergency_cleanup_error'] = repr(exc)
        if q is not None:
            q.close()
        for name in ('witness', 'recipient'):
            if name in children and children[name].poll() is None:
                try:
                    stop_actor(name)
                except Exception as exc:
                    raw.setdefault('cleanup_errors', []).append(repr(exc))
        for name, p in reversed(list(children.items())):
            if p.poll() is None:
                p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=2)
            next(r for r in raw['processes'] if r['name'] == name)['returncode'] = p.returncode
            for stream in (p.stdin, p.stdout):
                try:
                    stream.close()
                except Exception:
                    pass
        for h in handles:
            h.close()
        ipclog.close()
        # Authentication material is ephemeral, never part of retained evidence.
        auth.unlink(missing_ok=True)
        raw['ended_ns'] = time.monotonic_ns()
        save(destination / 'RAW.json', raw)
    print(json.dumps(dict(index=index, complete=raw['complete'], error=raw.get('error'),
                         policy=raw.get('policy_result')), sort_keys=True))
    if not raw['complete']:
        raise SystemExit(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('index', type=int, choices=range(16))
    parser.add_argument('out', type=Path)
    parser.add_argument('--formal', action='store_true')
    args = parser.parse_args()
    one(args.index, args.out.resolve(), args.formal)
