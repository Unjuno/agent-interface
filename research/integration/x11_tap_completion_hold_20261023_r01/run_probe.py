"""Frozen ABBA comparison; private Xvfb only, one matched completion-hold boundary."""
import ast
import asyncio
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def verify_sources():
    for name, expected in json.loads((HERE / 'SOURCES.json').read_text()).items():
        actual = hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if actual != expected:
            raise ValueError('source changed: ' + name)


def baseline_methods(module):
    tree = ast.parse((HERE / 'baseline_backend.py.txt').read_text())
    cls = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == 'X11Backend')
    nodes = [item for item in cls.body if isinstance(item, ast.FunctionDef)
             and item.name in ('key_state', 'key_chord')]
    if len(nodes) != 2:
        raise ValueError('baseline method inventory')
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'frozen-baseline-backend', 'exec'),
         module.__dict__, namespace)
    return namespace


async def exercise(directory, arm, report):
    from Xlib import X, Xatom, XK, display
    from Xlib.ext import xtest
    from runtime.backends.x11_v1 import backend as backend_module
    from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
    from runtime.cli_v1.mcp_server import create_server

    app = display.Display(':188')
    observer = display.Display(':188')
    stop = threading.Event()
    first_press = threading.Event()
    entered = threading.Event()
    gate = threading.Event()
    app_thread = None
    server = None
    input_task = None
    events, requests = [], []
    original_get = GuardedSessionOwner.get
    original_emit = xtest.fake_input
    lock = threading.Lock()
    hold = {}
    patched_backend = None
    try:
        screen = app.screen()
        window = screen.root.create_window(20, 20, 128, 128, 0,
            X.CopyFromParent, X.InputOutput, X.CopyFromParent, background_pixel=0,
            event_mask=X.KeyPressMask | X.KeyReleaseMask)
        atom = app.intern_atom('AI_TAP_COMPLETION_EFFECT_COUNT')
        window.change_property(atom, Xatom.CARDINAL, 32, [0])
        window.map()
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        screen.root.warp_pointer(52, 52)
        gc = window.create_gc(foreground=0xFFFFFF)
        for y in range(0, 128, 16):
            for x in range(0, 128, 16):
                if (x//16+y//16) % 2 == 0:
                    window.fill_rectangle(gc, x, y, 16, 16)
        app.sync()
        code = observer.keysym_to_keycode(XK.string_to_keysym('a'))
        controls = observer.get_keyboard_control()
        report.update(window_id=window.id, keycode=code,
            keyboard_controls={'global_auto_repeat':controls.global_auto_repeat,
                               'auto_repeats_hex':bytes(controls.auto_repeats).hex()})
        def read():
            started = time.monotonic_ns()
            prop = observer.create_resource_object('window', window.id).get_full_property(atom, X.AnyPropertyType)
            keymap = observer.query_keymap()
            return {'count':list(prop.value) if prop is not None else None,
                'key_down':bool(keymap[code//8] & (1 << (code % 8))),
                'keymap_hex':bytes(keymap).hex(), 'started_ns':started,
                'completed_ns':time.monotonic_ns()}
        report['initial'] = read()
        assert report['initial']['count'] == [0] and not report['initial']['key_down']
        def application():
            count = 0
            while not stop.is_set():
                if not app.pending_events():
                    time.sleep(0.002)
                    continue
                event = app.next_event()
                if event.type not in (X.KeyPress, X.KeyRelease) or event.detail != code:
                    continue
                row = {'type':event.type, 'detail':event.detail, 'observed_ns':time.monotonic_ns()}
                if event.type == X.KeyPress:
                    count += 1
                    window.change_property(atom, Xatom.CARDINAL, 32, [count])
                    app.sync()
                    row.update(count=count, committed_ns=time.monotonic_ns())
                with lock:
                    events.append(row)
                if event.type == X.KeyPress:
                    first_press.set()
        app_thread = threading.Thread(target=application, daemon=True)
        app_thread.start()
        def get(owner):
            nonlocal patched_backend
            session = original_get(owner)
            backend = session.backend
            if patched_backend is not None:
                assert backend is patched_backend
                return session
            patched_backend = backend
            original_sync = backend.d.sync
            def emit(connection, kind, detail=0, **kwargs):
                result = original_emit(connection, kind, detail=detail, **kwargs)
                if connection is backend.d:
                    requests.append({'type':kind, 'detail':detail, 'returned_ns':time.monotonic_ns()})
                return result
            def sync(*args, **kwargs):
                result = original_sync(*args, **kwargs)
                armed = any(r['type'] == X.KeyPress and r['detail'] == code for r in requests)
                if armed and not entered.is_set():
                    hold.update(real_sync_returned_ns=time.monotonic_ns(),
                        requests_at_entry=list(requests),
                        obligations_at_entry=dict(backend.held_keycodes))
                    entered.set()
                    if not gate.wait(3.0):
                        hold['gate_timeout'] = True
                        raise TimeoutError('completion gate not released')
                    hold['completion_returned_ns'] = time.monotonic_ns()
                return result
            backend.d.sync = sync
            xtest.fake_input = emit
            return session

        async def call(name, args, label):
            reply = await asyncio.wait_for(server.call_tool(name, args), timeout=10)
            save(directory / (label+'-reply-0.json'), reply.model_dump(mode='json'))
            row = json.loads(reply.content[0].text)
            for index in range(1, 61):
                if row.get('status') != 'pending':
                    return row
                await asyncio.sleep(0.05)
                reply = await asyncio.wait_for(server.call_tool('interface_results',
                    {'call_id':row['call_id']}), timeout=5)
                save(directory / (label+'-reply-'+str(index)+'.json'), reply.model_dump(mode='json'))
                row = json.loads(reply.content[0].text)
            raise TimeoutError('result polling exhausted')

        methods = baseline_methods(backend_module) if arm == 'baseline' else {
            name:getattr(backend_module.X11Backend, name) for name in ('key_state', 'key_chord')}
        with patch.object(backend_module.X11Backend, 'key_state', methods['key_state']), \
             patch.object(backend_module.X11Backend, 'key_chord', methods['key_chord']), \
             patch.object(GuardedSessionOwner, 'get', get):
            server = create_server({'app':window.id}, directory/'mcp',
                session_mode='guarded-x11', display_name=':188', guarded_process_identity=True)
            observed = await call('interface_guarded_observe', {}, 'observe')
            assert observed['status'] == 'observed', observed
            report['source_binding'] = observed['source']['pointer_binding']
            minted = await call('interface_guarded_mint',
                {'alias':'field','source_sequence':observed['source']['sequence'],
                 'point':[52,52],'region_size':[24,24]}, 'mint')
            assert minted['status'] == 'minted', minted
            report['input_invoked_ns'] = time.monotonic_ns()
            input_task = asyncio.create_task(call('interface_guarded_input',
                {'alias':'field','offset':minted['offset'],'interaction':'keyboard',
                 'observe_after':False,'wait_for_result_ms':10000,
                 'tail':[{'op':'key_chord','keys':['a']}]}, 'input'))
            assert await asyncio.to_thread(entered.wait, 2.0), 'completion hold not reached'
            assert await asyncio.to_thread(first_press.wait, 1.0), 'no app press'
            report['held_start'] = read()
            await asyncio.sleep(1.0)
            report['held_end'] = read()
            report['gate_released_ns'] = time.monotonic_ns()
            gate.set()
            report['input_result'] = await input_task
            report['input_returned_ns'] = time.monotonic_ns()
            await asyncio.sleep(0.15)
            report['final'] = read()
            report['close'] = await call('interface_close', {}, 'close')
            server = None
        report.update(status='OBSERVED', hold=hold, requests=requests)
    finally:
        gate.set()
        if input_task is not None and not input_task.done():
            try:
                await asyncio.wait_for(input_task, timeout=5)
            except BaseException as error:
                report['input_cleanup_error'] = repr(error)
        if server is not None:
            try:
                reply = await asyncio.wait_for(server.call_tool('interface_close', {}), timeout=5)
                save(directory/'exception-close.json', reply.model_dump(mode='json'))
            except BaseException as error:
                report['close_cleanup_error'] = repr(error)
        xtest.fake_input = original_emit
        stop.set()
        if app_thread is not None:
            app_thread.join(1)
            report['application_thread_stopped'] = not app_thread.is_alive()
        with lock:
            report['application_events'] = list(events)
        report['hold'] = hold
        report['requests'] = requests
        app.close()
        observer.close()


def main():
    verify_sources()
    conditions = json.loads((HERE/'conditions.json').read_text())
    assert hashlib.sha256(Path('/usr/bin/Xvfb').read_bytes()).hexdigest() == conditions['xvfb_sha256']
    with (HERE/'attempt-started.json').open('x') as stream:
        json.dump({'run_id':conditions['run_id'],'started_ns':time.monotonic_ns(),
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}, stream)
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    os.nice(10)
    rows = []
    for index, arm in enumerate(conditions['order']):
        directory = HERE / (str(index)+'-'+arm)
        directory.mkdir(exist_ok=False)
        report = {'arm':arm,'index':index,'status':'FAIL','started_ns':time.monotonic_ns()}
        proc = None
        pidfd = None
        try:
            assert not Path('/tmp/.X188-lock').exists() and not Path('/tmp/.X11-unix/X188').exists()
            with tempfile.TemporaryDirectory(prefix='ai-tap-hold-auth-') as td:
                auth = Path(td)/'Xauthority'
                auth.touch(mode=0o600)
                subprocess.run(['/usr/bin/xauth','-f',str(auth),'add',':188','.',secrets.token_hex(16)],
                    capture_output=True, check=True, timeout=5)
                os.environ.update(DISPLAY=':188', XAUTHORITY=str(auth),
                    OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
                os.environ.pop('WAYLAND_DISPLAY', None)
                with (directory/'xvfb.txt').open('wb') as log:
                    proc = subprocess.Popen(['/usr/bin/Xvfb',':188','-screen','0',
                        '320x240x24','-nolisten','tcp','-auth',str(auth)], stdout=log, stderr=subprocess.STDOUT)
                    pidfd = os.pidfd_open(proc.pid)
                    report['xvfb_pid'] = proc.pid
                    report['xvfb_stat'] = Path('/proc/'+str(proc.pid)+'/stat').read_text()
                    report['pidfd_info'] = Path('/proc/self/fdinfo/'+str(pidfd)).read_text()
                    save(directory/'process-started.json', report)
                    time.sleep(0.5)
                    assert proc.poll() is None
                    asyncio.run(exercise(directory, arm, report))
        except BaseException as error:
            report.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
        finally:
            if pidfd is not None:
                try:
                    signal.pidfd_send_signal(pidfd, signal.SIGCONT)
                    signal.pidfd_send_signal(pidfd, signal.SIGTERM)
                    report['xvfb_exit_code'] = proc.wait(timeout=5)
                except BaseException as error:
                    report.update(status='FAIL_CLEANUP',cleanup_error=repr(error))
                    try:
                        signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                        report['kill_exit_code'] = proc.wait(timeout=5)
                    except BaseException as error2:
                        report['kill_error'] = repr(error2)
                os.close(pidfd)
            elif proc is not None:
                proc.terminate()
                report['unpinned_exit_code'] = proc.wait(timeout=5)
            report['ended_ns'] = time.monotonic_ns()
            save(directory/'result.json', report)
        rows.append({'index':index,'arm':arm,'status':report['status']})
        if report['status'] != 'OBSERVED':
            break
    verify_sources()
    save(HERE/'run-result.json', {'status':'RAW_RETAINED_PENDING_AUDIT','arms':rows})
    print(json.dumps(rows))
    return 0 if len(rows) == 4 and all(r['status'] == 'OBSERVED' for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
