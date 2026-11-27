"""Bounded Xvfb probe: held input, blocked owner reply, independent release."""
import argparse
import json
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time


REPO = Path('/repo')
sys.path.insert(0, str(REPO))


def _write_json(path, payload):
    Path(path).write_text(json.dumps(payload, sort_keys=True), encoding='utf-8')


def _wait_for_file(path, timeout_s=5.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if Path(path).exists():
            return json.loads(Path(path).read_text(encoding='utf-8'))
        time.sleep(0.005)
    raise TimeoutError('timed out waiting for ' + str(path))


def _raise_timeout(_signum, _frame):
    raise TimeoutError('X server request exceeded the process watchdog')


def _bounded_call(call, *args, watchdog_s=15, **kwargs):
    previous = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(watchdog_s)
    try:
        return call(*args, **kwargs)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def _owner_process(display_name, directory, keycode):
    from Xlib import X, display
    from Xlib.ext import xtest

    root = Path(directory)
    connection = display.Display(display_name)
    base = connection.display.info.resource_id_base
    _write_json(root/'owner-ready.json', {'pid':os.getpid(), 'resource_base':base})
    _wait_for_file(root/'send-press')
    xtest.fake_input(connection, X.KeyPress, keycode)
    connection.flush()
    (root/'press-flushed').write_text('1', encoding='ascii')
    (root/'sync-entered').write_text('1', encoding='ascii')
    connection.sync()
    (root/'sync-returned').write_text('1', encoding='ascii')


def _task_receiver(display_name, directory, keycode):
    from Xlib import X, display

    root = Path(directory)
    connection = display.Display(display_name)
    screen = connection.screen()
    # Use the focused root as the smallest event target after A07 showed
    # keymap state changing without a selected-window KeyPress event.
    window = screen.root
    window.change_attributes(
        event_mask=X.KeyPressMask | X.KeyReleaseMask)
    connection.set_input_focus(window, X.RevertToParent, X.CurrentTime)
    connection.sync()
    focus = connection.get_input_focus().focus
    focus_id = getattr(focus, 'id', focus)
    attributes = window.get_attributes()
    _write_json(root/'task-ready.json', {
        'window_id':window.id,
        'input_focus_id':int(focus_id),
        'receiver_event_mask':int(attributes.your_event_mask),
        'map_state':int(attributes.map_state),
    })

    while True:
        event = connection.next_event()
        if event.type not in (X.KeyPress, X.KeyRelease):
            continue
        with open(root/'receiver-key-events.jsonl', 'a', encoding='utf-8') as log:
            log.write(json.dumps({
                'type':int(event.type),
                'detail':int(event.detail),
                'window_id':int(event.window.id),
                'send_event':bool(event.send_event),
                'time':int(event.time),
            }, sort_keys=True) + '\n')
        if event.detail != keycode:
            continue
        trial_path = root/'current-trial'
        if not trial_path.exists():
            continue
        trial = int(trial_path.read_text(encoding='ascii'))
        kind = 'press' if event.type == X.KeyPress else 'release'
        _write_json(root/f'trial-{trial:02d}-{kind}.json', {
            'event_type':kind,
            'keycode':event.detail,
            'window_id':event.window.id,
            'event_time':event.time,
        })


class UnixReplyProxy:
    """Forward X11 requests, gate only replies to the owner process."""

    def __init__(self, listen_path, upstream_path):
        self.listen_path = listen_path
        self.upstream_path = upstream_path
        if os.path.exists(listen_path):
            raise FileExistsError('proxy socket path already exists')
        self.allow_replies = threading.Event()
        self.allow_replies.set()
        self.ready = threading.Event()
        self.closed = threading.Event()
        self.errors = []
        self.byte_counts = {'owner_to_server':0, 'server_to_owner':0}
        self.lock = threading.Lock()
        self.reply_gate_lock = threading.Lock()
        self.withheld_server_to_owner_bytes = 0
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(listen_path)
        self.listener.listen(1)
        self.client = None
        self.upstream = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def block_replies(self):
        # Linearize gate closure against each downstream send. Once this
        # returns, no later server bytes can reach the owner until reopened.
        with self.reply_gate_lock:
            self.allow_replies.clear()

    def wait_for_withheld_reply(self, timeout_s=3.0):
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.withheld_server_to_owner_bytes > 0:
                return True
            if self.closed.is_set():
                return False
            time.sleep(0.005)
        return False

    def _pump(self, source, destination, direction):
        try:
            while not self.closed.is_set():
                if direction == 'server_to_owner' and not self.allow_replies.wait(0.05):
                    continue
                try:
                    data = source.recv(65536)
                except socket.timeout:
                    continue
                if not data:
                    return
                if direction == 'server_to_owner':
                    withheld = False
                    sent = False
                    while not self.closed.is_set():
                        with self.reply_gate_lock:
                            if self.allow_replies.is_set():
                                destination.sendall(data)
                                with self.lock:
                                    self.byte_counts[direction] += len(data)
                                sent = True
                        if sent:
                            break
                        if not withheld:
                            with self.lock:
                                self.withheld_server_to_owner_bytes += len(data)
                            withheld = True
                        self.allow_replies.wait(0.05)
                    if not sent:
                        return
                else:
                    destination.sendall(data)
                    with self.lock:
                        self.byte_counts[direction] += len(data)
        except (OSError, ValueError) as exc:
            if not self.closed.is_set():
                self.errors.append(type(exc).__name__ + ': ' + str(exc))
        finally:
            self.closed.set()
            for conn in (self.client, self.upstream):
                if conn is not None:
                    try:
                        conn.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    try:
                        conn.close()
                    except OSError:
                        pass

    def _run(self):
        try:
            self.client, _ = self.listener.accept()
            self.upstream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.upstream.connect(self.upstream_path)
            self.client.settimeout(0.1)
            self.upstream.settimeout(0.1)
            self.ready.set()
            toward_server = threading.Thread(
                target=self._pump,
                args=(self.client, self.upstream, 'owner_to_server'), daemon=True)
            toward_owner = threading.Thread(
                target=self._pump,
                args=(self.upstream, self.client, 'server_to_owner'), daemon=True)
            toward_server.start()
            toward_owner.start()
            toward_server.join()
            toward_owner.join(timeout=2)
        except (OSError, ValueError) as exc:
            self.errors.append(type(exc).__name__ + ': ' + str(exc))
            self.ready.set()
            self.closed.set()

    def stop(self):
        self.closed.set()
        self.allow_replies.set()
        for conn in (self.listener, self.client, self.upstream):
            if conn is not None:
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    conn.close()
                except OSError:
                    pass
        self.thread.join(timeout=2)
        try:
            os.unlink(self.listen_path)
        except FileNotFoundError:
            pass


def _is_down(connection, keycode):
    keymap = connection.query_keymap()
    return bool(keymap[keycode // 8] & (1 << (keycode % 8)))


def _wait_for_key_state(connection, keycode, expected, timeout_s=3.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _bounded_call(_is_down, connection, keycode) is expected:
            return True
        time.sleep(0.01)
    return False


def _run_trials(trials):
    from Xlib import X, display
    from Xlib.ext import res, xtest
    from Xlib.protocol import event as protocol_event
    from runtime.guarded_x11_v1.xres_client_fence import (
        client_is_connected,
        wait_for_client_disconnect,
    )

    server_display = ':91'
    owner_display = ':92'
    keycode = 38
    server_socket = '/tmp/.X11-unix/X91'
    owner_socket = '/tmp/.X11-unix/X92'
    server_log = tempfile.NamedTemporaryFile(prefix='xvfb-', delete=False)
    server_log_path = server_log.name
    server_log.close()
    with open(server_log_path, 'wb') as log_handle:
        server = subprocess.Popen([
            'Xvfb', server_display, '-screen', '0', '800x600x24',
            '-nolisten', 'tcp', '-noreset',
        ], stdout=log_handle, stderr=subprocess.STDOUT)

    observer = None
    task = None
    rows = []
    temporary = None
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError('Xvfb exited during startup')
            try:
                observer = display.Display(server_display)
                break
            except Exception:
                time.sleep(0.025)
        if observer is None:
            raise TimeoutError('Xvfb did not accept an observer client')
        if not observer.has_extension('X-Resource') or not observer.has_extension('XTEST'):
            raise RuntimeError('XRes and XTEST extensions are required')
        version = _bounded_call(observer.res_query_version)

        temporary = tempfile.TemporaryDirectory(prefix='xres-task-')
        root = Path(temporary.name)
        task = subprocess.Popen([
            sys.executable, __file__, '--task-receiver', server_display,
            str(root), str(keycode),
        ])
        task_row = _wait_for_file(root/'task-ready.json')
        if task_row['input_focus_id'] != task_row['window_id']:
            raise AssertionError('task receiver window does not own input focus')

        # Verify the receiver loop with SendEvent. This is only a plumbing
        # control and is never counted as task effect or XTEST input.
        target = observer.create_resource_object(
            'window', task_row['window_id'])
        (root/'current-trial').write_text('99', encoding='ascii')
        synthetic_press = protocol_event.KeyPress(
            time=X.CurrentTime,
            root=target,
            window=target,
            child=X.NONE,
            root_x=0,
            root_y=0,
            event_x=0,
            event_y=0,
            state=0,
            detail=keycode,
            same_screen=1,
        )
        target.send_event(
            synthetic_press, event_mask=X.KeyPressMask, propagate=False)
        _bounded_call(observer.sync)
        receiver_pipe_control = _wait_for_file(
            root/'trial-99-press.json')

        # Separately require actual XTEST state and receiver event before
        # exposing any blocked-owner trial.
        (root/'current-trial').write_text('0', encoding='ascii')
        xtest.fake_input(observer, X.KeyPress, keycode)
        _bounded_call(observer.sync)
        try:
            control_press = _wait_for_file(root/'trial-00-press.json')
        except TimeoutError:
            focus = _bounded_call(observer.get_input_focus).focus
            focus_id = int(getattr(focus, 'id', focus))
            target_window = observer.create_resource_object(
                'window', task_row['window_id'])
            attributes = _bounded_call(target_window.get_attributes)
            diagnostic = {
                'input_focus_id_after_control_timeout':focus_id,
                'receiver_focus_id_at_ready':task_row['input_focus_id'],
                'receiver_event_mask_at_ready':task_row['receiver_event_mask'],
                'receiver_map_state_at_ready':task_row['map_state'],
                'target_map_state_after_control_timeout':int(attributes.map_state),
                'key_down_after_control_timeout':_bounded_call(
                    _is_down, observer, keycode),
                'keycode_range':[
                    int(observer.display.info.min_keycode),
                    int(observer.display.info.max_keycode),
                ],
                'keycode_mapping':[int(value) for value in
                                   _bounded_call(observer.get_keyboard_mapping,
                                                 keycode, 1)[0]],
                'receiver_key_events':(
                    (root/'receiver-key-events.jsonl').read_text(
                        encoding='utf-8').splitlines()
                    if (root/'receiver-key-events.jsonl').exists() else []),
            }
            print(json.dumps({
                'status':'RECEIVER_CONTROL_TIMEOUT',
                'task_ready':task_row,
                'diagnostic':diagnostic,
            }, sort_keys=True), flush=True)
            raise
        control_down = _wait_for_key_state(observer, keycode, True)
        xtest.fake_input(observer, X.KeyRelease, keycode)
        _bounded_call(observer.sync)
        control_release = _wait_for_file(root/'trial-00-release.json')
        control_up = not _bounded_call(_is_down, observer, keycode)
        if (control_press['window_id'] != task_row['window_id']
                or control_release['window_id'] != task_row['window_id']
                or not control_down or not control_up):
            raise AssertionError('direct receiver control failed')
        receiver_control = {
            'passed':True,
            'input_focus_id':task_row['input_focus_id'],
            'receiver_event_mask':task_row['receiver_event_mask'],
            'map_state':task_row['map_state'],
            'synthetic_send_event_plumbing_only':receiver_pipe_control,
            'press':control_press,
            'key_down_after_press':control_down,
            'release':control_release,
            'key_down_after_release':not control_up,
        }
        observer_base = observer.display.info.resource_id_base
        for index in range(trials):
            trial = index + 1
            (root/'current-trial').write_text(str(trial), encoding='ascii')
            if _bounded_call(_is_down, observer, keycode):
                raise AssertionError('key was already down before trial')

            proxy = UnixReplyProxy(owner_socket, server_socket).start()
            owner = subprocess.Popen([
                sys.executable, __file__, '--owner', owner_display,
                str(root), str(keycode),
            ])
            try:
                owner_row = _wait_for_file(root/'owner-ready.json')
                resource_base = owner_row['resource_base']
                if resource_base == observer_base:
                    raise AssertionError('observer and owner client bases must differ')
                if not _bounded_call(client_is_connected, observer, resource_base):
                    raise AssertionError('owner missing from XRes before input')
                if not proxy.ready.wait(3.0) or proxy.errors:
                    raise RuntimeError('reply proxy did not establish its X11 relay')

                setup_bytes = proxy.byte_counts['server_to_owner']
                if setup_bytes == 0:
                    raise AssertionError('X11 setup reply did not traverse proxy')
                proxy.block_replies()
                owner_bytes_before_press = proxy.byte_counts['owner_to_server']
                (root/'send-press').write_text('1', encoding='ascii')
                _wait_for_file(root/'press-flushed')
                _wait_for_file(root/'sync-entered')

                if not proxy.wait_for_withheld_reply(timeout_s=3.0):
                    diagnostic = {
                        'owner_still_running':owner.poll() is None,
                        'owner_sync_returned':(root/'sync-returned').exists(),
                        'key_down':_bounded_call(_is_down, observer, keycode),
                        'owner_to_server_bytes_before_press':owner_bytes_before_press,
                        'owner_to_server_bytes_after_sync':proxy.byte_counts['owner_to_server'],
                        'server_to_owner_bytes_forwarded':proxy.byte_counts['server_to_owner'],
                        'server_to_owner_bytes_withheld':proxy.withheld_server_to_owner_bytes,
                        'proxy_errors':list(proxy.errors),
                    }
                    print(json.dumps({
                        'trial':trial,
                        'status':'OWNER_REPLY_NOT_HELD',
                        'diagnostic':diagnostic,
                    }, sort_keys=True), flush=True)
                    raise TimeoutError('no server reply was held by the closed gate')

                press_path = root/f'trial-{trial:02d}-press.json'
                try:
                    press_receipt = _wait_for_file(press_path, timeout_s=3.0)
                except TimeoutError:
                    diagnostic = {
                        'task_press_receipt_exists':press_path.exists(),
                        'key_down':_bounded_call(_is_down, observer, keycode),
                        'owner_still_running':owner.poll() is None,
                        'owner_sync_returned':(root/'sync-returned').exists(),
                        'owner_to_server_bytes':proxy.byte_counts['owner_to_server'],
                        'owner_client_still_connected':_bounded_call(
                            client_is_connected, observer, resource_base),
                        'proxy_errors':list(proxy.errors),
                    }
                    print(json.dumps({
                        'trial':trial,
                        'status':'NOT_ESTABLISHED_TASK_EVENT_TIMEOUT',
                        'receiver_control':receiver_control,
                        'diagnostic':diagnostic,
                    }, sort_keys=True), flush=True)
                    raise
                if press_receipt['keycode'] != keycode:
                    raise AssertionError('task recipient observed the wrong keycode')
                if press_receipt['window_id'] != task_row['window_id']:
                    raise AssertionError('KeyPress reached an unexpected target window')
                if not _wait_for_key_state(observer, keycode, True):
                    raise AssertionError('keymap did not show the task KeyPress')
                time.sleep(0.05)
                owner_blocked = (
                    owner.poll() is None
                    and not (root/'sync-returned').exists())
                if not owner_blocked:
                    raise AssertionError('owner XSync was not blocked by withheld reply')

                owner_kill_started = time.monotonic()
                owner.kill()
                owner.wait(timeout=2)
                owner_retire_ms = (time.monotonic() - owner_kill_started) * 1000
                disconnected = _bounded_call(
                    wait_for_client_disconnect, observer, resource_base,
                    timeout_s=3.0, poll_interval_s=0.005)
                if not disconnected:
                    raise TimeoutError('exact owner client remained in XRes')
                disconnect_ms = (time.monotonic() - owner_kill_started) * 1000
                down_at_fence = _bounded_call(_is_down, observer, keycode)
                row = {
                    'trial':trial,
                    'owner_resource_base':resource_base,
                    'observer_resource_base':observer_base,
                    'task_window_id':task_row['window_id'],
                    'owner_sync_returned':(root/'sync-returned').exists(),
                    'owner_xsync_blocked_on_withheld_reply':owner_blocked,
                    'task_keypress':press_receipt,
                    'proxy_setup_reply_bytes':setup_bytes,
                        'proxy_server_to_owner_bytes_withheld':proxy.withheld_server_to_owner_bytes,
                    'proxy_owner_to_server_bytes':proxy.byte_counts['owner_to_server'],
                    'proxy_errors_before_retirement':list(proxy.errors),
                    'owner_retire_ms':round(owner_retire_ms, 3),
                    'disconnect_fence_ms_from_kill':round(disconnect_ms, 3),
                    'owner_absent_from_xres':True,
                    'key_down_at_disconnect_fence':down_at_fence,
                }
                if not down_at_fence:
                    print(json.dumps(row, sort_keys=True), flush=True)
                    raise AssertionError('task effect was not held at disconnect fence')

                release_started = time.monotonic()
                xtest.fake_input(observer, X.KeyRelease, keycode)
                _bounded_call(observer.sync)
                release_path = root/f'trial-{trial:02d}-release.json'
                release_receipt = _wait_for_file(release_path, timeout_s=3.0)
                if release_receipt['keycode'] != keycode:
                    raise AssertionError('task recipient observed the wrong release keycode')
                if release_receipt['window_id'] != task_row['window_id']:
                    raise AssertionError('KeyRelease reached an unexpected target window')
                down_after_release = _bounded_call(_is_down, observer, keycode)
                time.sleep(0.05)
                down_after_settle = _bounded_call(_is_down, observer, keycode)
                row.update({
                    'independent_keyrelease':release_receipt,
                    'release_readback_ms':round((time.monotonic()-release_started)*1000,3),
                    'key_down_after_independent_release':down_after_release,
                    'key_down_after_50ms_settle':down_after_settle,
                })
                print(json.dumps(row, sort_keys=True), flush=True)
                if down_after_release or down_after_settle:
                    raise AssertionError('independent UP did not leave the key up')
                rows.append(row)
            finally:
                if owner.poll() is None:
                    owner.kill()
                    owner.wait(timeout=2)
                if _bounded_call(_is_down, observer, keycode):
                    try:
                        xtest.fake_input(observer, X.KeyRelease, keycode)
                        _bounded_call(observer.sync)
                    except Exception:
                        pass
                proxy.stop()

        return {
            'status':'PASS_XVFB_BLOCKED_OWNER_RELEASE_SCOPED',
            'receiver_control':receiver_control,
            'xres_version':[version.server_major, version.server_minor],
            'xserver_vendor':observer.display.info.vendor,
            'xserver_release':observer.display.info.release_number,
            'xvfb_display':server_display,
            'owner_proxy_display':owner_display,
            'keycode':keycode,
            'trial_count':len(rows),
            'all_task_press_events':all(r['task_keypress']['event_type']=='press' for r in rows),
            'all_owner_clients_absent_before_release':all(r['owner_absent_from_xres'] for r in rows),
            'all_releases_verified':all(not r['key_down_after_independent_release'] for r in rows),
            'no_late_down_after_settle':all(not r['key_down_after_50ms_settle'] for r in rows),
            'trials':rows,
        }
    finally:
        if task is not None and task.poll() is None:
            task.terminate()
            try:
                task.wait(timeout=2)
            except subprocess.TimeoutExpired:
                task.kill()
                task.wait(timeout=2)
        if temporary is not None:
            temporary.cleanup()
        if observer is not None:
            observer.close()
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)
        Path(server_log_path).unlink(missing_ok=True)


def _install_dependencies():
    subprocess.run(['apt-get', 'update'], check=True, timeout=180)
    subprocess.run(['apt-get', 'install', '-y', '--no-install-recommends', 'xvfb'],
                   check=True, timeout=180)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                    'python-xlib==0.33'], check=True, timeout=90)
    print(json.dumps({
        'python':platform.python_version(),
        'machine':platform.machine(),
        'os_release':Path('/etc/os-release').read_text(encoding='utf-8').strip(),
        'xvfb_package':subprocess.check_output(
            ['dpkg-query', '-W', '-f=${Version}', 'xvfb'], text=True).strip(),
        'xserver_common_package':subprocess.check_output(
            ['dpkg-query', '-W', '-f=${Version}', 'xserver-common'], text=True).strip(),
        'python_xlib_version':subprocess.check_output(
            [sys.executable, '-c',
             "from importlib.metadata import version; print(version('python-xlib'))"],
            text=True).strip(),
    }, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner', action='store_true')
    parser.add_argument('--task-receiver', action='store_true')
    parser.add_argument('display_name', nargs='?')
    parser.add_argument('directory', nargs='?')
    parser.add_argument('keycode', nargs='?', type=int)
    parser.add_argument('--trials', type=int, default=8)
    args = parser.parse_args()
    if args.owner:
        _owner_process(args.display_name, args.directory, args.keycode)
        return
    if args.task_receiver:
        _task_receiver(args.display_name, args.directory, args.keycode)
        return
    if type(args.trials) is not int or not 1 <= args.trials <= 32:
        raise ValueError('trials must be between 1 and 32')
    _install_dependencies()
    result = _run_trials(args.trials)
    print(json.dumps(result, sort_keys=True), flush=True)
    if not all((result['receiver_control']['passed'],
                result['all_task_press_events'],
                result['all_owner_clients_absent_before_release'],
                result['all_releases_verified'],
                result['no_late_down_after_settle'])):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
