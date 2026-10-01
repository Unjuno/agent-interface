"""One-shot XTEST experiment; exclusive outputs and an allocation-owned Xvfb."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import select
import secrets
import subprocess
import sys
import time
from Xlib import X, display
from Xlib.ext import xtest

ROOT = Path(__file__).resolve().parent
RECIPES = ['COMPLETE', 'RELEASE_ONLY_CANCEL', 'MOVE_AWAY_CANCEL',
           'CAPABILITY_GATED_CANCEL', 'STALE_CAPABILITY_CANCEL']
BUTTON_MASK = X.Button1Mask | X.Button2Mask | X.Button3Mask | X.Button4Mask | X.Button5Mask


def write(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write('\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receive(proc, ipc, timeout=5):
    deadline = time.monotonic() + timeout
    buf = b''
    while time.monotonic() < deadline:
        if select.select([proc.stdout], [], [], max(0, deadline - time.monotonic()))[0]:
            b = os.read(proc.stdout.fileno(), 1)
            if not b:
                raise RuntimeError('application stdout closed')
            buf += b
            if b == b'\n':
                ipc.append({'direction': 'receive', 'mono_ns': time.monotonic_ns(),
                            'raw': buf.decode('utf-8')})
                return json.loads(buf)
    raise TimeoutError('application response deadline')


def command(proc, ipc, op):
    req = {'op': op, 'id': sum(x['direction'] == 'send' for x in ipc)}
    raw = json.dumps(req, sort_keys=True) + '\n'
    ipc.append({'direction': 'send', 'mono_ns': time.monotonic_ns(), 'raw': raw})
    proc.stdin.write(raw.encode())
    proc.stdin.flush()
    res = receive(proc, ipc)
    if res.get('request_id') != req['id']:
        raise RuntimeError('IPC identity mismatch')
    return res


def server_state(observer):
    observer.sync()
    pointer = observer.screen().root.query_pointer()
    keys = list(observer.query_keymap())
    return {'mono_ns': time.monotonic_ns(), 'button_mask': int(pointer.mask) & BUTTON_MASK,
            'pointer_mask': int(pointer.mask), 'keys': keys}


def admit(receipt, ready):
    expected = ready['receipt']
    bound = all(receipt.get(k) == expected[k] for k in
                ['session', 'epoch', 'widget_class', 'widget_xid', 'root_xid', 'recipe'])
    return (bound and type(receipt.get('epoch')) is int
            and receipt.get('abort_without_effect') is True
            and ready['kind'] == 'button' and receipt.get('widget_class') == 'TButton')


def run_case(out, dname, case_id, kind, recipe, rep):
    target = out / case_id
    target.mkdir()
    row = {'case_id': case_id, 'kind': kind, 'recipe': recipe, 'rep': rep,
           'input': [], 'ipc': [], 'errors': []}
    err = (target / 'app_stderr.txt').open('xb')
    proc = subprocess.Popen([sys.executable, str(ROOT / 'fixture.py'), '--kind', kind,
                             '--out', str(target), '--session', case_id],
                            env=dict(os.environ, DISPLAY=dname, PYTHONUNBUFFERED='1'),
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err)
    sender = observer = None
    held = False
    try:
        ready = receive(proc, row['ipc'])
        sender = display.Display(dname)
        observer = display.Display(dname)
        row['ready'] = ready
        if ready.get('event') != 'ready' or ready['session'] != case_id or ready['pid'] != proc.pid:
            raise RuntimeError('invalid app identity')
        if observer.create_resource_object('window', ready['receipt']['root_xid']).get_attributes().map_state != X.IsViewable:
            raise RuntimeError('not viewable')
        if kind == 'scale' and ready.get('identified_part') != 'trough2':
            raise RuntimeError('scale target is not the increasing trough')
        row['initial_server'] = server_state(observer)
        if row['initial_server']['button_mask'] or any(row['initial_server']['keys']):
            raise RuntimeError('nonneutral initial server')
        row['initial'] = command(proc, row['ipc'], 'snapshot')
        if row['initial']['effect_count'] != 0 or row['initial']['value'] != 0:
            raise RuntimeError('nonzero application baseline')
        receipt = copy.deepcopy(ready['receipt'])
        if recipe == 'STALE_CAPABILITY_CANCEL':
            receipt['epoch'] = 0
        row['candidate_receipt'] = receipt
        allowed = admit(receipt, ready) if recipe in RECIPES[3:] else True
        row['admitted'] = allowed

        def emit(name, point=None):
            nonlocal held
            row['input'].append({'op': name, 'point': point, 'mono_ns': time.monotonic_ns()})
            if name == 'motion':
                xtest.fake_input(sender, X.MotionNotify, x=point[0], y=point[1])
            elif name == 'press':
                xtest.fake_input(sender, X.ButtonPress, detail=1)
                held = True
            elif name == 'release':
                xtest.fake_input(sender, X.ButtonRelease, detail=1)
                held = False
            sender.sync()

        if allowed:
            emit('motion', ready['point'])
            command(proc, row['ipc'], 'snapshot')
            emit('press')
            row['pressed_server'] = server_state(observer)
            deadline = time.monotonic() + 1
            while True:
                snap = command(proc, row['ipc'], 'snapshot')
                if snap['presses'] == 1:
                    row['post_press'] = snap
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError('app did not observe press')
            if recipe in ['MOVE_AWAY_CANCEL', 'CAPABILITY_GATED_CANCEL']:
                emit('motion', ready['away'])
                row['post_move'] = command(proc, row['ipc'], 'snapshot')
            emit('release')
        row['terminal'] = command(proc, row['ipc'], 'snapshot')
        row['final_server'] = server_state(observer)
        if row['final_server']['button_mask'] or any(row['final_server']['keys']):
            raise RuntimeError('unverified neutral release')
    except Exception as exc:
        row['errors'].append(type(exc).__name__ + ': ' + str(exc))
    finally:
        if sender is not None and held:
            row['input'].append({'op': 'emergency_release', 'point': None,
                                 'mono_ns': time.monotonic_ns()})
            xtest.fake_input(sender, X.ButtonRelease, detail=1)
            sender.sync()
        if observer is not None:
            row['cleanup_server'] = server_state(observer)
        try:
            if proc.poll() is None:
                row['closing'] = command(proc, row['ipc'], 'close')
            row['app_returncode'] = proc.wait(timeout=3)
        except Exception as exc:
            row['errors'].append('cleanup: ' + type(exc).__name__ + ': ' + str(exc))
            proc.kill()
            row['app_returncode'] = proc.wait(timeout=3)
        for con in [sender, observer]:
            if con is not None:
                con.close()
        err.close()
        if (target / 'app_stderr.txt').stat().st_size:
            row['errors'].append('application stderr is not empty')
        write(target / 'row.json', row)
    return row


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['construction', 'formal'], required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'formal':
        freeze = json.loads((ROOT / 'FREEZE.json').read_text())
        for name, value in freeze['sources'].items():
            if digest(ROOT / name) != value:
                raise RuntimeError('STOP_SOURCE_MISMATCH: ' + name)
        environment = json.loads((ROOT / 'ENVIRONMENT.json').read_text())
        for name, value in environment['files'].items():
            if digest(Path(name)) != value:
                raise RuntimeError('STOP_ENVIRONMENT_MISMATCH: ' + name)
    a.out.mkdir(parents=True, exist_ok=False)
    auth = a.out.resolve() / 'Xauthority'
    auth.touch(mode=0o600)
    cookie = secrets.token_hex(16)
    subprocess.run(['/usr/bin/xauth', '-f', str(auth), 'add', ':12345', '.', cookie], check=True, timeout=3)
    os.environ['XAUTHORITY'] = str(auth)
    rfd, wfd = os.pipe()
    xlog = (a.out / 'xvfb_stderr.txt').open('xb')
    xvfb = subprocess.Popen(['/usr/bin/Xvfb', '-displayfd', str(wfd), '-screen', '0',
                             '640x360x24', '-nolisten', 'tcp', '-noreset', '-auth', str(auth)],
                            pass_fds=[wfd], stdout=subprocess.DEVNULL, stderr=xlog)
    os.close(wfd)
    summary = {'mode': a.mode, 'rows': [], 'errors': [], 'xvfb_pid': xvfb.pid}
    try:
        if not select.select([rfd], [], [], 5)[0]:
            raise TimeoutError('private Xvfb did not become ready')
        number = os.read(rfd, 128).decode().strip()
        if not number.isdigit():
            raise RuntimeError('invalid Xvfb display allocation')
        dname = ':' + number
        subprocess.run(['/usr/bin/xauth', '-f', str(auth), 'add', dname, '.', cookie], check=True, timeout=3)
        summary['display'] = dname
        schedule = ([(0, k, s) for k in ['button', 'scale'] for s in ['COMPLETE', 'MOVE_AWAY_CANCEL']]
                    if a.mode == 'construction' else
                    [(r, k, s) for r in range(3) for k in ['button', 'scale'] for s in RECIPES])
        for index, (rep, kind, recipe) in enumerate(schedule):
            cid = f'{a.mode}-{index:02d}-{kind}-{recipe.lower()}'
            row = run_case(a.out, dname, cid, kind, recipe, rep)
            summary['rows'].append(cid)
            if row['errors'] or row['app_returncode'] != 0:
                raise RuntimeError('STOP_CASE: ' + cid)
    except Exception as exc:
        summary['errors'].append(type(exc).__name__ + ': ' + str(exc))
    finally:
        os.close(rfd)
        xvfb.terminate()
        try:
            summary['xvfb_returncode'] = xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill()
            summary['xvfb_returncode'] = xvfb.wait(timeout=3)
            summary['errors'].append('Xvfb required kill')
        xlog.close()
        auth.unlink()
        summary['xvfb_reaped'] = xvfb.poll() is not None
        write(a.out / 'run.json', summary)
        manifest = {str(x.relative_to(a.out)): digest(x) for x in sorted(a.out.rglob('*')) if x.is_file()}
        write(a.out / 'MANIFEST.json', manifest)
    print(json.dumps(summary, sort_keys=True))
    return 1 if summary['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
