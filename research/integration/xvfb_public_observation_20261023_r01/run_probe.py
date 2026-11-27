"""One frozen, input-free public MCP observation probe on an owned X server."""
import asyncio
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def exercise(report):
    from Xlib import X, display
    from PIL import Image
    from runtime.cli_v1.mcp_server import create_server

    app = display.Display(':188')
    server = None
    try:
        screen = app.screen()
        window = screen.root.create_window(20, 20, 64, 64, 0,
            X.CopyFromParent, X.InputOutput, X.CopyFromParent, background_pixel=0)
        window.map()
        app.sync()
        report['window_id'] = window.id
        report['x_vendor'] = app.display.info.vendor
        server = create_server({'fixture': window.id}, HERE / 'mcp',
            session_mode='persistent-x11', display_name=':188')

        async def call(name, args, label):
            reply = await asyncio.wait_for(server.call_tool(name, args), timeout=10)
            save(label + '-reply-0.json', reply.model_dump(mode='json'))
            row = json.loads(reply.content[0].text)
            call_id = row.get('call_id')
            for index in range(1, 101):
                if row.get('status') != 'pending':
                    return reply, row
                await asyncio.sleep(0.05)
                reply = await asyncio.wait_for(server.call_tool('interface_results',
                    {'call_id': call_id}), timeout=10)
                save(label + '-reply-' + str(index) + '.json', reply.model_dump(mode='json'))
                row = json.loads(reply.content[0].text)
            raise RuntimeError('public result did not settle')

        report['observations'] = []
        for index, color in enumerate((0xFF0000, 0x00FF00)):
            gc = window.create_gc(foreground=color)
            window.fill_rectangle(gc, 0, 0, 64, 64)
            app.sync()
            committed = time.monotonic_ns()
            started = time.monotonic_ns()
            reply, row = await call('interface_observe',
                {'target': 'fixture', 'frame': 'window_client', 'region': [0, 0, 64, 64]},
                'observe-' + str(index))
            returned = time.monotonic_ns()
            images = [part for part in reply.content if part.type == 'image']
            assert not reply.isError and len(images) == 1, row
            raw = base64.b64decode(images[0].data, validate=True)
            path = HERE / ('observation-' + str(index) + '.png')
            path.write_bytes(raw)
            image = Image.open(io.BytesIO(raw)).convert('RGB')
            expected = (255, 0, 0) if index == 0 else (0, 255, 0)
            colors = image.getcolors(maxcolors=4096)
            entry = {'index': index, 'app_sync_returned_ns': committed,
                'call_started_ns': started, 'call_returned_ns': returned,
                'call_id': row['call_id'], 'image_size': list(image.size),
                'colors': colors, 'expected_rgb': expected, 'png_sha256': digest(path)}
            report['observations'].append(entry)
            assert image.size == (64, 64) and colors == [(4096, expected)], entry
            native_report = json.loads((HERE / 'mcp' / row['call_id'] / 'report.json').read_text())
            native = native_report['observation']
            entry['capture_started_ns'] = native['capture_started_ns']
            entry['capture_ended_ns'] = native['capture_ended_ns']
            assert committed <= started <= native['capture_started_ns'] <= native['capture_ended_ns'] <= returned
            assert native_report['input_dispatched'] is False
            retained, retained_row = await call('interface_results',
                {'call_id': row['call_id']}, 'retained-' + str(index))
            retained_images = [part for part in retained.content if part.type == 'image']
            assert len(retained_images) == 1 and retained_images[0].data == images[0].data
            assert retained_row.get('operation_invoked') is False, retained_row
            entry['retained_identical'] = True
        _, close_row = await call('interface_close', {}, 'close')
        report['public_close'] = close_row
        # Actual close receipt is also retained under mcp/<call_id>/report.json.
        close_report = json.loads((HERE / 'mcp' / close_row['call_id'] / 'report.json').read_text())
        report['public_close_report'] = close_report
        assert close_report['status'] == 'closed', close_report
        assert close_report['release_attempted'] is False, close_report
        assert close_report['connection_close_attempted'] is True, close_report
        server = None
    finally:
        if server is not None:
            try:
                reply = await asyncio.wait_for(server.call_tool('interface_close', {}), timeout=10)
                save('exception-close.json', reply.model_dump(mode='json'))
            except Exception as error:
                report['exception_close_error'] = repr(error)
        app.close()


def main():
    conditions = json.loads((HERE / 'conditions.json').read_text())
    assert digest(Path('/usr/bin/Xvfb')) == conditions['xvfb_sha256']
    for name, expected in json.loads((HERE / 'SOURCES.json').read_text()).items():
        actual = hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        assert actual == expected, name
    for path in ('/tmp/.X188-lock', '/tmp/.X11-unix/X188'):
        assert not Path(path).exists(), path
    with (HERE / 'attempt-started.json').open('x') as stream:
        json.dump({'run_id': conditions['run_id'], 'started_ns': time.monotonic_ns()}, stream)
    report = {'status': 'FAIL', 'input_operations': 0, 'observations': [],
        'runtime': sys.version, 'platform': os.uname().release}
    proc = None
    pidfd = None
    def expired(_signum, _frame):
        raise TimeoutError('45 second probe deadline')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(45)
    try:
        with tempfile.TemporaryDirectory(prefix='ai-observe-r01-') as td:
            auth = Path(td) / 'Xauthority'
            auth.touch(mode=0o600)
            subprocess.run(['/usr/bin/xauth', '-f', str(auth), 'add', ':188', '.',
                secrets.token_hex(16)], check=True, capture_output=True, timeout=5)
            os.environ['DISPLAY'] = ':188'
            os.environ['XAUTHORITY'] = str(auth)
            os.environ.pop('WAYLAND_DISPLAY', None)
            with (HERE / 'xvfb.txt').open('wb') as log:
                proc = subprocess.Popen(['/usr/bin/Xvfb', ':188', '-screen', '0',
                    '320x240x24', '-nolisten', 'tcp', '-auth', str(auth)],
                    stdout=log, stderr=subprocess.STDOUT)
                pidfd = os.pidfd_open(proc.pid)
                report['pid'] = proc.pid
                report['pidfd_info'] = Path('/proc/self/fdinfo/' + str(pidfd)).read_text()
                report['process_stat'] = Path('/proc/' + str(proc.pid) + '/stat').read_text()
                save('process-started.json', report)
                # A single bounded readiness interval; no connection retries.
                time.sleep(0.5)
                assert proc.poll() is None, 'Xvfb exited during settle interval'
                asyncio.run(exercise(report))
                report['status'] = 'PASS_OBSERVATION_SCOPED'
    except BaseException as error:
        report['error'] = repr(error)
        report['traceback'] = traceback.format_exc()
    finally:
        if pidfd is not None:
            try:
                signal.pidfd_send_signal(pidfd, signal.SIGCONT)
                signal.pidfd_send_signal(pidfd, signal.SIGTERM)
                report['xvfb_exit_code'] = proc.wait(timeout=5)
            except BaseException as error:
                report['cleanup_error'] = repr(error)
                report['status'] = 'FAIL_CLEANUP'
                try:
                    signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                    report['xvfb_kill_exit_code'] = proc.wait(timeout=5)
                except BaseException as kill_error:
                    report['kill_error'] = repr(kill_error)
            os.close(pidfd)
        elif proc is not None:
            # Popen retains this unreaped child; no PID-reuse window while alive.
            proc.terminate()
            report['fallback_child_exit_code'] = proc.wait(timeout=5)
            report['status'] = 'FAIL_PIDFD'
        report['ended_ns'] = time.monotonic_ns()
        signal.alarm(0)
        save('result.json', report)
    print(json.dumps({'status': report['status'], 'error': report.get('error'), 'pid': report.get('pid')}))
    return 0 if report['status'] == 'PASS_OBSERVATION_SCOPED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
