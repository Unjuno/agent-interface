"""Frozen A03 probe: standard MCP caller with real Xvfb reply-path blocking.

The proxy is private to the spawned owner process. It forwards that process's
X11 connection to Xvfb and can withhold one complete server reply after the
synthetic application independently observes a KeyPress. XRes and recovery
connections remain direct clients of the same Xvfb server.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import select
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import traceback

from Xlib import X, Xatom, XK, display
from Xlib.ext import res
from PIL import Image, ImageStat
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner


OUT = Path(os.environ.get('AGENT_INTERFACE_A03_OUT', '/out'))
TRIALS = 3
def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n',
                         encoding='utf-8')
    os.replace(temporary, path)


def _metadata(response):
    return json.loads(response.content[0].text)


def _peer_pid(connection):
    raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                                struct.calcsize('3i'))
    return struct.unpack('3i', raw)[0]


def _recv_exact(connection, size):
    chunks = []
    remaining = size
    while remaining:
        chunk = connection.recv(remaining)
        if not chunk:
            if remaining == size:
                return None
            raise EOFError('truncated X11 server frame')
        chunks.append(chunk)
        remaining -= len(chunk)
    return b''.join(chunks)


def _server_frame(connection, first=True):
    header = _recv_exact(connection, 8 if first else 32)
    if header is None:
        return None
    if first:
        if header[0] not in (0, 1):
            raise ValueError('invalid X11 setup response')
        length = int.from_bytes(header[6:8], 'little')
        tail = _recv_exact(connection, length * 4)
        if tail is None:
            raise EOFError('truncated X11 setup body')
        return header + tail, None
    response_type = header[0] & 0x7f
    sequence = int.from_bytes(header[2:4], 'little')
    length = int.from_bytes(header[4:8], 'little') if response_type in (1, 35) else 0
    tail = _recv_exact(connection, length * 4)
    if tail is None:
        raise EOFError('truncated X11 reply body')
    return header + tail, (response_type, sequence)


def _relay_client_to_server(client, upstream):
    try:
        while True:
            data = client.recv(65536)
            if not data:
                return
            upstream.sendall(data)
    except (OSError, EOFError):
        return
    finally:
        for sock in (client, upstream):
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass


def _relay_server_to_owner(upstream, client, *, owner_pid, marker_dir):
    marker_dir = Path(marker_dir)
    first = True
    try:
        while True:
            frame_row = _server_frame(upstream, first=first)
            if frame_row is None:
                return
            frame, protocol = frame_row
            if first:
                first = False
                client.sendall(frame)
                continue
            response_type, _reply_sequence = protocol
            is_owner_reply = (owner_pid == os.getpid() and response_type == 1)
            if is_owner_reply and (marker_dir / 'input_started').exists():
                wait_until = time.monotonic() + 1.5
                while (time.monotonic() < wait_until
                       and not (marker_dir / 'key_press_seen').exists()):
                    time.sleep(0.001)
                if (marker_dir / 'key_press_seen').exists():
                    _write_json(marker_dir / 'owner_reply_held.json', {
                        'status':'held', 'owner_peer_pid':owner_pid,
                        'reply_sequence':_reply_sequence, 'response_type':response_type,
                        'reply_bytes':len(frame), 'reply_hex':frame.hex(),
                        'held_monotonic_ns':time.monotonic_ns(),
                        'release':'withheld_until_owner_process_retirement',
                    })
                    # Owner termination is the only way out of this read path.
                    while True:
                        select.select([], [], [], 30.0)
            client.sendall(frame)
    except (OSError, EOFError, ConnectionError):
        return
    finally:
        try:
            client.shutdown(socket.SHUT_WR)
        except OSError:
            pass


class _ReplyGateProxy:
    def __init__(self, direct_display: str, proxy_display: str, marker_dir: Path):
        self.direct_display = direct_display
        self.proxy_display = proxy_display
        self.marker_dir = Path(marker_dir)
        self.number = int(proxy_display.rsplit(':', 1)[1].split('.', 1)[0])
        self.path = Path('/tmp/.X11-unix') / f'X{self.number}'
        self.stop = threading.Event()
        self.thread = None
        self.listener = None

    def start(self):
        self.marker_dir.mkdir(parents=True, exist_ok=True)
        self.path.unlink(missing_ok=True)
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(self.path))
        os.chmod(self.path, 0o666)
        self.listener.listen(16)
        self.listener.settimeout(0.1)
        self.thread = threading.Thread(target=self._accept,
                                      name='a03-private-x11-proxy', daemon=True)
        self.thread.start()
        _write_json(self.marker_dir / 'proxy_ready.json', {
            'direct_display':self.direct_display, 'proxy_display':self.proxy_display,
            'socket_path':str(self.path), 'owner_pid':os.getpid(),
            'monotonic_ns':time.monotonic_ns(),
        })
        return self

    def _accept(self):
        while not self.stop.is_set():
            try:
                client, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            threading.Thread(target=self._connect, args=(client,), daemon=True).start()

    def _connect(self, client):
        try:
            peer_pid = _peer_pid(client)
            upstream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            upstream.connect(f'/tmp/.X11-unix/X{int(self.direct_display.rsplit(":",1)[1].split(".",1)[0])}')
            owner_client = peer_pid == os.getpid()
            _write_json(self.marker_dir / ('owner_peer.json' if owner_client else
                                           f'other_peer_{peer_pid}.json'), {
                'peer_pid':peer_pid, 'proxy_owner_pid':os.getpid(),
                'owner_connection':owner_client, 'monotonic_ns':time.monotonic_ns(),
            })
            reader = threading.Thread(target=_relay_server_to_owner,
                args=(upstream, client),
                kwargs={'owner_pid':peer_pid, 'marker_dir':self.marker_dir}, daemon=True)
            writer = threading.Thread(target=_relay_client_to_server,
                args=(client, upstream),
                daemon=True)
            reader.start(); writer.start()
            reader.join(); writer.join()
        except Exception as error:
            _write_json(self.marker_dir / 'proxy_error.json', {
                'error_type':type(error).__name__, 'error':str(error),
                'traceback':traceback.format_exc(),
            })
        finally:
            for sock in (locals().get('client'), locals().get('upstream')):
                if sock is not None:
                    try: sock.close()
                    except OSError: pass

    def close(self):
        self.stop.set()
        if self.listener is not None:
            self.listener.close()
        if self.thread is not None:
            self.thread.join(1.0)
        self.path.unlink(missing_ok=True)


def _owner_factory(targets, directory, display_name, options):
    proxy_display = os.environ.get('AGENT_INTERFACE_A03_PROXY_DISPLAY')
    if not proxy_display:
        return GuardedSessionOwner(targets, directory, display_name, **options)
    marker_dir = Path(os.environ['AGENT_INTERFACE_A03_MARKER_DIR'])
    proxy = _ReplyGateProxy(display_name, proxy_display, marker_dir).start()
    owner = GuardedSessionOwner(targets, directory, proxy_display, **options)
    # Daemon proxy lifetime is intentionally identical to the spawned owner.
    owner._a03_proxy = proxy
    return owner


def _xvfb_start(display_number):
    executable = shutil.which('Xvfb')
    if not executable:
        raise RuntimeError('Xvfb executable unavailable')
    log_path = OUT / f'xvfb-{display_number}.log'
    log = log_path.open('wb')
    process = subprocess.Popen([executable, f':{display_number}', '-screen', '0',
        '800x600x24', '-nolisten', 'tcp', '-ac', '-noreset'],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'Xvfb exited early: {process.returncode}')
        try:
            test = display.Display(f':{display_number}')
            test.close()
            return process, log
        except Exception:
            time.sleep(0.02)
    process.terminate(); process.wait(timeout=2)
    raise TimeoutError('private Xvfb did not become ready')


def _wait_for(path, seconds=5.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        time.sleep(0.005)
    raise TimeoutError(f'timed out waiting for {path.name}')


async def _server_result(server, call_id, wait_s=8.0):
    end = time.monotonic() + wait_s
    latest = None
    while time.monotonic() < end:
        latest = _metadata(await server.call_tool('interface_results', {
            'call_id':call_id, 'include_image':False}))
        if latest.get('status') != 'pending':
            return latest
        time.sleep(0.01)
    return latest


async def _run_trial(arm: str, index: int):
    trial_id = f'{arm}-{index:02d}'
    trial_dir = OUT / trial_id
    trial_dir.mkdir(parents=True, exist_ok=False)
    display_number = 101 + index * 2 + (1 if arm == 'blocked' else 0)
    display_name = f':{display_number}'
    proxy_display = f':{display_number + 1000}'
    marker_dir = trial_dir / 'proxy'
    app_display = observer = None
    server = None
    xvfb = xvfb_log = None
    app_stop = threading.Event()
    app_thread = None
    event_lock = threading.Lock()
    events = []
    press_seen = threading.Event()
    release_seen = threading.Event()
    effect_seen = threading.Event()
    report = {'schema':'agent-interface/standard-caller-blocked-x11-a03-v1',
              'trial_id':trial_id, 'arm':arm, 'status':'RUNNING',
              'timing':{}, 'events':events}
    active_call_id = None
    try:
        xvfb, xvfb_log = _xvfb_start(display_number)
        report['xvfb'] = {'display':display_name, 'pid':xvfb.pid,
            'argv':xvfb.args, 'log':str(trial_dir / f'xvfb-{display_number}.log')}
        app_display = display.Display(display_name)
        screen = app_display.screen()
        root = screen.root
        x, y, width, height = 10, 10, 780, 580
        window = root.create_window(x, y, width, height, 0, X.CopyFromParent,
            X.InputOutput, X.CopyFromParent, background_pixel=0,
            event_mask=X.KeyPressMask | X.KeyReleaseMask | X.StructureNotifyMask)
        effect_atom = app_display.intern_atom('AI_A03_SYNTHETIC_TASK_EFFECT')
        window.change_property(effect_atom, Xatom.CARDINAL, 32, [0])
        window.map(); window.set_input_focus(X.RevertToParent, X.CurrentTime)
        root.warp_pointer(400, 300)
        gc = window.create_gc(foreground=0xFFFFFF)
        for row in range((height + 15) // 16):
            for column in range((width + 15) // 16):
                if (row + column) % 2 == 0:
                    window.fill_rectangle(gc, column * 16, row * 16,
                        min(16, width - column * 16), min(16, height - row * 16))
        app_display.sync()
        keycode = app_display.keysym_to_keycode(XK.string_to_keysym('a'))
        if not keycode:
            raise AssertionError('Xvfb has no keycode for a')

        def application():
            while not app_stop.is_set():
                if not app_display.pending_events():
                    time.sleep(0.001)
                    continue
                event = app_display.next_event()
                row = {'type':event.type, 'detail':getattr(event, 'detail', None),
                       'monotonic_ns':time.monotonic_ns()}
                if event.type == X.KeyPress and event.detail == keycode:
                    window.change_property(effect_atom, Xatom.CARDINAL, 32, [1])
                    app_display.sync()
                    row['effect_committed_ns'] = time.monotonic_ns()
                    effect_seen.set(); press_seen.set()
                    if arm == 'blocked':
                        _write_json(marker_dir / 'key_press_seen', row)
                elif event.type == X.KeyRelease and event.detail == keycode:
                    release_seen.set()
                with event_lock:
                    events.append(row)

        app_thread = threading.Thread(target=application, daemon=True,
                                      name=f'a03-app-{trial_id}')
        app_thread.start()
        observer = display.Display(display_name)
        version = observer.res_query_version()
        pid_query = observer.res_query_client_ids([{
            'client':window.id, 'mask':res.LocalClientPIDMask}])
        report['server'] = {'vendor':observer.display.info.vendor,
            'release':observer.display.info.release_number,
            'xres_version':[version.server_major, version.server_minor],
            'target_pid':pid_query.ids[0].value[0] if pid_query.ids else None,
            'xvfb_pid':xvfb.pid, 'window_id':window.id,
            'keycode_a':keycode}
        if report['server']['target_pid'] != os.getpid():
            raise AssertionError('XRes target PID namespace mismatch')

        # The parent stays on the direct Xvfb display for XRes and independent
        # recovery. Only the owned session's Xlib client is routed through :N+1000.
        if arm == 'blocked':
            os.environ['AGENT_INTERFACE_A03_PROXY_DISPLAY'] = proxy_display
            os.environ['AGENT_INTERFACE_A03_MARKER_DIR'] = str(marker_dir)
        else:
            os.environ.pop('AGENT_INTERFACE_A03_PROXY_DISPLAY', None)
            os.environ.pop('AGENT_INTERFACE_A03_MARKER_DIR', None)
        server = create_server({'app':window.id}, trial_dir / 'mcp',
            display_name=display_name, session_mode='guarded-x11',
            guarded_process_identity=True, guarded_query_worker=True,
            guarded_window_lifecycle=True, guarded_owned_process=True,
            _guarded_owner_factory=_owner_factory)

        report['timing']['observe_started_ns'] = time.monotonic_ns()
        observed = _metadata(await server.call_tool('interface_guarded_observe', {}))
        report['timing']['observe_returned_ns'] = time.monotonic_ns()
        report['observe_status'] = observed.get('status')
        if observed.get('status') != 'observed':
            raise AssertionError(f'observe failed: {observed}')
        source = observed['source']
        report['observation_source'] = source
        binding = source['pointer_binding']
        image_artifact = observed['observation_report']['observation']['artifact']
        image = Image.open(image_artifact['path']).convert('RGB')
        # Observation reports vary by schema; use the known focused client point
        # while retaining the exact source and image patch used for minting.
        point = [400, 300]
        patch = image.crop((point[0]-12, point[1]-12, point[0]+12, point[1]+12))
        patch_stddev = ImageStat.Stat(patch).stddev
        report['mint_patch'] = {'point':point, 'stddev':patch_stddev,
            'image_sha256':image_artifact['sha256'],
            'image_bytes':image_artifact['bytes']}
        minted = _metadata(await server.call_tool('interface_guarded_mint', {
            'alias':'a03', 'source_sequence':source['sequence'],
            'point':point, 'region_size':[24,24]}))
        report['mint_status'] = minted.get('status')
        report['mint'] = minted
        if minted.get('status') != 'minted':
            raise AssertionError(f'mint failed: {minted}')

        report['timing']['input_started_ns'] = time.monotonic_ns()
        if arm == 'blocked':
            _write_json(marker_dir / 'input_started', {
                'monotonic_ns':report['timing']['input_started_ns']})
        input_result = _metadata(await server.call_tool('interface_guarded_input', {
            'alias':'a03', 'offset':minted['offset'], 'interaction':'keyboard',
            'observe_after':False, 'wait_for_result_ms':0,
            'tail':[{'op':'key_chord', 'keys':['a']}]}))
        report['timing']['input_returned_ns'] = time.monotonic_ns()
        report['input_initial'] = input_result
        active_call_id = input_result.get('call_id')
        if input_result.get('status') not in ('pending', 'completed'):
            raise AssertionError(f'input admission failed: {input_result}')

        if arm == 'healthy':
            terminal = (input_result if input_result.get('status') != 'pending'
                        else await _server_result(server, input_result['call_id']))
            report['terminal_before_close'] = terminal
            report['timing']['terminal_returned_ns'] = time.monotonic_ns()
            if terminal.get('status') != 'completed':
                raise AssertionError(f'healthy caller did not complete: {terminal}')
            if not press_seen.wait(3.0) or not release_seen.wait(3.0):
                raise AssertionError('healthy synthetic app missed press/release')
            report['independent_release_before_close'] = not bool(
                observer.query_keymap()[keycode // 8] & (1 << (keycode % 8)))
            report['independent_effect_before_close'] = list(observer
                .create_resource_object('window', window.id)
                .get_full_property(effect_atom, X.AnyPropertyType).value)
            if not report['independent_release_before_close']:
                raise AssertionError('healthy terminal keymap did not read up')
            if report['independent_effect_before_close'] != [1]:
                raise AssertionError('healthy app effect readback was not [1]')
            report['status'] = 'PASS_HEALTHY_CONTROL'
        else:
            if input_result.get('status') != 'pending':
                raise AssertionError(f'blocked input unexpectedly terminal: {input_result}')
            held = _wait_for(marker_dir / 'owner_reply_held.json', seconds=8.0)
            owner_peer = _wait_for(marker_dir / 'owner_peer.json', seconds=3.0)
            report['proxy_owner_peer'] = owner_peer
            report['proxy_held_reply'] = held
            owner_snapshot = (input_result.get('session', {})
                              .get('owner_process', {}))
            report['owner_pid_from_standard_caller'] = owner_snapshot.get('pid')
            if owner_snapshot.get('pid') != owner_peer.get('peer_pid'):
                raise AssertionError('proxy peer PID did not match standard caller owner PID')
            if not press_seen.wait(2.0) or not effect_seen.is_set():
                raise AssertionError('application did not independently observe key press/effect')
            down = observer.query_keymap()
            report['independent_keymap_before_cancel'] = {
                'keycode_a_down':bool(down[keycode // 8] & (1 << (keycode % 8))),
                'reader':'independent direct Xvfb client',
                'monotonic_ns':time.monotonic_ns()}
            effect = observer.create_resource_object('window', window.id).get_full_property(
                effect_atom, X.AnyPropertyType)
            report['independent_effect_before_cancel'] = {
                'value':list(effect.value) if effect is not None else None,
                'reader':'independent direct Xvfb client',
                'monotonic_ns':time.monotonic_ns()}
            if not report['independent_keymap_before_cancel']['keycode_a_down']:
                raise AssertionError('key was not down at the blocked-I/O boundary')
            if report['independent_effect_before_cancel']['value'] != [1]:
                raise AssertionError('synthetic app effect not independently committed')
            report['timing']['cancel_started_ns'] = time.monotonic_ns()
            cancel = _metadata(await server.call_tool('interface_guarded_cancel', {
                'call_id':input_result['call_id']}))
            report['timing']['cancel_returned_ns'] = time.monotonic_ns()
            report['cancel'] = cancel
            terminal = await _server_result(server, input_result['call_id'])
            report['terminal'] = terminal
            report['bounded_cancel_elapsed_ms'] = (
                report['timing']['cancel_returned_ns']
                - report['timing']['cancel_started_ns']) / 1_000_000
            keymap = observer.query_keymap()
            report['independent_keymap_after_cancel'] = {
                'keycode_a_down':bool(keymap[keycode // 8] & (1 << (keycode % 8))),
                'reader':'independent direct Xvfb client',
                'monotonic_ns':time.monotonic_ns()}
            report['application_release_seen'] = release_seen.wait(2.0)
            effect = observer.create_resource_object('window', window.id).get_full_property(
                effect_atom, X.AnyPropertyType)
            report['independent_effect_after_cancel'] = list(effect.value) if effect else None
            checks = {
                'one_complete_owner_reply_withheld':held.get('status') == 'held' and held.get('response_type') == 1 and held.get('reply_bytes', 0) >= 32,
                'gate_peer_is_owner_process':owner_peer.get('owner_connection') is True and owner_peer.get('peer_pid') == owner_snapshot.get('pid'),
                'owner_retired':cancel.get('owner_process_retired') is True,
                'xres_disconnect':cancel.get('owner_client_disconnect', {}).get('status') == 'disconnected',
                'key_down_before_cancel':report['independent_keymap_before_cancel']['keycode_a_down'],
                'key_up_after_cancel':report['independent_keymap_after_cancel']['keycode_a_down'] is False,
                'app_saw_release':report['application_release_seen'] is True,
                'effect_retained':report['independent_effect_after_cancel'] == [1],
                'caller_returned_under_3s':report['bounded_cancel_elapsed_ms'] < 3000,
                'release_not_overclaimed':cancel.get('release_confirmed') is False and cancel.get('cleanup_status') == 'UNKNOWN',
                'late_server_request_not_overruled':cancel.get('late_server_request_possible') is True,
                'terminal_status_failed_closed':terminal.get('status') == 'runtime_failed',
                'task_success_unknown':terminal.get('task_success') is None,
                'replay_disabled':terminal.get('replay_allowed') is False,
            }
            report['checks'] = checks
            report['status'] = 'PASS_BLOCKED_STANDARD_CALLER_SCOPED' if all(checks.values()) else 'FAIL_BLOCKED_STANDARD_CALLER_SCOPED'
            if report['status'].startswith('FAIL'):
                raise AssertionError(f'blocked checks failed: {checks}')
        report['timing']['trial_finished_ns'] = time.monotonic_ns()
        _write_json(trial_dir / 'result.json', report)
        return report
    except BaseException as error:
        report.update(status='FAIL', error_type=type(error).__name__, error=str(error),
                      traceback=traceback.format_exc())
        report['timing']['failed_ns'] = time.monotonic_ns()
        _write_json(trial_dir / 'result.json', report)
        raise
    finally:
        if server is not None:
            if (arm == 'blocked' and active_call_id
                    and report.get('cancel') is None):
                try:
                    report['finally_cancel'] = _metadata(await asyncio.wait_for(
                        server.call_tool('interface_guarded_cancel', {
                            'call_id':active_call_id}), timeout=5.0))
                except Exception as cleanup_error:
                    report['finally_cancel_error'] = {
                        'type':type(cleanup_error).__name__,
                        'message':str(cleanup_error)}
            try:
                await asyncio.wait_for(server.call_tool('interface_close', {}),
                                       timeout=3.0)
            except Exception:
                pass
        app_stop.set()
        if app_thread is not None:
            app_thread.join(1.0)
        for connection in (observer, app_display):
            if connection is not None:
                try: connection.close()
                except Exception: pass
        if xvfb is not None:
            if xvfb.poll() is None:
                xvfb.terminate()
                try: xvfb.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    xvfb.kill(); xvfb.wait(timeout=2.0)
            report['xvfb_exitcode'] = xvfb.returncode
        if xvfb_log is not None:
            xvfb_log.close()
        os.environ.pop('AGENT_INTERFACE_A03_PROXY_DISPLAY', None)
        os.environ.pop('AGENT_INTERFACE_A03_MARKER_DIR', None)
        _write_json(trial_dir / 'result.json', report)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = {'python':sys.version, 'xvfb':shutil.which('Xvfb'),
           'xauthority':os.environ.get('XAUTHORITY')}
    try:
        import mcp
        env['mcp_module'] = getattr(mcp, '__version__', 'present')
    except Exception as error:
        env['mcp_import_error'] = repr(error)
    report = {'schema':'agent-interface/standard-caller-blocked-x11-a03-run-v1',
              'status':'RUNNING', 'environment':env, 'trials':[]}
    _write_json(OUT / 'environment.json', env)
    _write_json(OUT / 'run-result.json', report)
    try:
        for index in range(1, TRIALS + 1):
            for arm in ('healthy', 'blocked'):
                trial = await _run_trial(arm, index)
                report['trials'].append({'trial_id':trial['trial_id'],
                                         'status':trial['status'], 'arm':arm})
                _write_json(OUT / 'run-result.json', report)
        report['status'] = ('PASS_3_PAIRED_TRIALS' if len(report['trials']) == 6
                            else 'FAIL_INCOMPLETE_TRIALS')
        _write_json(OUT / 'run-result.json', report)
        return 0 if report['status'] == 'PASS_3_PAIRED_TRIALS' else 1
    except BaseException as error:
        report.update(status='FAIL_FIRST_OUTCOME_RETAINED',
                      error_type=type(error).__name__, error=str(error),
                      traceback=traceback.format_exc())
        _write_json(OUT / 'run-result.json', report)
        return 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))

