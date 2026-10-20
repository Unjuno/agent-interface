"""Fail-closed caller behavior while the owned private Xvfb is stopped.

This test freezes only the Xvfb process launched by runtime-x11-v1.yml. It
distinguishes bounded MCP cancellation from physical key release: no release
receipt is accepted while the server cannot process or acknowledge X requests.
"""

import asyncio
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import threading
import time
import unittest

from Xlib import X, Xatom, XK, display
from Xlib.ext import xtest

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import (
    _DELAY_MS, _key_down, _metadata, _xvfb_blocking_owner_factory,
)
from runtime.cli_v1.test_synthetic_task_oracle import (
    score_synthetic_application_task,
)


_SERVER_STOP_SAFETY_S = 4.0
_CANCEL_BOUND_S = 3.0


def _private_xvfb_record():
    pid_text = os.environ.get('AGENT_INTERFACE_XVFB_PID')
    if not pid_text or not pid_text.isdigit():
        raise RuntimeError('workflow-owned Xvfb PID is unavailable')
    pid = int(pid_text)
    proc = Path('/proc', str(pid))
    executable = str((proc/'exe').resolve())
    command = [part.decode('utf-8', 'replace') for part in
               (proc/'cmdline').read_bytes().split(b'\0') if part]
    stat = (proc/'stat').read_text(encoding='ascii')
    close = stat.rfind(')')
    fields = stat[close+1:].split()
    record = {'pid':pid, 'executable':executable, 'command':command,
              'state':fields[0], 'start_ticks':int(fields[19])}
    if Path(executable).name != 'Xvfb' or ':88' not in command:
        raise RuntimeError('refusing to signal a process other than private Xvfb :88')
    return record


def _signal_private_xvfb(identity, signum):
    current = _private_xvfb_record()
    if any(current[key] != identity[key]
           for key in ('pid', 'executable', 'command', 'start_ticks')):
        raise RuntimeError('private Xvfb process identity changed')
    os.kill(identity['pid'], signum)
    return _private_xvfb_record()


@unittest.skipUnless(
    sys.platform == 'linux' and os.environ.get('DISPLAY') == ':88'
    and os.environ.get('AGENT_INTERFACE_MCP_XVFB_TEST') == '1'
    and os.environ.get('AGENT_INTERFACE_MCP_XVFB_SERVER_STOP_TEST') == '1',
    'requires the explicitly enabled workflow-owned private Xvfb server',
)
class StandardCallerServerStopTests(unittest.IsolatedAsyncioTestCase):
    async def _wait_for_file(self, path, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not path.exists():
            await asyncio.sleep(0.005)
        self.assertTrue(path.exists(), f'timed out waiting for {path.name}')
        return json.loads(path.read_text(encoding='utf-8'))

    async def _wait_for_server_state(self, identity, expected, timeout=1.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if _private_xvfb_record()['state'] == expected:
                return _private_xvfb_record()
            await asyncio.sleep(0.005)
        self.fail(f'private Xvfb did not enter process state {expected}')

    async def test_cancel_is_bounded_and_release_stays_unknown_while_server_stops(self):
        result_path = os.environ.get('AGENT_INTERFACE_MCP_XVFB_SERVER_STOP_RESULT')
        report = {
            'schema':'agent-interface/standard-mcp-xvfb-server-stop-v1',
            'status':'RUNNING',
            'scope':'owned standard MCP caller, private Xvfb process stop, synthetic app',
            'conditions':{
                'server_stop_safety_s':_SERVER_STOP_SAFETY_S,
                'cancel_response_bound_s':_CANCEL_BOUND_S,
                'delayed_request_time_field_ms':_DELAY_MS,
                'server_resume_policy':'resume exact workflow-owned Xvfb in finally',
            },
            'timing_ns':{}, 'owner_sync':None, 'server_process':None,
            'cancel':None, 'independent_readback_after_resume':None,
            'synthetic_task_oracle':None, 'final_cleanup':None,
        }
        app_display = observer = server = None
        app_thread = None
        app_stop = threading.Event()
        effect_seen = threading.Event()
        release_seen = threading.Event()
        app_lock = threading.Lock()
        app_events = []
        safety_timer = None
        resume_lock = threading.Lock()
        resumed = {'value':False, 'receipt':None, 'error':None}
        frozen_identity = None
        call_id = None
        output_root = None

        def resume_exact_server():
            with resume_lock:
                if resumed['value']:
                    return resumed['receipt']
                try:
                    current = _private_xvfb_record()
                    if any(current[key] != frozen_identity[key] for key in
                           ('pid', 'executable', 'command', 'start_ticks')):
                        raise RuntimeError('private Xvfb identity changed before resume')
                    if current['state'] in ('T', 't'):
                        current = _signal_private_xvfb(frozen_identity, signal.SIGCONT)
                    resumed['receipt'] = {
                        'status':'resumed', 'monotonic_ns':time.monotonic_ns(),
                        'signal':'SIGCONT', 'process':current,
                    }
                except BaseException as error:
                    resumed['error'] = repr(error)
                    resumed['receipt'] = {
                        'status':'resume_failed', 'monotonic_ns':time.monotonic_ns(),
                        'error':repr(error),
                    }
                resumed['value'] = True
                return resumed['receipt']

        with tempfile.TemporaryDirectory(prefix='mcp-xvfb-server-stop-') as td:
            root = Path(td)
            try:
                app_display = display.Display()
                screen = app_display.screen()
                x, y, width, height = 40, 40, 240, 180
                window = screen.root.create_window(
                    x, y, width, height, 0, X.CopyFromParent, X.InputOutput,
                    X.CopyFromParent, background_pixel=0,
                    event_mask=(X.KeyPressMask | X.KeyReleaseMask))
                effect_atom = app_display.intern_atom('AI_SERVER_STOP_EFFECT')
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
                    for name in ('a', 'b')}
                self.assertTrue(all(code > 0 for code in keycodes.values()), keycodes)
                for code in keycodes.values():
                    xtest.fake_input(observer, X.KeyRelease, detail=code)
                observer.sync()

                def run_app():
                    while not app_stop.is_set():
                        if not app_display.pending_events():
                            time.sleep(0.002)
                            continue
                        event = app_display.next_event()
                        row = {'type':event.type,
                               'detail':getattr(event, 'detail', None),
                               'monotonic_ns':time.monotonic_ns()}
                        with app_lock:
                            app_events.append(row)
                        if event.type == X.KeyPress and event.detail == keycodes['a']:
                            window.change_property(effect_atom, Xatom.CARDINAL, 32, [1])
                            app_display.sync()
                            with app_lock:
                                app_events[-1]['effect_committed_ns'] = time.monotonic_ns()
                            effect_seen.set()
                        elif event.type == X.KeyRelease and event.detail == keycodes['a']:
                            release_seen.set()
                        elif event.type == X.KeyPress and event.detail == keycodes['b']:
                            window.change_property(effect_atom, Xatom.CARDINAL, 32, [2])
                            app_display.sync()

                app_thread = threading.Thread(target=run_app,
                    name='xvfb-server-stop-test-app', daemon=True)
                app_thread.start()
                output_root = root/'mcp'
                server = create_server(
                    {'app':window.id}, output_root, session_mode='guarded-x11',
                    guarded_process_identity=True, guarded_query_worker=True,
                    guarded_window_lifecycle=True, guarded_owned_process=True,
                    _guarded_owner_factory=_xvfb_blocking_owner_factory)

                observed = _metadata(await server.call_tool(
                    'interface_guarded_observe', {}))
                self.assertEqual(observed.get('status'), 'observed', observed)
                source = observed['source']
                minted = _metadata(await server.call_tool('interface_guarded_mint', {
                    'alias':'field', 'source_sequence':source['sequence'],
                    'point':[x+48,y+48], 'region_size':[24,24]}))
                self.assertEqual(minted.get('status'), 'minted', minted)
                pending = _metadata(await server.call_tool('interface_guarded_input', {
                    'alias':'field', 'offset':minted['offset'],
                    'interaction':'keyboard', 'observe_after':False,
                    'wait_for_result_ms':0,
                    'tail':[{'op':'key_chord', 'keys':['a']}]}))
                self.assertEqual(pending.get('status'), 'pending', pending)
                call_id = pending['call_id']
                report['pending'] = {'call_id':call_id, 'status':pending['status']}
                report['owner_sync'] = await self._wait_for_file(
                    output_root/'xvfb-owner-sync-entered.json')
                await asyncio.wait_for(asyncio.to_thread(effect_seen.wait, 2.0), 2.5)
                report['before_stop'] = {
                    'effect':list(observer.create_resource_object(
                        'window', window.id).get_full_property(
                            effect_atom, X.AnyPropertyType).value),
                    'keys_down':{name:_key_down(observer, code)
                                 for name, code in keycodes.items()},
                    'monotonic_ns':time.monotonic_ns(),
                }
                self.assertEqual(report['before_stop']['effect'], [1])
                self.assertEqual(report['before_stop']['keys_down'],
                                 {'a':True, 'b':False})

                frozen_identity = _private_xvfb_record()
                report['server_process'] = dict(
                    frozen_identity, signal='SIGSTOP',
                    stop_requested_ns=time.monotonic_ns())
                _signal_private_xvfb(frozen_identity, signal.SIGSTOP)
                stopped = await self._wait_for_server_state(frozen_identity, 'T')
                report['server_process']['stopped_ns'] = time.monotonic_ns()
                report['server_process']['stopped_state'] = stopped['state']
                safety_timer = threading.Timer(
                    _SERVER_STOP_SAFETY_S, resume_exact_server)
                safety_timer.daemon = True
                safety_timer.start()

                report['timing_ns']['cancel_started'] = time.monotonic_ns()
                cancel = _metadata(await server.call_tool(
                    'interface_guarded_cancel', {'call_id':call_id}))
                report['timing_ns']['cancel_returned'] = time.monotonic_ns()
                elapsed_s = ((report['timing_ns']['cancel_returned']
                              - report['timing_ns']['cancel_started']) / 1_000_000_000)
                report['cancel_elapsed_s'] = elapsed_s
                report['cancel'] = cancel
                # Resume as soon as the bounded call returns; the safety timer
                # handles a broken bound without blocking final cleanup forever.
                report['server_resume'] = resume_exact_server()
                safety_timer.cancel()

                self.assertEqual(report['server_resume'].get('status'), 'resumed',
                                 report['server_resume'])
                self.assertLess(elapsed_s, _CANCEL_BOUND_S, cancel)
                self.assertTrue(cancel.get('owner_process_retired'), cancel)
                self.assertFalse(cancel.get('release_confirmed'), cancel)
                self.assertEqual(cancel.get('cleanup_status'), 'UNKNOWN', cancel)
                self.assertIsNone(cancel.get('task_success'), cancel)
                self.assertFalse(cancel.get('replay_allowed'), cancel)
                self.assertTrue(cancel.get('late_server_request_possible'), cancel)
                self.assertIn(cancel.get('owner_client_disconnect', {}).get('status'),
                              ('unknown', 'still_connected'), cancel)
                self.assertEqual(cancel.get('owner_release_attempt', {}).get('status'),
                                 'unknown', cancel)
                report['server_stop_ms'] = (
                    report['server_resume']['monotonic_ns']
                    - report['server_process']['stopped_ns']) / 1_000_000
                report['cancel_returned_before_server_resume'] = (
                    report['timing_ns']['cancel_returned']
                    < report['server_resume']['monotonic_ns'])

                # The X server may process a queued release only after resume.
                # This later independent readback cannot upgrade the earlier
                # UNKNOWN release receipt.
                await asyncio.sleep(0.25)
                release_readback = {
                    name:_key_down(observer, code) for name, code in keycodes.items()}
                release_effect_row = observer.create_resource_object(
                    'window', window.id).get_full_property(effect_atom, X.AnyPropertyType)
                release_effect = (list(release_effect_row.value)
                                  if release_effect_row is not None else None)
                horizon_ns = (report['timing_ns']['cancel_started']
                              + (_DELAY_MS+500)*1_000_000)
                while time.monotonic_ns() < horizon_ns:
                    await asyncio.sleep(min(0.02,
                        (horizon_ns-time.monotonic_ns())/1_000_000_000))
                horizon_readback = {
                    name:_key_down(observer, code) for name, code in keycodes.items()}
                effect_row = observer.create_resource_object(
                    'window', window.id).get_full_property(effect_atom, X.AnyPropertyType)
                final_effect = list(effect_row.value) if effect_row is not None else None
                report['independent_readback_after_resume'] = {
                    'release_readback':release_readback,
                    'release_effect':release_effect,
                    'horizon_readback':horizon_readback,
                    'effect':final_effect,
                    'release_event_seen':release_seen.is_set(),
                    'reader':'separate parent X client',
                    'monotonic_ns':time.monotonic_ns(),
                }
                report['synthetic_task_oracle'] = {
                    'definition':'one a effect and both a/b keys up after recovery horizon',
                    'initial_effect':[1], 'final_effect':final_effect,
                    'release_readback':release_readback,
                    'horizon_readback':horizon_readback,
                    **score_synthetic_application_task(
                        initial_effect=[1], final_effect=final_effect,
                        release_readback=release_readback,
                        horizon_readback=horizon_readback),
                }
                terminal = _metadata(await server.call_tool('interface_results', {
                    'call_id':call_id, 'include_image':False}))
                report['terminal'] = terminal
                self.assertNotEqual(terminal.get('status'), 'pending', terminal)
                self.assertFalse(terminal.get('release_confirmed'), terminal)
                self.assertEqual(terminal.get('cleanup_status'), 'UNKNOWN', terminal)
                self.assertIsNone(terminal.get('task_success'), terminal)
                self.assertFalse(terminal.get('replay_allowed'), terminal)
                report['status'] = 'BOUNDED_CANCEL_RELEASE_UNKNOWN_DURING_PRIVATE_XVFB_STOP'
            except BaseException as error:
                report.update(status='FAIL', error_type=type(error).__name__,
                              error=str(error))
                raise
            finally:
                if frozen_identity is not None:
                    report['server_resume'] = resume_exact_server()
                    if safety_timer is not None:
                        safety_timer.cancel()
                if server is not None and call_id is not None:
                    try:
                        await server.call_tool('interface_close', {})
                    except BaseException as error:
                        report['close_error'] = repr(error)
                app_stop.set()
                if app_thread is not None:
                    app_thread.join(1.0)
                if observer is not None:
                    try:
                        for name in ('a', 'b'):
                            code = observer.keysym_to_keycode(XK.string_to_keysym(name))
                            xtest.fake_input(observer, X.KeyRelease, detail=code)
                        observer.sync()
                        report['final_cleanup'] = {
                            'keys_down':{
                                name:_key_down(observer, observer.keysym_to_keycode(
                                    XK.string_to_keysym(name))) for name in ('a','b')},
                            'status':'completed',
                        }
                    except BaseException as error:
                        report['final_cleanup'] = {'status':'failed', 'error':repr(error)}
                if app_display is not None:
                    try:
                        app_display.close()
                    except BaseException:
                        pass
                if observer is not None:
                    try:
                        observer.close()
                    except BaseException:
                        pass
                if result_path:
                    target = Path(result_path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(report, indent=2, sort_keys=True)
                                      + '\n', encoding='utf-8')
