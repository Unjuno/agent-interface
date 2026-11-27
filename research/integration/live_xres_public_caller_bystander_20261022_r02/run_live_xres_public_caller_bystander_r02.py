"""One-shot live XRes bystander refusal through the standard public MCP caller."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from pathlib import Path

os.environ['AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR'] = '1'
os.environ['AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S'] = '0'
os.environ['AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS'] = '1'

from Xlib import X, Xatom, XK, display
from Xlib.ext import xtest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import metadata
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import (
    _xvfb_blocking_owner_factory,
)
from runtime.guarded_x11_v1.cancel_supervisor import x11_cancel_worker

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw' / 'r02'
DISPLAY_NAME = os.environ.get('DISPLAY', ':179')
_BYSTANDER_READY = 'live-bystander-ready.json'
_BYSTANDER_STOP = 'live-bystander-stop'
_BYSTANDER_CLOSED = 'live-bystander-closed.json'


def write_json(path, row):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(row, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(path)


def key_down(connection, keycode):
    keymap = connection.query_keymap()
    return bool(keymap[keycode // 8] & (1 << (keycode % 8)))


def bystander_process(directory):
    root = Path(directory)
    connection = display.Display(DISPLAY_NAME)
    row = {'pid': os.getpid(),
           'resource_base': int(connection.display.info.resource_id_base),
           'connected_ns': time.monotonic_ns()}
    write_json(root / _BYSTANDER_READY, row)
    deadline = time.monotonic() + 20
    while not (root / _BYSTANDER_STOP).exists() and time.monotonic() < deadline:
        time.sleep(0.005)
    connection.close()
    write_json(root / _BYSTANDER_CLOSED, {
        'pid': os.getpid(), 'closed_ns': time.monotonic_ns(),
        'stop_seen': (root / _BYSTANDER_STOP).exists()})
    return 0


def live_bystander_then_worker(request):
    """Test-only wrapper: make a real distinct X client the first bystander."""
    root = Path(request['owner_data_directory'])
    ready = root / _BYSTANDER_READY
    stop = root / _BYSTANDER_STOP
    closed = root / _BYSTANDER_CLOSED
    child = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), '--bystander', str(root)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True, env=os.environ.copy())
    try:
        deadline = time.monotonic() + 4
        while not ready.exists() and time.monotonic() < deadline:
            if child.poll() is not None:
                raise RuntimeError('bystander child exited before connecting')
            time.sleep(0.005)
        if not ready.exists():
            raise RuntimeError('bystander did not connect before timeout')
        row = json.loads(ready.read_text(encoding='utf-8'))
        write_json(root / 'live-bystander-comparison.json', {
            'owner_pid': request['owner_pid'],
            'owner_resource_base': request['x_resource_base'],
            'bystander_pid': row['pid'],
            'bystander_resource_base': row['resource_base'],
            'same_resource_base': row['resource_base'] == request['x_resource_base'],
        })
        if row['resource_base'] != request['x_resource_base']:
            result = {
                'status': 'unknown', 'reason': 'natural_resource_base_not_reused',
                'owner_client_disconnect': {
                    'status': 'unknown', 'reason': 'natural_resource_base_not_reused',
                    'observed_pid': row['pid']},
                'owner_release_attempt': {
                    'status': 'not_attempted',
                    'reason': 'bystander_base_not_equal_to_retired_owner'},
                'release_confirmed': False, 'cleanup_status': 'UNKNOWN',
                'task_success': None, 'replay_allowed': False,
            }
            write_json(root / 'live-worker-result.json', result)
            return result
        result = x11_cancel_worker(request)
        write_json(root / 'live-worker-result.json', result)
        return result
    finally:
        stop.write_text('stop\n', encoding='utf-8')
        try:
            child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=2)
        if child.returncode not in (0, None):
            stderr = child.stderr.read() if child.stderr else ''
            write_json(root / 'live-bystander-child-error.json', {
                'returncode': child.returncode, 'stderr': stderr[-1000:]})


async def wait_for_file(path, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        await asyncio.sleep(0.005)
    raise TimeoutError(f'file not observed: {path.name}')


async def wait_for_terminal(server, call_id, timeout=8):
    deadline = time.monotonic() + timeout
    latest = None
    while time.monotonic() < deadline:
        latest = metadata(await server.call_tool('interface_results', {
            'call_id': call_id, 'include_image': False}))
        cancellation = latest.get('cancellation')
        if isinstance(cancellation, dict) and cancellation.get('status') in (
                'completed', 'unknown'):
            return latest
        await asyncio.sleep(0.025)
    return latest


async def run_once():
    RAW.mkdir(parents=True, exist_ok=True)
    if (RAW / 'result.json').exists():
        raise RuntimeError('one-shot result already exists; refusing rerun')
    observer = display.Display(DISPLAY_NAME)
    server = None
    owner_root = RAW / 'mcp-owner'
    owner_root.mkdir(parents=True, exist_ok=True)
    window = None
    keycodes = {}
    report = {
        'schema': 'agent-interface/live-xres-public-caller-bystander-r02-v1',
        'status': 'HOLD', 'scope': 'standard public MCP cancel; private live Xvfb',
        'source_revision': os.environ.get('GITHUB_SHA') or source_revision(),
        'display': DISPLAY_NAME,
        'started_ns': time.monotonic_ns(),
        'owner_factory': 'existing _xvfb_blocking_owner_factory with real delayed XTEST and Display.sync',
        'supervisor_target': 'test wrapper starts one distinct real X client then calls unchanged x11_cancel_worker',
        'trial_count': 1,
    }
    try:
        screen = observer.screen()
        x, y, width, height = 40, 40, 240, 180
        window = screen.root.create_window(
            x, y, width, height, 0, X.CopyFromParent, X.InputOutput,
            X.CopyFromParent, background_pixel=0,
            event_mask=X.StructureNotifyMask)
        effect_atom = observer.intern_atom('AI_XRES_BYSTANDER_UNUSED')
        window.change_property(effect_atom, Xatom.CARDINAL, 32, [0])
        window.map()
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        screen.root.warp_pointer(x + 48, y + 48)
        gc = window.create_gc(foreground=0xFFFFFF)
        for row in range((height + 15) // 16):
            for column in range((width + 15) // 16):
                if (row + column) % 2 == 0:
                    window.fill_rectangle(gc, column * 16, row * 16,
                        min(16, width - column * 16),
                        min(16, height - row * 16))
        observer.sync()

        server = create_server(
            {'app': window.id}, owner_root, display_name=DISPLAY_NAME,
            session_mode='guarded-x11', guarded_process_identity=True,
            guarded_query_worker=True, guarded_window_lifecycle=True,
            guarded_owned_process=True, guarded_prestarted_cancel_supervisor=True,
            _guarded_cancel_supervisor_target=live_bystander_then_worker,
            _guarded_owner_factory=_xvfb_blocking_owner_factory)
        observed = metadata(await server.call_tool('interface_guarded_observe', {}))
        if observed.get('status') != 'observed':
            raise RuntimeError(f'observe failed: {observed}')
        minted = metadata(await server.call_tool('interface_guarded_mint', {
            'alias': 'field', 'source_sequence': observed['source']['sequence'],
            'point': [x + 48, y + 48], 'region_size': [24, 24]}))
        if minted.get('status') != 'minted':
            raise RuntimeError(f'mint failed: {minted}')
        keycodes = {name: observer.keysym_to_keycode(XK.string_to_keysym(name))
                    for name in ('a', 'b')}
        report['observation'] = {
            'status': observed['status'], 'sequence': observed['source']['sequence'],
            'window_id': window.id, 'window_pixel_patch': [x + 36, y + 36, x + 60, y + 60]}
        report['mint'] = {'status': minted['status'], 'offset': minted['offset']}
        action = metadata(await server.call_tool('interface_guarded_input', {
            'alias': 'field', 'offset': minted['offset'], 'interaction': 'keyboard',
            'observe_after': False, 'wait_for_result_ms': 0,
            'tail': [{'op': 'key_chord', 'keys': ['a']}]}))
        report['input_admission'] = action
        if action.get('status') != 'pending':
            raise RuntimeError(f'guarded input did not enter pending state: {action}')
        call_id = action['call_id']
        report['owner_sync_marker'] = await wait_for_file(
            owner_root / 'xvfb-owner-sync-entered.json')
        report['delayed_request_marker'] = await wait_for_file(
            owner_root / 'xvfb-delayed-request-queued.json')
        report['keycodes'] = keycodes
        report['key_down_before_cancel'] = {
            name: key_down(observer, code) for name, code in keycodes.items()}
        report['cancel_invoked_ns'] = time.monotonic_ns()
        cancel = metadata(await server.call_tool('interface_guarded_cancel', {
            'call_id': call_id}))
        report['cancel_response_ns'] = time.monotonic_ns()
        report['cancel_response'] = cancel
        terminal = await wait_for_terminal(server, call_id)
        report['terminal_result'] = terminal
        report['bystander'] = json.loads(
            (owner_root / 'live-bystander-comparison.json').read_text(encoding='utf-8'))
        report['worker_result'] = json.loads(
            (owner_root / 'live-worker-result.json').read_text(encoding='utf-8'))
        report['bystander_closed'] = json.loads(
            (owner_root / _BYSTANDER_CLOSED).read_text(encoding='utf-8'))
        report['key_down_after_cleanup'] = {
            name: key_down(observer, code) for name, code in keycodes.items()}
        cancellation = terminal.get('cancellation', {}).get('result', {})
        report['pass_checks'] = {
            'natural_resource_base_reuse': report['bystander']['same_resource_base'],
            'different_client_pid': report['bystander']['owner_pid'] != report['bystander']['bystander_pid'],
            'worker_saw_bystander': report['worker_result'].get('owner_client_disconnect', {}).get('reason') == 'resource_base_reused_by_unrelated_client',
            'worker_refused_release': report['worker_result'].get('owner_release_attempt', {}).get('status') == 'not_attempted',
            'input_still_down_after_worker': report['key_down_after_cleanup'].get('a') is True,
            'public_result_unknown_no_replay': cancellation.get('cleanup_status') == 'UNKNOWN' and cancellation.get('release_confirmed') is False and cancellation.get('task_success') is None and cancellation.get('replay_allowed') is False,
        }
        report['key_neutralization_started_ns'] = time.monotonic_ns()
        for name, code in keycodes.items():
            xtest.fake_input(observer, X.KeyRelease, detail=code)
        observer.sync()
        await asyncio.sleep(8.5)
        report['key_down_after_late_horizon'] = {
            name: key_down(observer, code) for name, code in keycodes.items()}
        for name, code in keycodes.items():
            if report['key_down_after_late_horizon'][name]:
                xtest.fake_input(observer, X.KeyRelease, detail=code)
        observer.sync()
        await asyncio.sleep(0.05)
        report['key_down_after_harness_cleanup'] = {
            name: key_down(observer, code) for name, code in keycodes.items()}
        report['pass_checks']['harness_restored_neutral_key_state'] = not any(
            report['key_down_after_harness_cleanup'].values())
        report['status'] = (
            'PASS_PUBLIC_CALLER_XRES_BYSTANDER_REFUSAL_SCOPED'
            if all(report['pass_checks'].values()) else 'HOLD_OR_FAIL')
        if server is not None:
            report['close_result'] = metadata(await server.call_tool('interface_close', {}))
        report['finished_ns'] = time.monotonic_ns()
        write_json(RAW / 'result.json', report)
        return 0 if report['status'] == 'PASS_PUBLIC_CALLER_XRES_BYSTANDER_REFUSAL_SCOPED' else 1
    except BaseException as error:
        report.update(status='ERROR_HOLD', error_type=type(error).__name__, error=str(error))
        report['finished_ns'] = time.monotonic_ns()
        write_json(RAW / 'result.json', report)
        raise
    finally:
        if server is not None:
            try:
                await server.call_tool('interface_close', {})
            except BaseException:
                pass
        if window is not None:
            try:
                window.destroy()
                observer.sync()
            except BaseException:
                pass
        observer.close()


def source_revision():
    conditions = json.loads(
        (RAW / 'CONDITIONS.json').read_text(encoding='utf-8'))
    return conditions['source_revision']


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--bystander':
        raise SystemExit(bystander_process(sys.argv[2]))
    raise SystemExit(asyncio.run(run_once()))
