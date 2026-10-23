"""One native-WSL2 standard-caller cancellation/recovery trial on two xterms."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def verify_frozen_sources():
    manifest = json.loads((HERE / 'SOURCES.json').read_text())
    for name, expected in manifest.items():
        actual = hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if actual != expected:
            raise RuntimeError(f'frozen source mismatch: {name}')


def verify_native_binaries():
    rows = json.loads((HERE/'native-binaries.json').read_text())
    results = []
    for row in rows:
        path = Path(row['path']).resolve(strict=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        results.append({'path':row['path'],'sha256':digest,'matches':digest == row['sha256']})
        if digest != row['sha256']:
            raise RuntimeError(f'native binary changed: {row["path"]}')
    return results


async def wait_until(predicate, timeout, name):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        await asyncio.sleep(.01)
    raise TimeoutError(name)


def metadata(reply):
    return json.loads(reply.content[0].text)


def journal(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def keymap(display_name):
    from Xlib import display
    connection = display.Display(display_name)
    try:
        return bytes(connection.query_keymap()).hex()
    finally:
        connection.close()


def launch_xterm(bundle, title, journal_path, auth, base):
    home = base / 'home'
    home.mkdir()
    binpath = base / 'bin'
    binpath.mkdir()
    shutil.copyfile(HERE / 'record_helper.py', binpath / 'record')
    (binpath / 'record').chmod(0o700)
    rc = base / 'shellrc'
    rc.write_text("PS1='READY> '; export PS1\numask 077\n")
    env = {
        'DISPLAY': ':188', 'XAUTHORITY': str(auth),
        'HOME': str(home), 'ENV': str(rc),
        'PATH': str(binpath) + ':/usr/bin:/bin',
        'LD_LIBRARY_PATH': str(bundle / 'usr/lib/x86_64-linux-gnu'),
        'XAPPLRESDIR': str(bundle / 'etc/X11/app-defaults'),
        'XDG_CACHE_HOME': str(home / '.cache'),
        'AI_TASK_JOURNAL': str(journal_path),
        'LANG': 'C.UTF-8', 'TERM': 'xterm',
    }
    command = [str(bundle / 'usr/bin/xterm'), '-ut', '+bc', '-fn', 'fixed',
        '-geometry', '80x24+20+20', '-title', title, '-e', '/bin/sh', '-i']
    log = (base / 'xterm.log').open('wb')
    process = subprocess.Popen(command, env=env, cwd=home, stdout=log,
        stderr=subprocess.STDOUT, start_new_session=True)
    return process, log, env, command


async def find_window(connection, title, process, timeout=5):
    from Xlib import X
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if process.poll() is not None:
            raise RuntimeError(f'xterm exited early: {process.returncode}')
        for window in connection.screen().root.query_tree().children:
            if window.get_wm_name() == title and window.get_attributes().map_state == X.IsViewable:
                return window
        await asyncio.sleep(.05)
    raise TimeoutError('mapped xterm not found')


async def public_setup(connection, window, server, report, label):
    from PIL import Image, ImageStat
    observed = metadata(await server.call_tool('interface_guarded_observe', {}))
    if observed.get('status') != 'observed':
        raise RuntimeError(f'{label} observation failed: {observed}')
    binding = observed['source']['pointer_binding']
    report[label + '_observation'] = {
        'session_id': observed['session']['session_id'],
        'sequence': observed['source']['sequence'],
        'binding': binding,
    }
    geometry = window.get_geometry()
    point = [geometry.x + 18, geometry.y + 14]
    image_path = observed['observation_report']['observation']['artifact']['path']
    image = Image.open(image_path).convert('RGB')
    patch = image.crop((point[0]-12, point[1]-12, point[0]+12, point[1]+12))
    stddev = ImageStat.Stat(patch).stddev
    if max(stddev) < 8:
        raise RuntimeError(f'{label} prompt anchor lacks texture: {stddev}')
    minted = metadata(await server.call_tool('interface_guarded_mint', {
        'alias':'prompt', 'source_sequence':observed['source']['sequence'],
        'point':point, 'region_size':[24, 24]}))
    if minted.get('status') != 'minted':
        raise RuntimeError(f'{label} mint failed: {minted}')
    return minted, geometry


async def call_until_terminal(server, call_id, timeout=5):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        row = metadata(await server.call_tool('interface_results', {
            'call_id':call_id, 'include_image':False}))
        if row.get('status') != 'pending':
            return row
        await asyncio.sleep(.05)
    return row


def terminate_owned(process, pidfd, log):
    row = {'pid':process.pid, 'pidfd_target':int(Path(f'/proc/self/fdinfo/{pidfd}').read_text().split('Pid:\t')[1].splitlines()[0])}
    try:
        if row['pid'] != row['pidfd_target'] or os.getpgid(process.pid) != process.pid:
            raise RuntimeError('owned xterm process/session identity changed')
        row['initial_session_pids'] = pids_in_group(process.pid)
        os.killpg(process.pid, signal.SIGTERM)
        row['signal'] = 'SIGTERM to the private xterm session while leader pidfd was retained'
        row['exit_code'] = process.wait(timeout=5)
        end = time.monotonic() + 3
        while time.monotonic() < end and pids_in_group(process.pid):
            time.sleep(.05)
        row['remaining_session_pids'] = pids_in_group(process.pid)
        if row['remaining_session_pids']:
            os.killpg(process.pid, signal.SIGKILL)
            end = time.monotonic() + 3
            while time.monotonic() < end and pids_in_group(process.pid):
                time.sleep(.05)
            row['post_kill_session_pids'] = pids_in_group(process.pid)
    except BaseException as error:
        row['error'] = repr(error)
        try:
            signal.pidfd_send_signal(pidfd, signal.SIGKILL)
            row['kill_exit_code'] = process.wait(timeout=5)
        except BaseException as second:
            row['kill_error'] = repr(second)
    finally:
        os.close(pidfd)
        log.close()
    return row


def pids_in_group(pgid):
    members = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry/'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == pgid:
                members.append(int(entry.name))
        except (OSError, ValueError, IndexError):
            continue
    return sorted(members)


async def run_trial():
    from Xlib import X, display
    from runtime.cli_v1.mcp_server import create_server
    from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _xvfb_blocking_owner_factory

    verify_frozen_sources()
    report_native_preflight = verify_native_binaries()
    conditions = json.loads((HERE / 'conditions.json').read_text())
    bundle = Path(conditions['xterm_bundle'])
    report = {'schema':'agent-interface/xterm-cancel-recovery-v1', 'status':'RUNNING',
        'conditions':conditions, 'started_ns':time.monotonic_ns(), 'model_calls':0,
        'python_executable':sys.executable, 'python_version':sys.version,
        'native_preflight':report_native_preflight,
        'old_effect_rows_at_cancel':None, 'old_effect_rows_at_horizon':None,
        'fresh_effect_rows_at_horizon':None, 'process_cleanup':{}}
    xvfb = None
    xvfb_fd = None
    xvfb_log = None
    previous_display = os.environ.get('DISPLAY')
    previous_xauthority = os.environ.get('XAUTHORITY')
    observer = None
    old_server = fresh_server = None
    old_terminal = fresh_terminal = None
    old_log = fresh_log = None
    old_pidfd = fresh_pidfd = None
    cleanup = []
    try:
        for path in ('/tmp/.X188-lock', '/tmp/.X11-unix/X188'):
            if Path(path).exists():
                raise RuntimeError('private display :188 is already occupied')
        auth_dir = Path(tempfile.mkdtemp(prefix='ai-xterm-recovery-auth-'))
        auth = auth_dir / 'Xauthority'
        auth.touch(mode=0o600)
        subprocess.run(['/usr/bin/xauth', '-f', str(auth), 'add', ':188', '.', secrets.token_hex(16)],
            check=True, timeout=5, capture_output=True)
        report['previous_display_environment'] = {
            'DISPLAY':previous_display,
            'XAUTHORITY_was_set':previous_xauthority is not None,
        }
        os.environ['DISPLAY'] = ':188'
        os.environ['XAUTHORITY'] = str(auth)
        xvfb_log = (HERE / 'xvfb.log').open('wb')
        xvfb = subprocess.Popen(['/usr/bin/Xvfb', ':188', '-screen', '0',
            '1024x768x24', '-nolisten', 'tcp', '-auth', str(auth)],
            stdout=xvfb_log, stderr=subprocess.STDOUT, start_new_session=True)
        xvfb_fd = os.pidfd_open(xvfb.pid)
        report['xvfb_pid'] = xvfb.pid
        report['xvfb_sha256'] = hashlib.sha256(Path('/usr/bin/Xvfb').read_bytes()).hexdigest()
        await asyncio.sleep(.5)
        if xvfb.poll() is not None:
            raise RuntimeError('private Xvfb exited before readiness')
        observer = display.Display(':188')
        report['xvfb_vendor'] = observer.display.info.vendor

        td = HERE / 'attempt'
        td.mkdir()
        old_base = td / 'old-xterm'
        old_journal = HERE / 'old-journal.jsonl'
        old_terminal, old_log, old_env, old_command = launch_xterm(
            bundle, conditions['old_target_title'], old_journal, auth, old_base)
        old_pidfd = os.pidfd_open(old_terminal.pid)
        old_window = await find_window(observer, conditions['old_target_title'], old_terminal)
        old_geo = old_window.get_geometry()
        report['old_app'] = {'pid':old_terminal.pid, 'command':old_command,
            'window_id':old_window.id, 'geometry':[old_geo.x,old_geo.y,old_geo.width,old_geo.height],
            'wm_class':old_window.get_wm_class(), 'journal':str(old_journal)}
        old_window.set_input_focus(X.RevertToParent, X.CurrentTime)
        observer.screen().root.warp_pointer(old_geo.x+18, old_geo.y+14)
        observer.sync()
        await asyncio.sleep(1)
        report['initial_keymap_hex'] = keymap(':188')
        owner_root = td / 'old-owner'
        old_server = create_server({'terminal':old_window.id}, owner_root,
            session_mode='guarded-x11', display_name=':188',
            guarded_process_identity=True, guarded_query_worker=True,
            guarded_window_lifecycle=True, guarded_owned_process=True,
            guarded_prestarted_cancel_supervisor=True,
            _guarded_owner_factory=_xvfb_blocking_owner_factory)
        minted, _ = await public_setup(observer, old_window, old_server, report, 'old')
        report['old_input_started_ns'] = time.monotonic_ns()
        old_input = metadata(await old_server.call_tool('interface_guarded_input', {
            'alias':'prompt', 'offset':minted['offset'], 'interaction':'keyboard',
            'observe_after':False, 'wait_for_result_ms':0,
            'tail':[{'op':'text','text':'record '+conditions['old_task_argument']},
                    {'op':'key_chord','keys':['Return']}]}))
        report['old_input_response'] = old_input
        if old_input.get('status') != 'pending':
            raise RuntimeError(f'old faulted input did not remain pending: {old_input}')
        old_call_id = old_input['call_id']
        owner_mcp = owner_root / 'mcp'
        marker = owner_mcp / 'xvfb-delayed-request-queued.json'
        sync_entry = owner_mcp / 'xvfb-owner-sync-entered.json'
        await wait_until(lambda: marker.exists() and sync_entry.exists(), 3, 'fault injection markers')
        report['fault_marker'] = json.loads(marker.read_text())
        report['owner_sync_entry'] = json.loads(sync_entry.read_text())
        report['cancel_invoked_ns'] = time.monotonic_ns()
        cancel_response = metadata(await asyncio.wait_for(old_server.call_tool(
            'interface_guarded_cancel', {'call_id':old_call_id}), timeout=4))
        report['cancel_returned_ns'] = time.monotonic_ns()
        report['cancel_response'] = cancel_response
        report['cancel_elapsed_ms'] = (report['cancel_returned_ns']-report['cancel_invoked_ns'])/1e6
        terminal = await call_until_terminal(old_server, old_call_id, 6)
        report['old_terminal'] = terminal
        report['old_effect_rows_at_cancel'] = journal(old_journal)
        report['old_task_done_at_cancel'] = (HERE/'old-journal.done.json').exists()
        report['independent_keymap_at_cancel'] = keymap(':188')
        horizon_ns = report['fault_marker']['flushed_ns'] + conditions['late_request_horizon_ms']*1_000_000
        delay_s = max(0, (horizon_ns-time.monotonic_ns())/1e9)
        report['late_horizon_wait_started_ns'] = time.monotonic_ns()
        await asyncio.sleep(delay_s)
        report['late_horizon_reached_ns'] = time.monotonic_ns()
        report['old_effect_rows_at_horizon'] = journal(old_journal)
        report['old_task_done_at_horizon'] = (HERE/'old-journal.done.json').exists()
        report['independent_keymap_at_horizon'] = keymap(':188')
        report['old_late_horizon_read_started_ns'] = time.monotonic_ns()
        report['old_late_horizon_read_completed_ns'] = time.monotonic_ns()
        old_close = metadata(await asyncio.wait_for(old_server.call_tool('interface_close', {}), timeout=8))
        report['old_close'] = old_close
        old_server = None
        report['old_process_cleanup'] = terminate_owned(old_terminal, old_pidfd, old_log)
        old_terminal = old_pidfd = old_log = None
        await asyncio.sleep(.25)
        report['old_xterm_absent_before_new_generation'] = old_terminal is None

        fresh_base = td / 'fresh-xterm'
        fresh_journal = HERE / 'fresh-journal.jsonl'
        fresh_terminal, fresh_log, fresh_env, fresh_command = launch_xterm(
            bundle, conditions['fresh_target_title'], fresh_journal, auth, fresh_base)
        fresh_pidfd = os.pidfd_open(fresh_terminal.pid)
        fresh_window = await find_window(observer, conditions['fresh_target_title'], fresh_terminal)
        fresh_geo = fresh_window.get_geometry()
        report['fresh_app'] = {'pid':fresh_terminal.pid, 'command':fresh_command,
            'window_id':fresh_window.id, 'geometry':[fresh_geo.x,fresh_geo.y,fresh_geo.width,fresh_geo.height],
            'wm_class':fresh_window.get_wm_class(), 'journal':str(fresh_journal)}
        fresh_window.set_input_focus(X.RevertToParent, X.CurrentTime)
        observer.screen().root.warp_pointer(fresh_geo.x+18, fresh_geo.y+14)
        observer.sync()
        await asyncio.sleep(1)
        fresh_server = create_server({'terminal':fresh_window.id}, td/'fresh-owner',
            session_mode='guarded-x11', display_name=':188', guarded_process_identity=True,
            guarded_query_worker=True, guarded_window_lifecycle=True, guarded_owned_process=True)
        fresh_minted, _ = await public_setup(observer, fresh_window, fresh_server, report, 'fresh')
        old_binding = report['old_observation']['binding']
        fresh_binding = report['fresh_observation']['binding']
        report['generation_comparison'] = {
            'process_generation_distinct':old_binding.get('process_generation') != fresh_binding.get('process_generation'),
            'window_generation_distinct':old_binding.get('window_generation') != fresh_binding.get('window_generation'),
            'surface_distinct':old_binding.get('surface') != fresh_binding.get('surface'),
            'old':old_binding, 'fresh':fresh_binding,
        }
        report['fresh_input_started_ns'] = time.monotonic_ns()
        fresh_input = metadata(await fresh_server.call_tool('interface_guarded_input', {
            'alias':'prompt','offset':fresh_minted['offset'],'interaction':'keyboard',
            'observe_after':False,'wait_for_result_ms':10000,
            'tail':[{'op':'text','text':'record '+conditions['fresh_task_argument']},
                    {'op':'key_chord','keys':['Return']}]}))
        report['fresh_input_response'] = fresh_input
        report['fresh_input_returned_ns'] = time.monotonic_ns()
        await wait_until(lambda: (HERE/'fresh-journal.done.json').exists(), 3, 'fresh saved effect')
        await asyncio.sleep(.25)
        report['fresh_effect_rows_at_horizon'] = journal(fresh_journal)
        report['fresh_done_receipt'] = json.loads((HERE/'fresh-journal.done.json').read_text())
        report['fresh_oracle_read_ns'] = time.monotonic_ns()
        report['fresh_close'] = metadata(await asyncio.wait_for(fresh_server.call_tool('interface_close', {}), timeout=8))
        fresh_server = None
        report['fresh_process_cleanup'] = terminate_owned(fresh_terminal, fresh_pidfd, fresh_log)
        fresh_terminal = fresh_pidfd = fresh_log = None
        report['status'] = 'OBSERVED_XTERM_CANCEL_AND_NEW_GENERATION_PENDING_AUDIT'
    except BaseException as error:
        report.update(status='FAIL', error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    finally:
        if old_server is not None:
            try:
                report['old_final_close'] = metadata(await asyncio.wait_for(old_server.call_tool('interface_close', {}), timeout=8))
            except BaseException as error: cleanup.append('old close: '+repr(error))
        if fresh_server is not None:
            try:
                report['fresh_final_close'] = metadata(await asyncio.wait_for(fresh_server.call_tool('interface_close', {}), timeout=8))
            except BaseException as error: cleanup.append('fresh close: '+repr(error))
        for name, process, pidfd, log in (
                ('old',old_terminal,old_pidfd,old_log), ('fresh',fresh_terminal,fresh_pidfd,fresh_log)):
            if process is not None:
                report['process_cleanup'][name] = terminate_owned(process,pidfd,log)
        if observer is not None:
            try: observer.close()
            except BaseException as error: cleanup.append('observer close: '+repr(error))
        if xvfb_fd is not None:
            try:
                signal.pidfd_send_signal(xvfb_fd, signal.SIGCONT)
                signal.pidfd_send_signal(xvfb_fd, signal.SIGTERM)
                report['xvfb_exit_code'] = xvfb.wait(timeout=5)
            except BaseException as error:
                cleanup.append('Xvfb close: '+repr(error))
                try:
                    signal.pidfd_send_signal(xvfb_fd, signal.SIGKILL)
                    report['xvfb_kill_exit_code'] = xvfb.wait(timeout=5)
                except BaseException as second: cleanup.append('Xvfb kill: '+repr(second))
            os.close(xvfb_fd)
            xvfb_log.close()
        elif xvfb is not None:
            xvfb.terminate()
            report['xvfb_exit_code'] = xvfb.wait(timeout=5)
        if 'auth_dir' in locals():
            shutil.rmtree(auth_dir, ignore_errors=True)
        if 'previous_display_environment' in report:
            if previous_display is None:
                os.environ.pop('DISPLAY',None)
            else:
                os.environ['DISPLAY'] = previous_display
            if previous_xauthority is not None:
                os.environ['XAUTHORITY'] = previous_xauthority
            else:
                os.environ.pop('XAUTHORITY',None)
        if xvfb_log is not None and not xvfb_log.closed:
            xvfb_log.close()
        try:
            report['native_postrun'] = verify_native_binaries()
        except BaseException as error:
            cleanup.append('native post-run verification: '+repr(error))
        report['cleanup_errors'] = cleanup
        report['ended_ns'] = time.monotonic_ns()
        save('result.json', report)
    return report


def main():
    os.environ['AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S'] = '0'
    os.environ['AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS'] = '1'
    verify_frozen_sources()
    verify_native_binaries()
    conditions = json.loads((HERE / 'conditions.json').read_text())
    with (HERE / 'attempt-started.json').open('x') as marker:
        marker.write(json.dumps({'run_id':conditions['run_id'],'started_ns':time.monotonic_ns()})+'\n')
    try:
        report = asyncio.run(run_trial())
    except BaseException as error:
        report = {'status':'FAIL_LAUNCH','error':repr(error),'traceback':traceback.format_exc()}
        save('launcher-result.json', report)
    print(json.dumps({'status':report.get('status'),'cancel_elapsed_ms':report.get('cancel_elapsed_ms'),
        'old_rows':len(report.get('old_effect_rows_at_horizon') or []),
        'fresh_rows':len(report.get('fresh_effect_rows_at_horizon') or []),
        'error':report.get('error')}))
    return 0 if report.get('status') == 'OBSERVED_XTERM_CANCEL_AND_NEW_GENERATION_PENDING_AUDIT' else 1


if __name__ == '__main__':
    raise SystemExit(main())
