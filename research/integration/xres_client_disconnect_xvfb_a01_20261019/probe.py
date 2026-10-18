"""Bounded Xvfb probe for exact XRes client disappearance after owner death."""
import argparse
import json
import os
import platform
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


REPO = Path('/repo')
sys.path.insert(0, str(REPO))


def _wait_for_file(path, timeout_s=5.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if Path(path).exists():
            return
        time.sleep(0.005)
    raise TimeoutError('timed out waiting for ' + str(path))


def _wait_for_process_state(pid, stopped, timeout_s=2.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        stat = Path(f'/proc/{pid}/stat').read_text(encoding='ascii')
        state = stat.rsplit(')', 1)[1].strip().split()[0]
        if (state in ('T', 't')) == stopped:
            return state
        time.sleep(0.005)
    raise TimeoutError('Xvfb did not reach requested process state')


def _write_json(path, payload):
    Path(path).write_text(json.dumps(payload, sort_keys=True), encoding='utf-8')


def _owner_process(display_name, directory, keycode):
    from Xlib import X, display
    from Xlib.ext import xtest

    root = Path(directory)
    connection = display.Display(display_name)
    base = connection.display.info.resource_id_base
    _write_json(root/'owner-ready.json', {
        'pid':os.getpid(), 'resource_base':base,
    })
    _wait_for_file(root/'send-press')
    xtest.fake_input(connection, X.KeyPress, keycode)
    connection.flush()
    (root/'press-flushed').write_text('1', encoding='ascii')
    (root/'sync-entered').write_text('1', encoding='ascii')
    connection.sync()
    (root/'sync-returned').write_text('1', encoding='ascii')


def _query_worker(display_name, directory, resource_base):
    from Xlib import display
    from Xlib.ext import res
    from runtime.guarded_x11_v1.xres_client_fence import client_is_connected

    root = Path(directory)
    connection = display.Display(display_name)
    _write_json(root/'query-ready.json', {
        'pid':os.getpid(),
        'resource_base':connection.display.info.resource_id_base,
        'target_resource_base':resource_base,
    })
    _wait_for_file(root/'send-query')
    (root/'query-entered').write_text('1', encoding='ascii')
    connected = client_is_connected(connection, resource_base)
    _write_json(root/'query-returned.json', {'target_connected':connected})


def _is_down(connection, keycode):
    keymap = connection.query_keymap()
    return bool(keymap[keycode // 8] & (1 << (keycode % 8)))


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


def _run_trials(trials):
    from Xlib import X, display
    from Xlib.ext import res, xtest
    from runtime.guarded_x11_v1.xres_client_fence import (
        client_is_connected,
        wait_for_client_disconnect,
    )

    display_name = ':91'
    keycode = 250
    server_log = tempfile.NamedTemporaryFile(prefix='xvfb-', delete=False)
    server_log_path = server_log.name
    server_log.close()
    server = subprocess.Popen([
        'Xvfb', display_name, '-screen', '0', '800x600x24',
        '-nolisten', 'tcp', '-noreset',
    ], stdout=open(server_log_path, 'wb'), stderr=subprocess.STDOUT)
    observer = None
    rows = []
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError('Xvfb exited during startup')
            try:
                observer = display.Display(display_name)
                break
            except Exception:
                time.sleep(0.025)
        if observer is None:
            raise TimeoutError('Xvfb did not accept a local client')
        if not observer.has_extension('X-Resource') or not observer.has_extension('XTEST'):
            raise RuntimeError('XRes and XTEST extensions are required')
        version = _bounded_call(observer.res_query_version)
        if (type(version.server_major) is not int or version.server_major < 1):
            raise RuntimeError('XRes 1.0 or later required')

        for index in range(trials):
            with tempfile.TemporaryDirectory(prefix='xres-owner-') as td:
                root = Path(td)
                owner = subprocess.Popen([
                    sys.executable, __file__, '--owner', display_name,
                    str(root), str(keycode),
                ])
                query_worker = None
                paused = False
                try:
                    _wait_for_file(root/'owner-ready.json')
                    owner_row = json.loads((root/'owner-ready.json').read_text(encoding='utf-8'))
                    resource_base = owner_row['resource_base']
                    query_worker = subprocess.Popen([
                        sys.executable, __file__, '--query-worker', display_name,
                        str(root), str(resource_base),
                    ])
                    _wait_for_file(root/'query-ready.json')
                    query_row = json.loads((root/'query-ready.json').read_text(encoding='utf-8'))
                    query_base = query_row['resource_base']
                    if not _bounded_call(client_is_connected, observer, resource_base):
                        raise AssertionError('owner client missing before server pause')
                    observer_base = observer.display.info.resource_id_base
                    if len({observer_base, resource_base, query_base}) != 3:
                        raise AssertionError('observer, owner and query worker need distinct client bases')
                    if _bounded_call(_is_down, observer, keycode):
                        raise AssertionError('key was already down before the trial')

                    os.kill(server.pid, signal.SIGSTOP)
                    paused = True
                    _wait_for_process_state(server.pid, stopped=True)
                    (root/'send-press').write_text('1', encoding='ascii')
                    _wait_for_file(root/'press-flushed')
                    _wait_for_file(root/'sync-entered')
                    time.sleep(0.05)
                    if owner.poll() is not None:
                        raise AssertionError('owner unexpectedly returned from sync while Xvfb stopped')
                    if (root/'sync-returned').exists():
                        raise AssertionError('owner sync returned while Xvfb stopped')

                    (root/'send-query').write_text('1', encoding='ascii')
                    _wait_for_file(root/'query-entered')
                    time.sleep(0.05)
                    query_was_blocked = (
                        query_worker.poll() is None
                        and not (root/'query-returned.json').exists())
                    if not query_was_blocked:
                        raise AssertionError('XRes request returned while Xvfb stopped')
                    query_kill_started = time.monotonic()
                    query_worker.kill()
                    query_worker.wait(timeout=2)
                    query_retire_ms = (time.monotonic() - query_kill_started) * 1000

                    owner_kill_started = time.monotonic()
                    owner.kill()
                    owner.wait(timeout=2)
                    owner_retire_ms = (time.monotonic() - owner_kill_started) * 1000
                    server_resume_started = time.monotonic()
                    os.kill(server.pid, signal.SIGCONT)
                    paused = False
                    _wait_for_process_state(server.pid, stopped=False)

                    disconnected = _bounded_call(
                        wait_for_client_disconnect, observer, resource_base,
                        timeout_s=3.0, poll_interval_s=0.005)
                    if not disconnected:
                        raise TimeoutError('XRes continued listing the dead owner client')

                    owner_sync_returned = (root/'sync-returned').exists()
                    down_at_fence = _bounded_call(_is_down, observer, keycode)
                    row = {
                        'trial':index + 1,
                        'owner_pid':owner_row['pid'],
                        'owner_resource_base':resource_base,
                        'query_worker_resource_base':query_base,
                        'observer_resource_base':observer_base,
                        'owner_sync_returned':owner_sync_returned,
                        'xres_query_was_blocked_while_server_stopped':query_was_blocked,
                        'query_worker_retire_ms':round(query_retire_ms, 3),
                        'owner_retire_ms':round(owner_retire_ms, 3),
                        'owner_absent_from_xres':True,
                        'server_resume_to_disconnect_fence_ms':round(
                            (time.monotonic() - server_resume_started) * 1000, 3),
                        'key_down_at_disconnect_fence':down_at_fence,
                    }
                    if owner_sync_returned:
                        raise AssertionError('owner sync returned despite server pause')
                    if not down_at_fence:
                        print(json.dumps(row, sort_keys=True), flush=True)
                        raise AssertionError('queued DOWN was not observed at disconnect fence')

                    xtest.fake_input(observer, X.KeyRelease, keycode)
                    _bounded_call(observer.sync)
                    down_after_release = _bounded_call(_is_down, observer, keycode)
                    time.sleep(0.05)
                    down_after_settle = _bounded_call(_is_down, observer, keycode)
                    row['key_down_after_independent_release'] = down_after_release
                    row['key_down_after_50ms_settle'] = down_after_settle
                    print(json.dumps(row, sort_keys=True), flush=True)
                    if down_after_release or down_after_settle:
                        raise AssertionError('independent UP/readback left a late key-down')
                    rows.append(row)
                finally:
                    if query_worker is not None and query_worker.poll() is None:
                        query_worker.kill()
                        query_worker.wait(timeout=2)
                    if owner.poll() is None:
                        owner.kill()
                        owner.wait(timeout=2)
                    if paused and server.poll() is None:
                        os.kill(server.pid, signal.SIGCONT)

        return {
            'status':'PASS_XVFB_CLIENT_DISCONNECT_AND_RELEASE_SCOPED',
            'xres_version':[version.server_major, version.server_minor],
            'xserver_vendor':observer.display.info.vendor,
            'xserver_release':observer.display.info.release_number,
            'xvfb_display':display_name,
            'xvfb_pid':server.pid,
            'keycode':keycode,
            'trial_count':len(rows),
            'disconnected_before_release':all(r['owner_absent_from_xres'] for r in rows),
            'all_releases_verified':all(not r['key_down_after_independent_release'] for r in rows),
            'no_late_down_after_settle':all(not r['key_down_after_50ms_settle'] for r in rows),
            'trials':rows,
        }
    finally:
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
    subprocess.run([
        'apt-get', 'install', '-y', '--no-install-recommends', 'xvfb',
    ], check=True, timeout=180)
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
        'python-xlib==0.33',
    ], check=True, timeout=90)
    print(json.dumps({
        'python':platform.python_version(),
        'machine':platform.machine(),
        'os_release':Path('/etc/os-release').read_text(encoding='utf-8').strip(),
        'xvfb_package':subprocess.check_output(
            ['dpkg-query', '-W', '-f=${Version}', 'xvfb'], text=True).strip(),
        'python_xlib_version':subprocess.check_output(
            [sys.executable, '-c', "from importlib.metadata import version; print(version('python-xlib'))"],
            text=True).strip(),
    }, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner', action='store_true')
    parser.add_argument('--query-worker', action='store_true')
    parser.add_argument('display_name', nargs='?')
    parser.add_argument('directory', nargs='?')
    parser.add_argument('keycode', nargs='?', type=int)
    parser.add_argument('--trials', type=int, default=8)
    args = parser.parse_args()
    if args.owner:
        _owner_process(args.display_name, args.directory, args.keycode)
        return
    if args.query_worker:
        _query_worker(args.display_name, args.directory, args.keycode)
        return
    if type(args.trials) is not int or not 1 <= args.trials <= 32:
        raise ValueError('trials must be between 1 and 32')
    _install_dependencies()
    result = _run_trials(args.trials)
    print(json.dumps(result, sort_keys=True), flush=True)
    if not all((result['disconnected_before_release'],
                result['all_releases_verified'],
                result['no_late_down_after_settle'])):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
