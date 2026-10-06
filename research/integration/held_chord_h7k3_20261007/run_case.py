"""One private-Xvfb backend-method experiment; exclusive output, no retries."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import socket as sockets
import secrets
import signal
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'deps'))
from runtime.core_v1.contract import validate_program
from Xlib import X, display

CONDITIONS = ('NO_HOLD', 'SHIFT_SAME', 'SHIFT_ALIAS', 'CTRL_DISJOINT',
              'SHIFT_TEXT_UPPER', 'SHIFT_ALREADY_RELEASED')


def load_backend(path):
    spec = importlib.util.spec_from_file_location('tested_backend', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.X11Backend


def operations(condition):
    held = 'CTRL' if condition == 'CTRL_DISJOINT' else 'SHIFT'
    prefix = [] if condition == 'NO_HOLD' else [dict(op='key_state', key=held, down=True)]
    if condition == 'SHIFT_ALREADY_RELEASED':
        prefix.append(dict(op='key_state', key=held, down=False))
    action = (dict(op='text', text='A') if condition == 'SHIFT_TEXT_UPPER' else
              dict(op='key_chord', keys=['Shift_L' if condition == 'SHIFT_ALIAS' else 'SHIFT', 'a']))
    suffix = [dict(op='key_chord', keys=['b'])]
    if condition not in ('NO_HOLD', 'SHIFT_ALREADY_RELEASED'):
        suffix.append(dict(op='key_state', key=held, down=False))
    return prefix, action, suffix


def call(backend, op):
    if op['op'] == 'key_state':
        backend.key_state(op['key'], op['down'])
    elif op['op'] == 'key_chord':
        backend.key_chord(op['keys'])
    elif op['op'] == 'text':
        backend.text(op['text'])
    else:
        raise ValueError('unexpected experiment operation')


def run(condition, variant, output):
    output.mkdir(parents=True, exist_ok=False)
    record = dict(schema='h7k3-case-v1', condition=condition, variant=variant,
                  session='h7k3-' + secrets.token_hex(12),
                  started_ns=time.monotonic_ns(), authority='fixture-only',
                  task_success=None, route='backend_methods_not_public_dispatch',
                  argv=sys.argv, processes=[], steps=[])
    (output / 'START.json').write_text(json.dumps(record, indent=2))
    server = app = backend = observer = None
    old_auth = os.environ.get('XAUTHORITY')
    old_display = os.environ.get('DISPLAY')
    auth = output / 'private.Xauthority'
    streams = []
    failed = None
    try:
        number = secrets.randbelow(20000) + 3000
        socket = Path(f'/tmp/.X11-unix/X{number}')
        lock = Path(f'/tmp/.X{number}-lock')
        if socket.exists() or lock.exists():
            raise RuntimeError('chosen display already occupied')
        record['display'] = ':' + str(number)
        def field(b): return struct.pack('>H', len(b)) + b
        cookie = secrets.token_bytes(16)
        auth.write_bytes(struct.pack('>H', 256) + field(sockets.gethostname().encode()) + field(str(number).encode())
                         + field(b'MIT-MAGIC-COOKIE-1') + field(cookie))
        auth.chmod(0o600)
        os.environ['XAUTHORITY'] = str(auth)
        os.environ['DISPLAY'] = record['display']
        env = dict(os.environ)
        rd, wr = os.pipe()
        server_log = open(output / 'xvfb.stderr', 'xb'); streams.append(server_log)
        command = ['/usr/bin/Xvfb', record['display'], '-screen', '0', '640x480x24',
                   '-nolisten', 'tcp', '-auth', str(auth), '-noreset', '-displayfd', str(wr)]
        server = subprocess.Popen(command, pass_fds=(wr,), stdout=subprocess.DEVNULL,
                                  stderr=server_log, env=env)
        os.close(wr)
        try:
            if not select.select([rd], [], [], 8)[0]:
                raise TimeoutError('owned Xvfb did not become ready')
            ready = os.read(rd, 64)
        finally:
            os.close(rd)
        if ready.strip() != str(number).encode():
            raise RuntimeError('wrong Xvfb ready identity')
        record['server_ready'] = ready.decode('ascii')
        record['processes'].append(dict(role='xvfb', pid=server.pid, argv=command))
        err = open(output / 'app.stderr', 'xb'); streams.append(err)
        command = [sys.executable, '-u', '-B', str(ROOT / 'recipient.py'),
                   record['display'], str(output / 'app_events.jsonl')]
        app = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=err, env=env)
        wire = open(output / 'app_wire.jsonl', 'x', encoding='utf-8'); streams.append(wire)
        def read_reply():
            if not select.select([app.stdout], [], [], 5)[0]:
                raise TimeoutError('recipient reply unavailable')
            line = app.stdout.readline()
            wire.write(json.dumps(dict(direction='from_app', raw=line.decode('utf-8'))) + '\n')
            wire.flush()
            if not line: raise RuntimeError('recipient exited without reply')
            return json.loads(line)
        ready = read_reply()
        record['recipient_ready'] = ready
        record['processes'].append(dict(role='recipient', pid=app.pid, argv=command))
        source = ROOT / ('upstream/backend.py' if variant == 'current' else 'candidate/backend.py')
        data = source.read_bytes()
        record['backend_sha256'] = hashlib.sha256(data).hexdigest()
        backend = load_backend(source)(record['display'], {'fixture': ready['window']})
        observer = display.Display(record['display'])
        record['keycodes'] = {key: backend._keycode(key) for key in ('SHIFT', 'Shift_L', 'CTRL', 'a', 'b')}
        prefix, action, suffix = operations(condition)
        all_ops = [dict(op='focus', target='fixture'), *prefix, action, *suffix, dict(op='release_all')]
        program = dict(schema='agent-interface/program-v1', program_id=record['session'],
                       source=dict(observation_seq=1,binding_revision=1),
                       authority=dict(lease_id='fixture',expires_at_ns=time.monotonic_ns()+20_000_000_000),
                       terminal=dict(release_all_required=True),ops=all_ops)
        validate_program(program)
        record['program'] = program
        record['core_valid'] = True
        backend.focus('fixture')
        count = 0
        def snapshot(label):
            nonlocal count
            count += 1
            started = time.monotonic_ns()
            keymap = list(observer.query_keymap())
            ended = time.monotonic_ns()
            req = dict(kind='snapshot',id=count)
            raw = json.dumps(req) + '\n'
            wire.write(json.dumps(dict(direction='to_app', raw=raw)) + '\n'); wire.flush()
            app.stdin.write(raw.encode()); app.stdin.flush()
            reply = read_reply()
            if reply['id'] != count: raise RuntimeError('wrong recipient reply')
            row = dict(label=label, keymap=keymap, query_started_ns=started,
                       query_ended_ns=ended, held=dict(backend.held_keycodes),
                       app=reply, emissions=backend.emissions)
            record['steps'].append(row)
        snapshot('initial')
        for op in prefix: call(backend,op)
        snapshot('before_chord')
        call(backend,action)
        snapshot('after_chord')
        call(backend,suffix[0])
        snapshot('after_b')
        for op in suffix[1:]: call(backend,op)
        record['release'] = backend.release_all()
        snapshot('final')
        record['final_pointer_mask'] = int(observer.screen().root.query_pointer().mask)
        raw = json.dumps(dict(kind='stop',id=count+1)) + '\n'
        wire.write(json.dumps(dict(direction='to_app',raw=raw)) + '\n');wire.flush()
        app.stdin.write(raw.encode());app.stdin.flush()
        record['app_terminal'] = read_reply()
        app.stdin.close()
        app.wait(timeout=5)
    except Exception as exc:
        failed = repr(exc)
        record['error'] = failed
    finally:
        cleanup_errors = []
        if backend is not None:
            try: record['cleanup_release'] = backend.release_all()
            except Exception as exc: cleanup_errors.append(repr(exc))
            try: backend.close()
            except Exception as exc: cleanup_errors.append(repr(exc))
        if observer is not None:
            try: observer.close()
            except Exception as exc: cleanup_errors.append(repr(exc))
        for role,proc in [('recipient',app),('xvfb',server)]:
            if proc is not None:
                terminated = False
                if proc.poll() is None:
                    proc.terminate();terminated=True
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=5);cleanup_errors.append(role+' killed after timeout')
                record.setdefault('exits',[]).append(dict(role=role,pid=proc.pid,
                    returncode=proc.returncode,supervisor_terminate=terminated))
        for stream in streams: stream.close()
        if auth.exists(): auth.unlink()
        record['auth_removed'] = not auth.exists()
        if 'display' in record:
            n=record['display'][1:]
            record['display_socket_removed'] = not Path('/tmp/.X11-unix/X'+n).exists()
            record['display_lock_removed'] = not Path('/tmp/.X'+n+'-lock').exists()
        if old_auth is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=old_auth
        if old_display is None: os.environ.pop('DISPLAY',None)
        else: os.environ['DISPLAY']=old_display
        record['cleanup_errors']=cleanup_errors
        record['ended_ns']=time.monotonic_ns()
        (output/'record.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    if failed: raise RuntimeError(failed)
    return record


def main():
    def interrupted(signum, frame):
        raise InterruptedError('owned case terminated by supervisor')
    signal.signal(signal.SIGTERM, interrupted)
    p=argparse.ArgumentParser()
    p.add_argument('condition',choices=CONDITIONS)
    p.add_argument('variant',choices=('current','proposal'))
    p.add_argument('output',type=Path)
    p.add_argument('--require-preserved',action='store_true')
    a=p.parse_args()
    r=run(a.condition,a.variant,a.output.resolve())
    if a.require_preserved:
        code=r['keycodes']['SHIFT']; step=r['steps'][2]
        assert step['keymap'][code//8] & (1 << (code%8)), 'previous SHIFT hold was released by chord'
    print(json.dumps(dict(condition=a.condition,variant=a.variant,record=str(a.output/'record.json'))))

if __name__=='__main__':main()
