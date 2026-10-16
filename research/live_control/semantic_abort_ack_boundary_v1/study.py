"""Issue 3930: live application-ack ordering, never a production input backend."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import struct
import socket
import sys
import time
import uuid
import traceback

HERE = Path(__file__).resolve().parent
SCENARIOS = ['complete', 'applied', 'request_only', 'timeout', 'unsupported', 'stale_receipt']


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def line_read(fd, timeout=4):
    """Unbuffered, bounded one-line pipe reader; retain bytes in caller."""
    end, data = time.monotonic() + timeout, bytearray()
    while b'\n' not in data:
        left = end - time.monotonic()
        if left <= 0 or not select.select([fd], [], [], max(0, left))[0]:
            raise TimeoutError('pipe response deadline')
        b = os.read(fd, 1)
        if not b:
            raise EOFError('pipe closed before LF')
        data.extend(b)
        if len(data) > 65536:
            raise ValueError('response bound exceeded')
    return bytes(data)


def proof_matches(ready, receipt):
    return (isinstance(receipt, dict) and receipt.get('kind') == 'cancel_applied'
            and all(receipt.get(k) == ready[k] for k in ('session', 'case', 'action'))
            and type(receipt.get('at_ns')) is int and receipt['at_ns'] > 0
            and receipt.get('nonce') == ready['action'] + ':cancel')


def receiver(case, scenario, journal_path):
    import tkinter as tk
    root = tk.Tk()
    root.geometry('600x300+20+20')
    root.title('3930 isolated disposable effect')
    journal = open(journal_path, 'x', encoding='utf-8')
    session = str(uuid.uuid4())
    action = case + ':button1'
    state = {'presses': 0, 'releases': 0, 'enters': 0, 'callbacks': 0,
             'pending': False, 'applied': False, 'nonce': None}
    seq = 0

    def emit(kind, **fields):
        nonlocal seq
        seq += 1
        row = dict(seq=seq, kind=kind, at_ns=time.monotonic_ns(), session=session,
                   case=case, action=action, pid=os.getpid(), **fields)
        journal.write(json.dumps(row, sort_keys=True) + '\n')
        journal.flush()
        return row

    marker = tk.Frame(root, background='#000000')
    marker.place(x=400, y=100, width=32, height=32)

    def commit():
        state['callbacks'] += 1
        marker.configure(background='#ffffff')
        emit('callback', count=state['callbacks'])

    button = tk.Button(root, text='Commit private effect', command=commit)
    button.place(x=60, y=70, width=240, height=80)

    def record(kind):
        state[kind] += 1
        emit(kind, count=state[kind])
        # Returning None keeps the existing Button class binding unmodified.

    button.bind('<Enter>', lambda e: record('enters'), add='+')
    button.bind('<ButtonPress-1>', lambda e: record('presses'), add='+')
    button.bind('<ButtonRelease-1>', lambda e: record('releases'), add='+')
    root.update()
    ready = dict(kind='ready', session=session, case=case, action=action,
                 pid=os.getpid(), root_xid=root.winfo_id(), button_xid=button.winfo_id(),
                 point=[button.winfo_rootx()+120, button.winfo_rooty()+40],
                 roi=[marker.winfo_rootx()+8, marker.winfo_rooty()+8, 8, 8],
                 can_abort=scenario != 'unsupported', tk=root.tk.call('info', 'patchlevel'),
                 tk_package=root.tk.call('package', 'provide', 'Tk'),
                 button_release_binding=root.bind_class('Button', '<ButtonRelease-1>'),
                 bindtags=list(button.bindtags()))
    emit('ready', metadata=ready)
    print(json.dumps(ready, sort_keys=True), flush=True)
    buf = bytearray()

    def readable(fd, mask):
        nonlocal buf
        chunk = os.read(fd, 65536)
        if not chunk:
            root.destroy()
            return
        buf.extend(chunk)
        if len(buf) > 65536:
            raise ValueError('request buffer bound')
        while b'\n' in buf:
            raw, _, rest = buf.partition(b'\n')
            buf = bytearray(rest)
            req = json.loads(raw)
            emit('request', request=req)
            op = req['op']
            if op == 'snapshot':
                root.update_idletasks()
                out = dict(kind='snapshot', state=dict(state), button_state=str(button['state']))
            elif op == 'cancel_request':
                if not ready['can_abort'] or req['nonce'] != action + ':cancel':
                    raise ValueError('unadmitted cancellation request')
                state['pending'], state['nonce'] = True, req['nonce']
                out = emit('cancel_received', nonce=state['nonce'])
            elif op == 'apply_cancel':
                if not state['pending'] or req['nonce'] != state['nonce']:
                    raise ValueError('no matching pending cancel')
                # Application-specific abort; not a generic Tk cancellation API.
                button.configure(state='disabled')
                root.update_idletasks()
                state['pending'], state['applied'] = False, True
                out = emit('cancel_applied', nonce=state['nonce'])
            elif op == 'close':
                out = emit('close', state=dict(state))
            else:
                raise ValueError('unknown operation')
            out = dict(out, rpc_id=req['rpc_id'])
            print(json.dumps(out, sort_keys=True), flush=True)
            if op == 'close':
                root.destroy()
                return

    root.createfilehandler(sys.stdin.fileno(), tk.READABLE, readable)
    try:
        root.mainloop()
    finally:
        journal.close()


def one_case(folder, case, scenario, old_receipt):
    from Xlib import X, display
    from Xlib.ext import xtest
    folder.mkdir()
    trace, row = [], dict(case=case, scenario=scenario)
    server = app = motor = observer = None
    down = False
    sf = open(folder/'xvfb.stderr', 'wb')
    af = open(folder/'app.stderr', 'wb')

    def log(kind, **kw):
        trace.append(dict(kind=kind, at_ns=time.monotonic_ns(), **kw))

    def physical(label):
        p = observer.screen().root.query_pointer()
        keymap = list(observer.query_keymap())
        rec = dict(label=label, at_ns=time.monotonic_ns(), mask=p.mask,
                   keys=keymap, point=[p.root_x, p.root_y])
        row.setdefault('physical', []).append(rec)
        return rec

    rpc_id = 0

    def rpc(op, **kw):
        nonlocal rpc_id
        rpc_id += 1
        req = dict(op=op, rpc_id=rpc_id, **kw)
        wire = (json.dumps(req, sort_keys=True) + '\n').encode()
        log('rpc_send', wire=wire.decode())
        app.stdin.write(wire)
        app.stdin.flush()
        reply_wire = line_read(app.stdout.fileno())
        log('rpc_receive', wire=reply_wire.decode())
        out = json.loads(reply_wire)
        if out['rpc_id'] != rpc_id:
            raise ValueError('RPC identity mismatch')
        return out

    def await_counter(name, value):
        end = time.monotonic() + 2
        while True:
            s = rpc('snapshot')
            if s['state'][name] == value:
                return s
            if time.monotonic() >= end:
                raise TimeoutError('application event not observed: '+name)
            time.sleep(.005)

    def release():
        nonlocal down
        log('release_send')
        xtest.fake_input(motor, X.ButtonRelease, 1)
        motor.sync()
        down = False
        log('release_server_sync')

    try:
        auth = folder/'private.Xauthority'
        fields = [b'', b'', b'MIT-MAGIC-COOKIE-1', os.urandom(16)]
        auth.write_bytes(struct.pack('>H', 65535) + b''.join(struct.pack('>H', len(v))+v for v in fields))
        auth.chmod(0o600)
        server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0',
                                   '640x360x24', '-nolisten', 'tcp', '-noreset', '-auth', str(auth)],
                                  stdout=subprocess.PIPE, stderr=sf)
        name = ':' + line_read(server.stdout.fileno()).decode().strip()
        exact_fields = [socket.gethostname().encode(), name[1:].encode(), fields[2], fields[3]]
        with auth.open('ab') as f:
            f.write(struct.pack('>H', 256) + b''.join(struct.pack('>H', len(v))+v for v in exact_fields))
        log('server_started', pid=server.pid, display=name)
        env = dict(os.environ, DISPLAY=name, XAUTHORITY=str(auth), PYTHONDONTWRITEBYTECODE='1')
        app = subprocess.Popen([sys.executable, '-u', str(HERE/'study.py'), 'receiver',
                                '--case', case, '--scenario', scenario,
                                '--journal', str(folder/'app.jsonl')], env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=af)
        ready_wire = line_read(app.stdout.fileno())
        row['ready'] = ready = json.loads(ready_wire)
        log('app_ready', wire=ready_wire.decode())
        if ready['pid'] != app.pid or ready['case'] != case:
            raise ValueError('receiver identity mismatch')
        inherited_auth = os.environ.get('XAUTHORITY')
        try:
            os.environ['XAUTHORITY'] = str(auth)
            motor, observer = display.Display(name), display.Display(name)
        finally:
            if inherited_auth is None:
                os.environ.pop('XAUTHORITY', None)
            else:
                os.environ['XAUTHORITY'] = inherited_auth
        if not motor.has_extension('XTEST'):
            raise RuntimeError('XTEST unavailable')
        row['initial'] = rpc('snapshot')
        before = physical('initial')
        if before['mask'] & 0x1f00 or any(before['keys']):
            raise RuntimeError('initial state not neutral')
        row['receipt'] = None
        row['candidate_claim_at_release'] = 'REFUSED_UNSUPPORTED'
        row['unsafe_control_abort_claim'] = False
        if scenario != 'unsupported':
            xtest.fake_input(motor, X.MotionNotify, x=ready['point'][0], y=ready['point'][1])
            motor.sync()
            log('pointer_moved')
            await_counter('enters', 1)
            log('press_send')
            xtest.fake_input(motor, X.ButtonPress, 1)
            motor.sync()
            down = True
            row['pressed'] = await_counter('presses', 1)
            if not physical('pressed')['mask'] & X.Button1Mask:
                raise RuntimeError('press not present at server')
            if scenario in ('applied', 'request_only', 'timeout'):
                receipt = rpc('cancel_request', nonce=ready['action']+':cancel')
                row['received_receipt'] = receipt
                if scenario == 'applied':
                    receipt = rpc('apply_cancel', nonce=ready['action']+':cancel')
                if scenario == 'timeout':
                    log('ack_wait_start', budget_ns=30000000)
                    time.sleep(.03)
                    log('ack_wait_expired')
                    if not rpc('snapshot')['state']['pending']:
                        raise ValueError('timeout control was not pending')
                row['receipt'] = receipt
            elif scenario == 'stale_receipt':
                if old_receipt is None:
                    raise RuntimeError('missing real predecessor receipt')
                row['receipt'] = old_receipt
            valid = proof_matches(ready, row['receipt'])
            row['candidate_claim_at_release'] = ('APPLICATION_ABORT_APPLIED' if valid
                else 'COMPLETION_UNVERIFIED' if scenario == 'complete' else 'QUERY_EFFECT')
            row['unsafe_control_abort_claim'] = (scenario == 'request_only'
                and isinstance(row['receipt'], dict)
                and row['receipt'].get('kind') == 'cancel_received'
                and all(row['receipt'].get(k) == ready[k] for k in ('session','case','action')))
            log('decision', claim=row['candidate_claim_at_release'], proof_valid=valid)
            release()
            row['released'] = await_counter('releases', 1)
            if scenario == 'request_only':
                row['late_receipt'] = rpc('apply_cancel', nonce=ready['action']+':cancel')
        row['terminal'] = rpc('snapshot')
        time.sleep(.02)  # Fixed rendering drain, not a measured feedback claim.
        terminal = physical('terminal')
        if terminal['mask'] & 0x1f00 or any(terminal['keys']):
            raise RuntimeError('terminal state not neutral')
        x, y, w, h = ready['roi']
        image = observer.screen().root.get_image(x, y, w, h, X.ZPixmap, 0xffffffff)
        # Installed python-xlib String8 decodes valid UTF-8 (including all-zero pixels).
        # Reverse that exact decoding, never interpret image bytes as Latin-1.
        payload = image.data.encode('utf-8') if isinstance(image.data, str) else image.data
        if not isinstance(payload, bytes) or len(payload) != w*h*4:
            raise ValueError('unexpected image representation/length')
        row['capture'] = dict(at_ns=time.monotonic_ns(), roi=ready['roi'],
                              parser_value_type=type(image.data).__name__,
                              depth=image.depth, bytes_b64=base64.b64encode(payload).decode(),
                              sha256=hashlib.sha256(payload).hexdigest(),
                              image_byte_order=observer.display.info.image_byte_order,
                              formats=[dict(depth=f.depth, bits_per_pixel=f.bits_per_pixel,
                                            scanline_pad=f.scanline_pad)
                                       for f in observer.display.info.pixmap_formats])
        row['final_candidate_semantic_abort'] = (proof_matches(ready, row['receipt'])
                                                and row['terminal']['state']['callbacks'] == 0)
        row['close'] = rpc('close')
        row['app_exit'] = app.wait(timeout=4)
        if row['app_exit'] != 0:
            raise RuntimeError('receiver exit failure')
        row['status'] = 'COMPLETE'
    except Exception as exc:
        row['status'] = 'STOP'
        row['error'] = type(exc).__name__ + ': ' + str(exc)
        row['traceback'] = traceback.format_exc()
    finally:
        if motor is not None and observer is not None:
            try:
                current = physical('cleanup_before')
                if down or current['mask'] & 0x100:
                    release()
                final = physical('cleanup_after')
                row['cleanup_neutral'] = not (final['mask'] & 0x1f00 or any(final['keys']))
            except Exception as exc:
                row['cleanup_error'] = repr(exc)
                row['cleanup_neutral'] = False
            motor.close()
            observer.close()
        if app is not None and app.poll() is None:
            app.terminate()
            try:
                app.wait(timeout=2)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=2)
        if app is not None:
            row['app_exit'] = app.returncode
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)
            row['xvfb_exit'] = server.returncode
        sf.close()
        af.close()
        row['trace'] = trace
        row['journal'] = (folder/'app.jsonl').read_text() if (folder/'app.jsonl').exists() else ''
        row['stderr'] = {p.name: p.read_text(errors='replace') for p in folder.glob('*.stderr')}
        (folder/'ROW.json').write_text(json.dumps(row, sort_keys=True, indent=2)+'\n')
    return row


def run(out, construction):
    out = Path(out).resolve()
    out.mkdir()  # Never overwrite an allocation, including a partial one.
    sources = {p.name: digest(p) for p in (HERE/'study.py', HERE/'audit.py', HERE/'PLAN.json')}
    if not construction:
        freeze = json.loads((HERE/'FREEZE.json').read_text())
        if sources != freeze['sources']:
            raise ValueError('frozen source mismatch')
    raw = dict(allocation='construction' if construction else 'semantic-abort-ack-20260922-01',
               source_hashes=sources, construction=construction, rows=[], reruns=0)
    prior = None
    try:
        for rep in range(1 if construction else 3):
            for scenario in SCENARIOS:
                case = ('construction' if construction else 'formal') + f'-{rep}-{scenario}'
                row = one_case(out/case, case, scenario, prior)
                raw['rows'].append(row)
                (out/'partial.json').write_text(json.dumps(raw, sort_keys=True, indent=2)+'\n')
                print(json.dumps({'case': case, 'status': row['status'], 'error': row.get('error'),
                                  'callbacks': row.get('terminal', {}).get('state', {}).get('callbacks')}), flush=True)
                if row['status'] != 'COMPLETE' or not row.get('cleanup_neutral'):
                    raise RuntimeError('case STOP: '+case)
                if scenario == 'applied':
                    prior = row['receipt']
        raw['status'] = 'COMPLETE'
    except Exception as exc:
        raw['status'], raw['error'] = 'STOP', repr(exc)
    raw['post_source_hashes'] = {p.name: digest(p) for p in (HERE/'study.py', HERE/'audit.py', HERE/'PLAN.json')}
    with open(out/'RAW.json', 'x') as f:
        json.dump(raw, f, sort_keys=True, indent=2)
        f.write('\n')
    return 0 if raw['status'] == 'COMPLETE' else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['run', 'receiver'])
    p.add_argument('--out')
    p.add_argument('--construction', action='store_true')
    p.add_argument('--case')
    p.add_argument('--scenario', choices=SCENARIOS)
    p.add_argument('--journal')
    a = p.parse_args()
    if a.mode == 'receiver':
        receiver(a.case, a.scenario, a.journal)
    else:
        if not a.out:
            p.error('--out is required')
        sys.exit(run(a.out, a.construction))
