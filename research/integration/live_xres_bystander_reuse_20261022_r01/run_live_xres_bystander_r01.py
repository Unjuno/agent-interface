"""One-shot live XRes bystander-reuse discriminator on an isolated Xvfb."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from Xlib import X, XK, display
from Xlib.ext import xtest

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw' / 'r01'
DISPLAY_NAME = os.environ.get('DISPLAY', ':177')


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(path)


def key_down(connection, keycode):
    keymap = connection.query_keymap()
    return bool(keymap[keycode // 8] & (1 << (keycode % 8)))


def owner_mode(ready_path, close_path):
    connection = display.Display(DISPLAY_NAME)
    keycode = connection.keysym_to_keycode(XK.string_to_keysym('a'))
    base = int(connection.display.info.resource_id_base)
    pid = os.getpid()
    xtest.fake_input(connection, X.KeyPress, detail=keycode)
    connection.sync()
    write_json(ready_path, {'pid': pid, 'resource_base': base,
                            'keycode': keycode, 'press_synced': True})
    deadline = time.monotonic() + 8
    while not Path(close_path).exists() and time.monotonic() < deadline:
        time.sleep(0.005)
    connection.close()
    return 0 if Path(close_path).exists() else 21


def supervisor_mode(ready_path, request_path, result_path):
    pid = os.getpid()
    write_json(ready_path, {'pid': pid, 'ready': True})
    deadline = time.monotonic() + 8
    while not Path(request_path).exists() and time.monotonic() < deadline:
        time.sleep(0.005)
    if not Path(request_path).exists():
        write_json(result_path, {'status': 'unknown', 'reason': 'request_timeout'})
        return 22
    from runtime.guarded_x11_v1.cancel_supervisor import x11_cancel_worker
    request = json.loads(Path(request_path).read_text(encoding='utf-8'))
    request['supervisor_pid'] = pid
    write_json(result_path, x11_cancel_worker(request))
    return 0


def run_once():
    RAW.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    owner_ready = RAW / 'owner-ready.json'
    owner_close = RAW / 'owner-close'
    supervisor_ready = RAW / 'supervisor-ready.json'
    request_path = RAW / 'cleanup-request.json'
    result_path = RAW / 'cleanup-result.json'
    observer = display.Display(DISPLAY_NAME)
    owner = supervisor = bystander = None
    row = {'schema': 'agent-interface/live-xres-bystander-r01-v1',
           'disposition': 'HOLD', 'operation_id': 'bystander-' + token,
           'display': DISPLAY_NAME}
    try:
        supervisor = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), '--supervisor',
             str(supervisor_ready), str(request_path), str(result_path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 5
        while not supervisor_ready.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        if not supervisor_ready.exists():
            row.update(disposition='HOLD', reason='supervisor_not_ready')
            return row

        owner = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), '--owner',
             str(owner_ready), str(owner_close)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 5
        while not owner_ready.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        if not owner_ready.exists():
            row.update(reason='owner_not_ready')
            return row
        owner_receipt = json.loads(owner_ready.read_text(encoding='utf-8'))
        keycode = owner_receipt['keycode']
        row.update(owner=owner_receipt,
                   key_down_before_retirement=key_down(observer, keycode),
                   supervisor= json.loads(supervisor_ready.read_text(encoding='utf-8')))
        owner_close.write_text('retire\n', encoding='utf-8')
        owner_exit = owner.wait(timeout=5)
        row['owner_exitcode'] = owner_exit
        if owner_exit != 0:
            row['reason'] = 'owner_exit_unconfirmed'
            return row

        bystander = display.Display(DISPLAY_NAME)
        bystander_base = int(bystander.display.info.resource_id_base)
        bystander_pid = os.getpid()
        row['bystander'] = {'pid': bystander_pid,
                            'resource_base': bystander_base}
        row['resource_base_reused'] = (
            bystander_base == owner_receipt['resource_base'])
        row['key_down_before_cleanup'] = key_down(observer, keycode)
        if not row['resource_base_reused']:
            row['reason'] = 'owner_resource_base_not_reused_first_connection'
            return row
        if not row['key_down_before_cleanup']:
            row['reason'] = 'held_key_not_observable_after_owner_retirement'
            return row

        request = {
            'operation_id': row['operation_id'],
            'session_id': 'live-xres-bystander-' + token,
            'deadline_monotonic_ns': time.monotonic_ns() + 5_000_000_000,
            'owner_process_retired': True,
            'owner_process_exitcode': owner_exit,
            'x_resource_base': owner_receipt['resource_base'],
            'owner_pid': owner_receipt['pid'],
            'supervisor_pid': int(row['supervisor']['pid']),
            'binding_revision': 1,
            'owner_generation': {
                'session_id': 'live-xres-bystander-' + token,
                'child_pid': owner_receipt['pid'],
                'x_resource_base': owner_receipt['resource_base'],
                'binding_revision': 1},
            'keys': {'a': keycode}, 'buttons': [],
            'display_name': DISPLAY_NAME}
        write_json(request_path, request)
        deadline = time.monotonic() + 6
        while not result_path.exists() and time.monotonic() < deadline:
            if supervisor.poll() is not None:
                break
            time.sleep(0.005)
        if not result_path.exists():
            row['reason'] = 'supervisor_result_unavailable'
            return row
        result = json.loads(result_path.read_text(encoding='utf-8'))
        row['cleanup_result'] = result
        row['supervisor_exitcode'] = supervisor.wait(timeout=3)
        row['key_down_after_cleanup'] = key_down(observer, keycode)
        refused = (result.get('status') == 'unknown'
                   and result.get('reason') == 'stale_owner_identity'
                   and result.get('owner_client_disconnect', {}).get('reason')
                       == 'resource_base_reused_by_unrelated_client'
                   and result.get('owner_release_attempt', {}).get('status')
                       == 'not_attempted')
        preserved = row['key_down_after_cleanup'] is row['key_down_before_cleanup'] is True
        if refused and preserved:
            row.update(disposition='PASS_XRES_BYSTANDER_REFUSAL_SCOPED',
                       reason=None)
        else:
            row.update(disposition='FAIL_OR_HOLD',
                       reason='refusal_or_independent_key_state_mismatch')
        return row
    finally:
        if owner is not None and owner.poll() is None:
            owner_close.write_text('retire\n', encoding='utf-8')
            try:
                owner.wait(timeout=1)
            except subprocess.TimeoutExpired:
                owner.terminate()
                owner.wait(timeout=1)
        if bystander is not None:
            try:
                if 'keycode' in locals() and key_down(observer, keycode):
                    xtest.fake_input(bystander, X.KeyRelease, detail=keycode)
                    bystander.sync()
                if 'keycode' in locals():
                    row['key_down_after_harness_cleanup'] = key_down(observer, keycode)
            finally:
                bystander.close()
        if supervisor is not None and supervisor.poll() is None:
            try:
                supervisor.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                supervisor.terminate()
                supervisor.wait(timeout=1)
        observer.close()
        write_json(RAW / 'result.json', row)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--owner':
        raise SystemExit(owner_mode(sys.argv[2], sys.argv[3]))
    if len(sys.argv) > 1 and sys.argv[1] == '--supervisor':
        raise SystemExit(supervisor_mode(sys.argv[2], sys.argv[3], sys.argv[4]))
    try:
        final = run_once()
    except BaseException as error:
        final = {'schema': 'agent-interface/live-xres-bystander-r01-v1',
                 'disposition': 'HOLD', 'reason': 'runner_exception',
                 'error_type': type(error).__name__, 'error': str(error)[:500]}
        RAW.mkdir(parents=True, exist_ok=True)
        write_json(RAW / 'result.json', final)
    print(json.dumps(final, sort_keys=True))
