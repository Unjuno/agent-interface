import asyncio
import ctypes
import hashlib
import json
import os
import re
import sys
import time
from ctypes import wintypes
from pathlib import Path

from runtime.backends.win32_v1.backend import Win32Backend
from runtime.cli_v1.mcp_server import create_server

ROOT = Path(__file__).resolve().parent
TARGET = 'notepad'
HWND = 24840738
MARKER = 'AI-CTRL-20261024-R04'
EXPECTATIONS = {}
ORACLE_TIMES = {}


def child_edit_text(hwnd):
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found = []
    def visit(child, _):
        name = ctypes.create_unicode_buffer(128)
        user32.GetClassNameW(child, name, len(name))
        if name.value == 'RichEditD2DPT':
            found.append(int(child))
        return True
    if not user32.EnumChildWindows(hwnd, EnumProc(visit), 0):
        raise OSError('EnumChildWindows failed')
    if len(found) != 1:
        raise RuntimeError(f'expected exactly one RichEditD2DPT child, found {len(found)}')
    child = found[0]
    send = user32.SendMessageTimeoutW
    send.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                     wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                     ctypes.POINTER(ctypes.c_size_t)]
    send.restype = wintypes.LPARAM
    out = ctypes.c_size_t()
    ok = send(child, 0x000E, 0, 0, 0x0002, 750, ctypes.byref(out))
    if not ok:
        raise TimeoutError('WM_GETTEXTLENGTH timed out')
    n = int(out.value)
    if n > 4096:
        raise RuntimeError('oracle text exceeds bounded read length')
    buf = ctypes.create_unicode_buffer(n + 1)
    got = ctypes.c_size_t()
    ok = send(child, 0x000D, len(buf), ctypes.addressof(buf),
              0x0002, 750, ctypes.byref(got))
    if not ok:
        raise TimeoutError('WM_GETTEXT timed out')
    return {'hwnd': child, 'text': buf.value, 'characters': int(got.value)}


def generation_now():
    backend = Win32Backend({TARGET: HWND})
    try:
        return backend.target_generation(TARGET)
    finally:
        backend.close()


def oracle(action):
    call_id = action['call_id']
    expected = EXPECTATIONS.get(call_id)
    begin_ns = time.monotonic_ns()
    try:
        current = generation_now()
        readback = child_edit_text(HWND)
        end_ns = time.monotonic_ns()
        ORACLE_TIMES[call_id] = {'started_ns': begin_ns, 'finished_ns': end_ns,
            'observed_ns': end_ns, 'characters': readback['characters'],
            'child_hwnd': readback['hwnd'], 'observed_text_sha256': hashlib.sha256(
                readback['text'].encode('utf-8')).hexdigest()}
        if current != action['target_generation'] or expected is None:
            outcome = 'unknown'
        else:
            outcome = 'success' if readback['text'] == expected else 'failure'
    except Exception as exc:
        end_ns = time.monotonic_ns()
        ORACLE_TIMES[call_id] = {'started_ns': begin_ns, 'finished_ns': end_ns,
            'error_type': type(exc).__name__, 'error': str(exc)[:256]}
        outcome = 'unknown'
        end_ns = max(time.monotonic_ns(), begin_ns + 1)
    return {'call_id': call_id, 'operation_id': action['operation_id'],
        'target_generation': action['target_generation'], 'oracle_id': '04040404040404040404040404040404',
        'outcome': outcome, 'observed_monotonic_ns': end_ns,
        'evidence_ref': 'oracle-log.json#' + call_id}


def save_reply(name, reply):
    row = {'isError': bool(getattr(reply, 'isError', False)), 'content': []}
    for item in reply.content:
        if item.type == 'text':
            row['content'].append({'type': 'text', 'text': item.text})
        elif item.type == 'image':
            filename = name + '-image-' + str(len(row['content'])) + '.png'
            (ROOT / filename).write_bytes(__import__('base64').b64decode(item.data))
            row['content'].append({'type': 'image', 'file': filename,
                                  'mimeType': item.mimeType,
                                  'sha256': hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()})
        else:
            row['content'].append({'type': item.type, 'repr': repr(item)[:1000]})
    (ROOT / (name + '.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return row


def parse_text(row):
    for item in row['content']:
        if item.get('type') == 'text':
            try:
                return json.loads(item['text'])
            except Exception:
                pass
    return {}


def raw_report(obj):
    if type(obj) is dict:
        if type(obj.get('receipt')) is dict:
            source = obj['receipt'].get('source')
            if type(source) is dict and type(source.get('raw_report')) is dict:
                return source['raw_report']
        if type(obj.get('raw_report')) is dict:
            return obj['raw_report']
    return obj


def required_generation(obj):
    candidates = [obj, raw_report(obj)]
    for candidate in candidates:
        if type(candidate) is dict:
            gen = candidate.get('target_generation')
            if type(gen) is str and re.fullmatch(r'[0-9a-f]{64}', gen):
                return gen
            source = candidate.get('source')
            if type(source) is dict:
                raw = source.get('raw_report')
                if type(raw) is dict and type(raw.get('target_generation')) is str:
                    return raw['target_generation']
    raise RuntimeError('public observation did not return a target generation')


def effect_fields(dispatch_obj):
    raw = raw_report(dispatch_obj)
    supervision = raw.get('supervision') or {} if type(raw) is dict else {}
    action = supervision.get('action') or {}
    result = raw.get('result') or {} if type(raw) is dict else {}
    return {'call_id': dispatch_obj.get('call_id') or raw.get('call_id'),
            'status': result.get('status'), 'release_confirmed': action.get('release_confirmed'),
            'task_success': action.get('task_success'), 'input_dispatched': raw.get('input_dispatched'),
            'replay_allowed': action.get('replay_allowed'),
            'target_generation': action.get('target_generation'),
            'backend_emissions': result.get('backend_emissions'), 'detail': result.get('detail')}


async def run():
    # Preflight is read-only and binds this exact fresh window to one observed native generation.
    before = child_edit_text(HWND)
    generation = generation_now()
    (ROOT / 'preflight.json').write_text(json.dumps({
        'hwnd': HWND, 'expected_title': 'タイトルなし - メモ帳',
        'control_class': 'RichEditD2DPT', 'initial_characters': before['characters'],
        'initial_text_sha256': hashlib.sha256(before['text'].encode('utf-8')).hexdigest(),
        'initial_generation': generation, 'python': sys.version,
        'branch_head': '16dfc8843564d3768a767aaa85b165fd3c8c0cd3',
        'origin_main': '736f4c51243d984c5ddf2724220e1e5bf4bc36ac',
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if before['text'] != '':
        raise RuntimeError('isolated Notepad precondition was not empty; no input sent')

    server = create_server({TARGET: HWND}, ROOT / 'mcp-calls',
        session_mode='supervised-win32', supervised_win32_task_oracle=oracle)
    report = {'scope': 'single native Notepad task via public supervised-win32 MCP route',
        'target': 'one freshly opened blank Notepad window', 'initial_generation': generation,
        'tasks': [], 'limitations': ['No blocked-platform-I/O recovery trial in this run.',
            'No WSLc allocation used.', 'Single-task result is not a reliability estimate.']}
    try:
        observe = save_reply('observe-1', await server.call_tool('interface_observe', {
            'target': TARGET, 'frame': 'window_client', 'region': [0, 0, 640, 240]}))
        observe_obj = parse_text(observe)
        if raw_report(observe_obj).get('status') != 'returned':
            raise RuntimeError('public observation failed: ' + json.dumps(observe_obj)[:500])
        observed_generation = required_generation(observe_obj)
        if observed_generation != generation:
            raise RuntimeError('generation mismatch between independent preflight and public observation')

        async def dispatch_and_verify(label, operations, expected):
            EXPECTATIONS.clear()
            started_ns = time.monotonic_ns()
            program = {'schema': 'agent-interface/program-v1', 'program_id': 'notepad-r04-' + label,
                'source': {'observation_seq': 1, 'binding_revision': 1,
                           'target_generations': {TARGET: observed_generation}},
                'authority': {'lease_id': 'notepad-r04-' + label,
                              'expires_at_ns': time.monotonic_ns() + 15_000_000_000},
                'terminal': {'release_all_required': True}, 'ops': operations}
            dispatched_raw = save_reply(label + '-dispatch', await server.call_tool('interface_dispatch', {
                'program': program, 'current_observation_seq': 1,
                'current_binding_revision': 1, 'wait_for_result_ms': 10000}))
            dispatched = parse_text(dispatched_raw)
            call_id = dispatched.get('call_id')
            if type(call_id) is not str or not re.fullmatch(r'[0-9a-f]{32}', call_id):
                return {'dispatch': effect_fields(dispatched), 'verification': None,
                        'error': 'no standard action call ID; no replay attempted'}
            EXPECTATIONS[call_id] = expected
            verified_raw = save_reply(label + '-task-verification', await server.call_tool(
                'interface_verify_task', {'call_id': call_id, 'wait_for_result_ms': 5000}))
            verified = parse_text(verified_raw)
            raw = raw_report(dispatched)
            task = {'call_id': call_id, 'program_id': program['program_id'],
                'dispatch_started_ns': started_ns, 'dispatch_received_ns': time.monotonic_ns(),
                'dispatch_summary': effect_fields(dispatched),
                'verification': {'status': verified.get('status'),
                    'task_success': verified.get('task_success'),
                    'outcome': ((verified.get('task_effect') or {}).get('receipt') or {}).get('outcome'),
                    'oracle': ORACLE_TIMES.get(call_id)},
                'raw_execution_status': ((raw.get('result') or {}).get('status')
                    if type(raw) is dict else None)}
            report['tasks'].append(task)
            return task

        typed = await dispatch_and_verify('type-marker', [
            {'op': 'focus', 'target': TARGET}, {'op': 'text', 'text': MARKER},
            {'op': 'release_all'}], MARKER)

        # Only erase the marker if the first independently checked task and action release both passed.
        if (typed.get('verification', {}).get('status') == 'verified'
                and typed.get('verification', {}).get('task_success') is True
                and typed.get('dispatch_summary', {}).get('release_confirmed') is True):
            # A fresh public observation is used for the cleanup dispatch as well.
            observe2 = save_reply('observe-2', await server.call_tool('interface_observe', {
                'target': TARGET, 'frame': 'window_client', 'region': [0, 0, 640, 240]}))
            observe2_obj = parse_text(observe2)
            generation2 = required_generation(observe2_obj)
            if generation2 != generation:
                report['cleanup_skipped'] = 'target generation changed after verified first task'
            else:
                observed_generation = generation2
                cleanup = await dispatch_and_verify('clear-marker', [
                    {'op': 'focus', 'target': TARGET},
                    {'op': 'key_chord', 'keys': ['CTRL', 'A']},
                    {'op': 'key_chord', 'keys': ['BACKSPACE']}, {'op': 'release_all'}], '')
                report['cleanup'] = cleanup
        else:
            report['cleanup_skipped'] = 'first action or independent task check did not fully pass'
        report['overall'] = ('PASS' if typed.get('verification', {}).get('status') == 'verified'
            and typed.get('verification', {}).get('task_success') is True
            and typed.get('dispatch_summary', {}).get('release_confirmed') is True
            else 'FAIL_OR_UNKNOWN')
    finally:
        try:
            report['close'] = parse_text(save_reply('close', await server.call_tool('interface_close', {})))
        except Exception as exc:
            report['close_error'] = repr(exc)
    (ROOT / 'oracle-log.json').write_text(json.dumps(ORACLE_TIMES, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'RESULT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    result = asyncio.run(run())
    print(json.dumps(result, ensure_ascii=False, indent=2))



