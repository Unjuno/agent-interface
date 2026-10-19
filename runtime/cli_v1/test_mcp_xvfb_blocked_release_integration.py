"""Standard guarded MCP cancellation with real Xvfb input and XRes cleanup.

The owner test factory injects one delayed XTEST request after the public
caller emits KeyPress(a). The first press reaches the private Xvfb and a
synthetic app before the owner blocks in the real Display.sync() response
wait. Cancellation then exercises the normal owned-process, XRes disconnect,
and fresh-client release path. No arbitrary developer DISPLAY is used.
"""

import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from time import monotonic_ns as _monotonic_ns
import unittest

from Xlib import X, Xatom, XK, display
from PIL import Image, ImageStat

from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1 import owned_guarded_session as owned_session_module
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


_DELAY_MS = 8000
_CANCEL_BOUND_MS = 3000
_CANCEL_ACK_WITHHOLD_S = float(os.environ.get(
    'AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S', '1.0'))
_TRACE_OWNER_PROCESS_METHODS = (
    os.environ.get('AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS', '1') == '1')
_TERMINAL_BOUND_MS = 5000

if not 0 <= _CANCEL_ACK_WITHHOLD_S <= 2:
    raise ValueError('cancel acknowledgement hold must be between 0 and 2 seconds')


def _metadata(response):
    return json.loads(response.content[0].text)


def _xvfb_provenance():
    pid_text = os.environ.get('AGENT_INTERFACE_XVFB_PID')
    if not pid_text or not pid_text.isdigit():
        return {'status':'unavailable', 'reason':'xvfb_pid_not_supplied'}
    executable = Path('/proc', pid_text, 'exe')
    try:
        resolved = Path(os.readlink(executable))
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except OSError as error:
        return {'status':'unavailable', 'reason':repr(error)}
    package = subprocess.run(
        ['dpkg-query', '-W', '-f=${binary:Package}=${Version}', 'xvfb'],
        capture_output=True, text=True, check=False)
    return {'status':'captured', 'pid':int(pid_text), 'path':str(resolved),
            'sha256':digest, 'package_returncode':package.returncode,
            'package_stdout':package.stdout.strip(),
            'package_stderr':package.stderr.strip()}


def _xvfb_blocking_owner_factory(targets, directory, display_name, options):
    """Inject blocked X I/O and optionally delay the child cancel acknowledgement."""
    from Xlib.ext import xtest

    owner = GuardedSessionOwner(targets, directory, display_name, **options)
    original_get = owner.get
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    marker = root/'xvfb-delayed-request-queued.json'
    sync_entered = root/'xvfb-owner-sync-entered.json'
    sync_returned = root/'xvfb-owner-sync-returned.json'
    cancel_ack_withheld = root/'xvfb-cancel-ack-withheld.json'

    original_cancel = owner.cancel_guarded

    def cancel_with_delayed_ack(token):
        result = original_cancel(token)
        row = {'owner_pid':os.getpid(), 'status':result.get('status'),
               'withheld_ack_s':_CANCEL_ACK_WITHHOLD_S,
               'entered_ns':time.monotonic_ns()}
        temporary = cancel_ack_withheld.with_suffix('.tmp')
        temporary.write_text(json.dumps(row, sort_keys=True), encoding='utf-8')
        temporary.replace(cancel_ack_withheld)
        if _CANCEL_ACK_WITHHOLD_S:
            time.sleep(_CANCEL_ACK_WITHHOLD_S)
        row['returned_ns'] = time.monotonic_ns()
        return result

    owner.cancel_guarded = cancel_with_delayed_ack

    def get_with_delayed_request():
        session = original_get()
        backend = session.backend
        original_fake_input = xtest.fake_input
        original_sync = backend.d.sync
        injected = {'value':False}
        sync_seen = {'value':False}

        def fake_input(display_connection, event_type, detail=0, time=0,
                       root=0, x=0, y=0):
            result = original_fake_input(
                display_connection, event_type, detail=detail, time=time,
                root=root, x=x, y=y)
            if event_type == X.KeyPress and not injected['value']:
                delayed_keycode = backend._keycode('b')
                original_fake_input(
                    display_connection, X.KeyPress, detail=delayed_keycode,
                    time=_DELAY_MS)
                display_connection.flush()
                row = {
                    'owner_pid':os.getpid(),
                    'resource_base':display_connection.display.info.resource_id_base,
                    'immediate_event':'KeyPress',
                    'immediate_keycode':detail,
                    'delayed_event':'KeyPress',
                    'delayed_keycode':delayed_keycode,
                    'delay_ms':_DELAY_MS,
                    'flushed_ns':_monotonic_ns(),
                    'blocked_boundary':'real python-xlib Display.sync response wait',
                }
                temporary = marker.with_suffix('.tmp')
                temporary.write_text(json.dumps(row, sort_keys=True),
                                      encoding='utf-8')
                temporary.replace(marker)
                injected['value'] = True
            return result

        def sync_with_boundary_receipt(*args, **kwargs):
            if injected['value'] and not sync_seen['value']:
                sync_seen['value'] = True
                row = {'owner_pid':os.getpid(),
                       'resource_base':backend.d.display.info.resource_id_base,
                       'entered_ns':time.monotonic_ns(),
                       'call':'python-xlib Display.sync'}
                temporary = sync_entered.with_suffix('.tmp')
                temporary.write_text(json.dumps(row, sort_keys=True), encoding='utf-8')
                temporary.replace(sync_entered)
                result = original_sync(*args, **kwargs)
                returned = dict(row, returned_ns=time.monotonic_ns())
                temporary = sync_returned.with_suffix('.tmp')
                temporary.write_text(json.dumps(returned, sort_keys=True),
                                     encoding='utf-8')
                temporary.replace(sync_returned)
                return result
            return original_sync(*args, **kwargs)

        # Backend.key_state calls sync immediately after sending the press.
        # The real XTEST delayed request makes that server reply wait pending.
        xtest.fake_input = fake_input
        backend.d.sync = sync_with_boundary_receipt
        return session

    owner.get = get_with_delayed_request
    return owner


def _key_down(observer, keycode):
    keymap = observer.query_keymap()
    return bool(keymap[keycode//8] & (1 << (keycode % 8)))


@unittest.skipUnless(
    sys.platform == 'linux' and os.environ.get('DISPLAY') == ':88'
    and os.environ.get('AGENT_INTERFACE_MCP_XVFB_TEST') == '1',
    'requires the explicitly enabled private Linux Xvfb integration job',
)
class StandardCallerBlockedReleaseXvfbTests(unittest.IsolatedAsyncioTestCase):
    async def _wait_for_file(self, path, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not path.exists():
            await asyncio.sleep(0.005)
        self.assertTrue(path.exists(), f'timed out waiting for {path.name}')
        return json.loads(path.read_text(encoding='utf-8'))

    async def _wait_for_event(self, event, timeout=2.0):
        completed = await asyncio.to_thread(event.wait, timeout)
        self.assertTrue(completed, f'timed out waiting for {event}')

    async def _wait_for_terminal(self, server, call_id, timeout=8.0):
        deadline = time.monotonic() + timeout
        while True:
            row = _metadata(await asyncio.wait_for(server.call_tool(
                'interface_results', {'call_id':call_id, 'include_image':False}),
                timeout=2.0))
            if row.get('status') != 'pending':
                return row
            if time.monotonic() >= deadline:
                return row
            await asyncio.sleep(0.05)

    async def _close_after_work(self, server, timeout=6.0):
        deadline = time.monotonic() + timeout
        while True:
            row = _metadata(await asyncio.wait_for(
                server.call_tool('interface_close', {}), timeout=2.0))
            if row.get('status') != 'busy' or time.monotonic() >= deadline:
                return row
            await asyncio.sleep(0.05)

    async def test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb(self):
        result_path = os.environ.get('AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT')
        report = {
            'schema':'agent-interface/standard-mcp-xvfb-blocked-release-v1',
            'status':'RUNNING',
            'scope':'standard MCP caller; private Xvfb; test-injected delayed request; synthetic app',
            'conditions':{
                'delayed_keypress_ms':_DELAY_MS,
                'cancel_return_bound_ms':_CANCEL_BOUND_MS,
                'child_cancel_ack_withheld_s':_CANCEL_ACK_WITHHOLD_S,
                'owner_process_method_trace':_TRACE_OWNER_PROCESS_METHODS,
                'terminal_result_bound_ms':_TERMINAL_BOUND_MS,
                'late_keypress_outcome':'record either result; do not assume queue cancellation',
            },
            'xvfb':_xvfb_provenance(),
            'source_identity':{
                'python':sys.version,
                'platform':platform.platform(),
                'github_sha':os.environ.get('GITHUB_SHA'),
                'github_run_id':os.environ.get('GITHUB_RUN_ID'),
                'github_job':os.environ.get('GITHUB_JOB'),
            },
            'timing_ns':{},
            'input_before_cancel':None,
            'cancel':None,
            'owner_release_attempt':None,
            'independent_release_readback':None,
            'late_request_horizon_readback':None,
            'synthetic_application_effect':None,
            'terminal':None,
            'final_cleanup':None,
        }
        app_display = observer = None
        server = None
        close_resolved = False
        app_thread = None
        app_stop = threading.Event()
        effect_committed = threading.Event()
        a_release_seen = threading.Event()
        b_press_seen = threading.Event()
        app_events = []
        app_lock = threading.Lock()
        owner_marker = None
        keycodes = None
        cancelled = False
        pending_call_id = None
        terminal_returned = False
        cleanup_errors = []

        with tempfile.TemporaryDirectory(prefix='mcp-xvfb-blocked-release-') as td:
            root = Path(td)
            try:
                app_display = display.Display()
                screen = app_display.screen()
                x, y, width, height = 40, 40, 240, 180
                window = screen.root.create_window(
                    x, y, width, height, 0, X.CopyFromParent, X.InputOutput,
                    X.CopyFromParent, background_pixel=0,
                    event_mask=(X.KeyPressMask | X.KeyReleaseMask |
                                X.StructureNotifyMask))
                effect_atom = app_display.intern_atom('AI_BLOCKED_RELEASE_EFFECT')
                window.change_property(effect_atom, Xatom.CARDINAL, 32, [0])
                window.map()
                window.set_input_focus(X.RevertToParent, X.CurrentTime)
                screen.root.warp_pointer(x+48, y+48)
                gc = window.create_gc(foreground=0xFFFFFF)
                for row in range((height+15)//16):
                    for column in range((width+15)//16):
                        if (row+column) % 2 == 0:
                            window.fill_rectangle(gc, column*16, row*16,
                                min(16, width-column*16),
                                min(16, height-row*16))
                app_display.sync()

                observer = display.Display()
                keycodes = {
                    name:observer.keysym_to_keycode(XK.string_to_keysym(name))
                    for name in ('a', 'b')
                }
                self.assertTrue(all(code > 0 for code in keycodes.values()), keycodes)
                for code in keycodes.values():
                    from Xlib.ext import xtest
                    xtest.fake_input(observer, X.KeyRelease, detail=code)
                observer.sync()
                report['initial_keymap'] = {
                    name:_key_down(observer, code) for name, code in keycodes.items()}
                self.assertFalse(any(report['initial_keymap'].values()), report)

                def run_synthetic_application():
                    while not app_stop.is_set():
                        if not app_display.pending_events():
                            time.sleep(0.002)
                            continue
                        event = app_display.next_event()
                        now = time.monotonic_ns()
                        with app_lock:
                            row = {'type':event.type,
                                   'detail':getattr(event, 'detail', None),
                                   'monotonic_ns':now}
                            app_events.append(row)
                        if event.type == X.KeyPress and event.detail == keycodes['a']:
                            window.change_property(effect_atom, Xatom.CARDINAL,
                                                   32, [1])
                            app_display.sync()
                            with app_lock:
                                app_events[-1]['effect_committed_ns'] = time.monotonic_ns()
                            effect_committed.set()
                        elif event.type == X.KeyRelease and event.detail == keycodes['a']:
                            a_release_seen.set()
                        elif event.type == X.KeyPress and event.detail == keycodes['b']:
                            window.change_property(effect_atom, Xatom.CARDINAL,
                                                   32, [2])
                            app_display.sync()
                            b_press_seen.set()

                app_thread = threading.Thread(
                    target=run_synthetic_application,
                    name='xvfb-blocked-release-app', daemon=True)
                app_thread.start()

                owner_output_root = root/'mcp'
                report['owner_marker_directory'] = str(owner_output_root)
                server = create_server(
                    {'app':window.id}, owner_output_root, session_mode='guarded-x11',
                    guarded_process_identity=True, guarded_query_worker=True,
                    guarded_window_lifecycle=True, guarded_owned_process=True,
                    _guarded_owner_factory=_xvfb_blocking_owner_factory)

                report['timing_ns']['observe_started'] = time.monotonic_ns()
                observed = _metadata(await server.call_tool(
                    'interface_guarded_observe', {}))
                report['timing_ns']['observe_returned'] = time.monotonic_ns()
                report['observation'] = {
                    'status':observed.get('status'),
                    'process_generation':observed.get('source', {}).get(
                        'pointer_binding', {}).get('process_generation'),
                    'sequence':observed.get('source', {}).get('sequence'),
                    'xvfb':observer.display.info.vendor,
                }
                self.assertEqual(observed['status'], 'observed', observed)
                source = observed['source']
                binding = source['pointer_binding']
                report['observation']['pointer_binding'] = binding
                self.assertRegex(binding.get('process_generation', ''), r'^[0-9a-f]{64}$')
                self.assertRegex(binding.get('window_generation', ''), r'^[0-9a-f]{64}$')
                image_artifact = observed['observation_report']['observation']['artifact']
                image_path = Path(image_artifact['path'])
                image_bytes = image_path.read_bytes()
                image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                patch = image.crop((x+36, y+36, x+60, y+60))
                patch_stddev = ImageStat.Stat(patch).stddev
                report['mint_source_patch'] = {
                    'box':[x+36,y+36,x+60,y+60],
                    'stddev':patch_stddev,
                    'capture_sha256':image_artifact['sha256'],
                    'capture_bytes':image_artifact['bytes'],
                }
                self.assertGreaterEqual(max(patch_stddev), 8.0, report)
                if result_path:
                    retained_image = Path(result_path).with_suffix('.observation.png')
                    retained_image.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(image_path, retained_image)
                    report['mint_source_patch']['retained_image'] = str(retained_image)
                    report['mint_source_patch']['retained_image_sha256'] = hashlib.sha256(
                        retained_image.read_bytes()).hexdigest()

                minted = _metadata(await server.call_tool('interface_guarded_mint', {
                    'alias':'field', 'source_sequence':source['sequence'],
                    'point':[x+48,y+48], 'region_size':[24,24]}))
                report['mint'] = minted
                self.assertEqual(minted['status'], 'minted', minted)

                report['timing_ns']['input_started'] = time.monotonic_ns()
                pending = _metadata(await server.call_tool('interface_guarded_input', {
                    'alias':'field', 'offset':minted['offset'],
                    'interaction':'keyboard', 'observe_after':False,
                    'wait_for_result_ms':0,
                    'tail':[{'op':'key_chord', 'keys':['a']}]}))
                report['timing_ns']['pending_returned'] = time.monotonic_ns()
                report['pending'] = {'status':pending.get('status'),
                                     'call_id':pending.get('call_id')}
                self.assertEqual(pending['status'], 'pending', pending)
                pending_call_id = pending['call_id']

                owner_marker = await self._wait_for_file(
                    owner_output_root/'xvfb-delayed-request-queued.json')
                report['owner_delayed_request'] = owner_marker
                self.assertEqual(owner_marker['delay_ms'], _DELAY_MS, owner_marker)
                sync_marker = await self._wait_for_file(
                    owner_output_root/'xvfb-owner-sync-entered.json')
                report['blocked_owner_sync'] = sync_marker
                self.assertEqual(sync_marker['owner_pid'], owner_marker['owner_pid'])
                self.assertEqual(sync_marker['resource_base'], owner_marker['resource_base'])
                await self._wait_for_event(effect_committed)
                before_cancel_effect = observer.create_resource_object(
                    'window', window.id).get_full_property(effect_atom, X.AnyPropertyType)
                before_cancel_value = (
                    list(before_cancel_effect.value) if before_cancel_effect is not None else None)
                report['effect_before_cancel'] = {
                    'property_value':before_cancel_value,
                    'reader':'separate parent X client',
                    'observed_ns':time.monotonic_ns(),
                }
                self.assertEqual(before_cancel_value, [1], report)
                down_before = {
                    name:_key_down(observer, code) for name, code in keycodes.items()}
                report['input_before_cancel'] = {
                    'keys_down':down_before,
                    'synthetic_effect_committed':True,
                    'observed_ns':time.monotonic_ns(),
                    'owner_sync_return_receipt_present':(
                        (root/'xvfb-owner-sync-returned.json').exists()),
                }
                self.assertEqual(down_before, {'a':True,'b':False}, report)
                self.assertFalse(
                    report['input_before_cancel']['owner_sync_return_receipt_present'],
                    report)

                cancel_internal_trace = {
                    'cancel_entries':[], 'cancel_returns':[],
                    'retirement_decisions':[], 'retire_calls':[],
                    'owner_process_calls':[]}
                def describe_owner_process(owned):
                    process = getattr(owned, '_process', None)
                    row = {
                        'caller_pid':os.getpid(),
                        'caller_thread':threading.current_thread().name,
                        'owner_object_id':id(owned),
                        'process_present':process is not None,
                        'control_present':getattr(owned, '_control', None) is not None,
                    }
                    if process is None:
                        return row
                    row.update(
                        process_type=type(process).__module__+'.'+type(process).__qualname__,
                        process_pid=getattr(process, 'pid', None),
                        process_parent_pid=getattr(process, '_parent_pid', None),
                        process_popen_present=getattr(process, '_popen', None) is not None,
                        process_kill_callable=callable(getattr(process, 'kill', None)))
                    popen = getattr(process, '_popen', None)
                    row['process_returncode'] = getattr(popen, 'returncode', None)
                    try:
                        row['process_alive'] = process.is_alive()
                    except BaseException as error:
                        row['process_alive_error'] = repr(error)
                    try:
                        row['process_exitcode'] = process.exitcode
                    except BaseException as error:
                        row['process_exitcode_error'] = repr(error)
                    return row

                original_decision_method = (
                    OwnedGuardedSessionOwner._cancel_requires_owner_retirement)
                original_retire = OwnedGuardedSessionOwner._retire
                original_cancel = OwnedGuardedSessionOwner.cancel_guarded

                def traced_cancel(owned, token):
                    entry = describe_owner_process(owned)
                    cancel_internal_trace['cancel_entries'].append(entry)
                    started_ns = time.monotonic_ns()
                    try:
                        result = original_cancel(owned, token)
                    except BaseException as error:
                        cancel_internal_trace['cancel_returns'].append({
                            'elapsed_ms':(time.monotonic_ns()-started_ns)/1_000_000,
                            'error_type':type(error).__name__,
                            'error':repr(error),
                            'process_after':describe_owner_process(owned),
                        })
                        raise
                    cancel_internal_trace['cancel_returns'].append({
                        'elapsed_ms':(time.monotonic_ns()-started_ns)/1_000_000,
                        'status':result.get('status') if isinstance(result, dict) else None,
                        'owner_process_retired':result.get('owner_process_retired')
                            if isinstance(result, dict) else None,
                        'owner_process_exitcode':result.get('owner_process_exitcode')
                            if isinstance(result, dict) else None,
                        'process_after':describe_owner_process(owned),
                    })
                    return result

                def traced_retirement_decision(owned, result):
                    required = original_decision_method(owned, result)
                    cancel_internal_trace['retirement_decisions'].append({
                        'required':required,
                        'result_status':result.get('status'),
                        'result_owner_process_retired':result.get('owner_process_retired'),
                        'result_late_server_request_possible':result.get(
                            'late_server_request_possible'),
                        'result_obligations':result.get('owner_input_obligations'),
                        'cached_obligations':getattr(
                            owned, '_owner_input_obligations', None),
                        'cached_snapshot_owner_pid':owned._snapshot_cache.get(
                            'owner_process_pid'),
                        'process':describe_owner_process(owned),
                    })
                    return required

                def traced_retire(owned, reason):
                    process = getattr(owned, '_process', None)
                    before_alive = process.is_alive() if process is not None else None
                    started_ns = time.monotonic_ns()
                    original_process_methods = {}
                    if process is not None and _TRACE_OWNER_PROCESS_METHODS:
                        for method_name in ('is_alive', 'terminate', 'join', 'kill'):
                            original_method = getattr(process, method_name, None)
                            if not callable(original_method):
                                continue
                            original_process_methods[method_name] = original_method

                            def traced_process_method(*args, _name=method_name,
                                                     _method=original_method, **kwargs):
                                method_started_ns = time.monotonic_ns()
                                row = {'method':_name, 'args':list(args),
                                       'kwargs':dict(kwargs)}
                                try:
                                    result = _method(*args, **kwargs)
                                except BaseException as error:
                                    row.update(error_type=type(error).__name__,
                                               error=repr(error))
                                    raise
                                else:
                                    if result is None or type(result) in (bool, int, float, str):
                                        row['result'] = result
                                    else:
                                        row['result_type'] = type(result).__name__
                                    return result
                                finally:
                                    row['elapsed_ms'] = (
                                        time.monotonic_ns()-method_started_ns)/1_000_000
                                    cancel_internal_trace['owner_process_calls'].append(row)

                            setattr(process, method_name, traced_process_method)
                    try:
                        result = original_retire(owned, reason)
                    except BaseException as error:
                        for method_name, original_method in original_process_methods.items():
                            setattr(process, method_name, original_method)
                        cancel_internal_trace['retire_calls'].append({
                            'reason':reason,
                            'elapsed_ms':(time.monotonic_ns()-started_ns)/1_000_000,
                            'before_alive':before_alive,
                            'process':describe_owner_process(owned),
                            'error_type':type(error).__name__,
                            'error':repr(error),
                        })
                        raise
                    for method_name, original_method in original_process_methods.items():
                        setattr(process, method_name, original_method)
                    cancel_internal_trace['retire_calls'].append({
                        'reason':reason,
                        'elapsed_ms':(time.monotonic_ns()-started_ns)/1_000_000,
                        'before_alive':before_alive,
                        'retired':result.get('retired'),
                        'exitcode':result.get('exitcode'),
                        'configured_terminate_grace_s':(
                            owned_session_module._RETIRE_TERMINATE_GRACE_S),
                        'configured_kill_grace_s':(
                            owned_session_module._RETIRE_KILL_GRACE_S),
                        'alive_after':process.is_alive() if process is not None else None,
                        'process_after':describe_owner_process(owned),
                    })
                    return result

                report['timing_ns']['cancel_started'] = time.monotonic_ns()
                original_retire_method = OwnedGuardedSessionOwner._retire
                original_cancel_method = OwnedGuardedSessionOwner.cancel_guarded
                OwnedGuardedSessionOwner._cancel_requires_owner_retirement = (
                    traced_retirement_decision)
                OwnedGuardedSessionOwner._retire = traced_retire
                OwnedGuardedSessionOwner.cancel_guarded = traced_cancel
                try:
                    cancel = _metadata(await server.call_tool(
                        'interface_guarded_cancel', {'call_id':pending['call_id']}))
                finally:
                    OwnedGuardedSessionOwner._cancel_requires_owner_retirement = (
                        original_decision_method)
                    OwnedGuardedSessionOwner._retire = original_retire_method
                    OwnedGuardedSessionOwner.cancel_guarded = original_cancel_method
                report['timing_ns']['cancel_returned'] = time.monotonic_ns()
                cancel_elapsed_ms = (
                    report['timing_ns']['cancel_returned']
                    - report['timing_ns']['cancel_started'])/1_000_000
                report['cancel_elapsed_ms'] = cancel_elapsed_ms
                report['cancel'] = cancel
                report['cancel_internal_trace'] = cancel_internal_trace
                cancelled = True
                self.assertLess(cancel_elapsed_ms, _CANCEL_BOUND_MS, cancel)
                expected_cancel_status = (
                    'cancel_unconfirmed' if _CANCEL_ACK_WITHHOLD_S
                    else 'cancel_requested')
                self.assertEqual(cancel.get('status'), expected_cancel_status, cancel)
                if _CANCEL_ACK_WITHHOLD_S:
                    self.assertIsNone(cancel.get('input_dispatched'), cancel)
                else:
                    self.assertFalse(cancel.get('input_dispatched'), cancel)
                ack_marker = owner_output_root/'xvfb-cancel-ack-withheld.json'
                self.assertTrue(ack_marker.exists(), report)
                report['cancel_control_ack_withheld'] = json.loads(
                    ack_marker.read_text(encoding='utf-8'))
                process_calls = cancel_internal_trace['owner_process_calls']
                if _TRACE_OWNER_PROCESS_METHODS:
                    self.assertTrue(process_calls, cancel_internal_trace)
                else:
                    self.assertEqual(process_calls, [], cancel_internal_trace)
                self.assertTrue(cancel.get('owner_process_retired'), cancel)
                self.assertEqual(cancel.get('owner_client_disconnect', {}).get('status'),
                                 'disconnected', cancel)
                self.assertEqual(cancel.get('owner_release_attempt', {}).get('status'),
                                 'readback_verified', cancel)
                self.assertFalse(cancel.get('release_confirmed'), cancel)
                self.assertEqual(cancel.get('cleanup_status'), 'UNKNOWN', cancel)
                self.assertIsNone(cancel.get('task_success'), cancel)
                self.assertFalse(cancel.get('replay_allowed'), cancel)
                self.assertTrue(cancel.get('late_server_request_possible'), cancel)
                self.assertTrue(cancel['owner_release_attempt']['release']['verified'])

                await self._wait_for_event(a_release_seen)
                release_readback = {
                    name:_key_down(observer, code) for name, code in keycodes.items()}
                report['independent_release_readback'] = {
                    'keys_down':release_readback,
                    'owner_release_attempt':cancel['owner_release_attempt'],
                    'reader':'separate parent X client',
                    'observed_ns':time.monotonic_ns(),
                }
                self.assertEqual(release_readback, {'a':False,'b':False}, report)

                horizon_ns = (report['timing_ns']['cancel_started']
                              + (_DELAY_MS+500)*1_000_000)
                while time.monotonic_ns() < horizon_ns:
                    await asyncio.sleep(min(0.02,
                        (horizon_ns-time.monotonic_ns())/1_000_000_000))
                late = {name:_key_down(observer, code)
                        for name, code in keycodes.items()}
                if late['b']:
                    await self._wait_for_event(b_press_seen)
                effect = observer.create_resource_object('window', window.id).get_full_property(
                    effect_atom, X.AnyPropertyType)
                effect_value = list(effect.value) if effect is not None else None
                report['late_request_horizon_readback'] = {
                    'keys_down':late,
                    'late_keypress_b_observed':late['b'],
                    'ms_after_cancel_start':(
                        time.monotonic_ns()-report['timing_ns']['cancel_started'])/1_000_000,
                    'reader':'separate parent X client',
                    'observed_ns':time.monotonic_ns(),
                }
                report['synthetic_application_effect'] = {
                    'before_cancel_property_value':before_cancel_value,
                    'property_value':effect_value,
                    'expected_initial_key_effect':[1],
                    'task_success':None,
                    'independent_reader':'separate parent X client',
                    'app_key_events':None,
                    'late_b_press_event_seen':b_press_seen.is_set(),
                }
                with app_lock:
                    report['synthetic_application_effect']['app_key_events'] = list(app_events)
                # Either delayed-b outcome is evidence. Do not convert a live
                # result into an assumed general queue-drain guarantee.
                self.assertFalse(late['a'], report)
                self.assertIn(effect_value, ([1],[2]), report)

                report['timing_ns']['terminal_started'] = time.monotonic_ns()
                terminal = _metadata(await server.call_tool('interface_results', {
                    'call_id':pending['call_id'], 'include_image':False}))
                report['timing_ns']['terminal_returned'] = time.monotonic_ns()
                terminal_elapsed_ms = (
                    report['timing_ns']['terminal_returned']
                    - report['timing_ns']['terminal_started'])/1_000_000
                report['terminal_elapsed_ms'] = terminal_elapsed_ms
                report['terminal'] = terminal
                terminal_returned = True
                self.assertLess(terminal_elapsed_ms, _TERMINAL_BOUND_MS, terminal)
                self.assertNotEqual(terminal.get('status'), 'pending', terminal)
                self.assertFalse(terminal.get('release_confirmed'), terminal)
                self.assertEqual(terminal.get('cleanup_status'), 'UNKNOWN', terminal)
                self.assertIsNone(terminal.get('task_success'), terminal)
                self.assertFalse(terminal.get('replay_allowed'), terminal)

                report['status'] = (
                    'OBSERVED_SCOPED_XVFB_STANDARD_CALLER_CANCEL_CLEANUP_UNKNOWN')
            except BaseException as error:
                report.update(status='FAIL', error_type=type(error).__name__,
                              error=str(error))
                raise
            finally:
                if server is not None and pending_call_id and not cancelled:
                    try:
                        report['final_cleanup_cancel'] = _metadata(await asyncio.wait_for(
                            server.call_tool('interface_guarded_cancel',
                                             {'call_id':pending_call_id}),
                            timeout=6.0))
                    except BaseException as error:
                        report['final_cleanup_cancel_error'] = repr(error)
                        cleanup_errors.append(f'fallback cancel failed: {error!r}')
                if server is not None and pending_call_id and not terminal_returned:
                    try:
                        report['final_cleanup_terminal'] = await self._wait_for_terminal(
                            server, pending_call_id)
                        if report['final_cleanup_terminal'].get('status') == 'pending':
                            cleanup_errors.append('guarded input call remained pending after cleanup wait')
                    except BaseException as error:
                        report['final_cleanup_terminal_error'] = repr(error)
                        cleanup_errors.append(f'terminal result retrieval failed: {error!r}')
                if server is not None and not close_resolved:
                    try:
                        close_row = await self._close_after_work(server)
                        report['close'] = close_row
                        close_resolved = close_row.get('status') == 'closed'
                        if (not close_resolved
                                and close_row.get('status') == 'cleanup_failed'
                                and close_row.get('cleanup_status') == 'UNKNOWN'
                                and close_row.get('release_confirmed') is False
                                and close_row.get('task_success') is None
                                and close_row.get('replay_allowed') is False
                                and close_row.get('owner_process_retired') is True
                                and close_row.get('late_server_request_possible') is True
                                and close_row.get('owner_client_disconnect', {}).get(
                                    'status') == 'disconnected'
                                and close_row.get('owner_release_attempt') ==
                                    report.get('cancel', {}).get('owner_release_attempt')):
                            # Retirement intentionally leaves the contract UNKNOWN.
                            # A repeated close must preserve the already recorded
                            # cleanup attempt, not issue another release.
                            report['close_outcome'] = 'fail_closed_after_owner_retirement'
                            close_resolved = True
                        if not close_resolved:
                            cleanup_errors.append(f'private MCP server did not close cleanly: {close_row!r}')
                    except BaseException as error:
                        report['close_error'] = repr(error)
                        cleanup_errors.append(f'private MCP close failed: {error!r}')
                app_stop.set()
                if app_thread is not None:
                    app_thread.join(1.0)
                    if app_thread.is_alive():
                        cleanup_errors.append('synthetic application thread did not stop')
                if observer is not None and keycodes is not None:
                    try:
                        from Xlib.ext import xtest
                        for code in keycodes.values():
                            xtest.fake_input(observer, X.KeyRelease, detail=code)
                        observer.sync()
                        report['final_cleanup'] = {
                            'keys_down':{name:_key_down(observer, code)
                                         for name, code in keycodes.items()},
                            'status':'key_release_sync_completed',
                        }
                        if any(report['final_cleanup']['keys_down'].values()):
                            report['final_cleanup']['status'] = 'input_still_down_after_cleanup'
                            cleanup_errors.append(
                                f"input remained down after final release: {report['final_cleanup']['keys_down']!r}")
                    except BaseException as error:
                        report['final_cleanup'] = {'status':'failed',
                                                   'error':repr(error)}
                        cleanup_errors.append(f'final release/readback failed: {error!r}')
                if app_display is not None:
                    try:
                        app_display.close()
                    except Exception:
                        pass
                if observer is not None:
                    try:
                        observer.close()
                    except Exception:
                        pass
                if result_path:
                    output = Path(result_path)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    if cleanup_errors:
                        report['cleanup_errors'] = cleanup_errors
                        if report.get('status') != 'FAIL':
                            report['status'] = 'FAIL_CLEANUP'
                    output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n',
                                      encoding='utf-8')
                if cleanup_errors and report.get('status') != 'FAIL':
                    self.fail(f'private Xvfb integration cleanup failed: {cleanup_errors}')


if __name__ == '__main__':
    unittest.main()
