"""Experimental MCP cancellation on an exclusively owned disposable Xvfb."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


@unittest.skipUnless(sys.platform.startswith('linux') and hasattr(os, 'pidfd_open')
                     and shutil.which('Xvfb') and shutil.which('xauth')
                     and importlib.util.find_spec('Xlib'), 'Linux pidfd, Xvfb, xauth and Xlib required')
class McpPrivateDisplayRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_successive_cancellation_operations_reach_owner(self):
        from Xlib import X, display
        from Xlib.error import ConnectionClosedError
        from runtime.cli_v1.mcp_server import create_server
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner

        def metadata(result): return json.loads(result.content[0].text)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); owner = PrivateDisplayOwner(root/'display'); app = server = None
            try:
                session = owner.start(timeout_s=5)
                with patch.dict(os.environ, {'XAUTHORITY':str(session.authority)}):
                    app = display.Display(session.display)
                win = app.screen().root.create_window(10,10,200,120,0,
                    app.screen().root_depth,X.InputOutput,X.CopyFromParent)
                win.map(); win.set_input_focus(X.RevertToParent,X.CurrentTime); app.sync()
                gc = win.create_gc(foreground=app.screen().white_pixel)
                win.fill_rectangle(gc,16,16,8,8); app.sync()
                server = create_server({'app':win.id}, root/'mcp', display_name=session.display,
                    session_mode='guarded-x11', guarded_owned_process=True,
                    guarded_process_identity=True, guarded_query_worker=True,
                    guarded_prestarted_cancel_supervisor=True,
                    _guarded_display_owner=owner, _guarded_xauthority=str(session.authority),
                    _guarded_recovery_retirement_reserve_ns=1)
                operation_ids = []
                with patch.object(OwnedGuardedSessionOwner, 'cancel_guarded', return_value={
                    'status':'cancel_requested', 'cleanup_status':'verified',
                    'release_confirmed':False, 'replay_allowed':False}) as cancel:
                    for index in range(2):
                        alias='field'+str(index)
                        observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                        minted=metadata(await server.call_tool('interface_guarded_mint',{
                            'alias':alias,'source_sequence':observed['source']['sequence'],
                            'point':[30,30],'region_size':[12,12]}))
                        self.assertEqual(minted.get('status'),'minted',minted)
                        action=metadata(await server.call_tool('interface_guarded_input',{
                            'alias':alias,'offset':minted['offset'],'interaction':'keyboard',
                            'observe_after':False,'wait_for_result_ms':0,
                            'tail':[{'op':'wait_update','timeout_ms':700},
                                    {'op':'key_chord','keys':['a']}]}))
                        self.assertEqual(action['status'],'pending',action)
                        receipt=metadata(await server.call_tool('interface_guarded_cancel',{'call_id':action['call_id']}))
                        self.assertEqual(receipt['status'],'unknown',receipt)
                        operation_ids.append(receipt['operation_id'])
                        end=time.monotonic()+3
                        while time.monotonic()<end:
                            row=metadata(await server.call_tool('interface_results',{'call_id':action['call_id']}))
                            if row['status']!='pending':break
                            await asyncio.sleep(.02)
                        self.assertNotEqual(row['status'],'pending',row)
                    self.assertEqual(cancel.call_count,2)
                    self.assertNotEqual(*operation_ids)
                    self.assertEqual([c.kwargs['operation_id'] for c in cancel.call_args_list],operation_ids)
                    self.assertIsNone(owner._process.poll())
            finally:
                try:
                    if server is not None: await asyncio.wait_for(server.call_tool('interface_close',{}),5)
                finally:
                    try:
                        if app is not None: app.close()
                    except ConnectionClosedError: pass
                    finally:
                        closed=owner.close(timeout_s=3)
                        self.assertEqual(closed['status'],'retired',closed)

    async def test_cancel_stopped_display_retains_unknown_and_retires_owned_display(self):
        from Xlib import X, XK, display
        from Xlib.error import ConnectionClosedError
        from runtime.cli_v1.mcp_server import create_server
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner

        def metadata(result):
            return json.loads(result.content[0].text)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            owner = PrivateDisplayOwner(root / 'display')
            app = server = None
            fresh_owner = fresh_app = fresh_server = fresh_target = fresh_pidfd = None
            cleanup_pidfd = None
            async def cleanup_fresh():
                errors = []
                try:
                    if fresh_target is not None:
                        (root/'fresh-target'/'target-stop').touch()
                        try: fresh_target.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            fresh_target.kill(); fresh_target.wait(timeout=3)
                        if fresh_target.returncode != 0:
                            errors.append('fresh target did not exit cleanly')
                except Exception as error:
                    errors.append('fresh target: '+repr(error))
                try:
                    if fresh_owner is not None:
                        fresh_cleanup=fresh_owner.close(timeout_s=3)
                        if fresh_cleanup.get('status')!='retired':
                            errors.append('fresh display close: '+repr(fresh_cleanup))
                except Exception as error:
                    errors.append('fresh display close: '+repr(error))
                try:
                    if (fresh_owner is not None and fresh_owner._process is not None
                            and fresh_owner._process.poll() is None and fresh_pidfd is not None):
                        try: signal.pidfd_send_signal(fresh_pidfd, signal.SIGKILL)
                        except ProcessLookupError: pass
                        try: fresh_owner._process.wait(timeout=3)
                        except subprocess.TimeoutExpired: pass
                except Exception as error:
                    errors.append('fresh display fallback: '+repr(error))
                finally:
                    if fresh_pidfd is not None: os.close(fresh_pidfd)
                if (fresh_owner is not None and fresh_owner._process is not None
                        and fresh_owner._process.poll() is None):
                    errors.append('fresh display alive; client close skipped')
                else:
                    try:
                        if fresh_server is not None:
                            await asyncio.wait_for(fresh_server.call_tool('interface_close',{}),5)
                    except Exception as error:
                        errors.append('fresh server close: '+repr(error))
                    finally:
                        try:
                            if fresh_app is not None: fresh_app.close()
                        except ConnectionClosedError: pass
                        except Exception as error: errors.append('fresh app close: '+repr(error))
                self.assertEqual(errors,[])
            try:
                session = owner.start(timeout_s=5)
                cleanup_pidfd = os.dup(owner._pidfd)
                with patch.dict(os.environ, {'XAUTHORITY': str(session.authority)}):
                    app = display.Display(session.display)
                win = app.screen().root.create_window(10, 10, 200, 120, 0,
                    app.screen().root_depth, X.InputOutput, X.CopyFromParent,
                    event_mask=X.KeyPressMask | X.KeyReleaseMask)
                win.map(); win.set_input_focus(X.RevertToParent, X.CurrentTime); app.sync()
                gc = win.create_gc(foreground=app.screen().white_pixel)
                win.fill_rectangle(gc, 16, 16, 8, 8); app.sync()
                server = create_server({'app':win.id}, root/'mcp', display_name=session.display,
                    session_mode='guarded-x11', guarded_owned_process=True,
                    guarded_process_identity=True, guarded_query_worker=True,
                    guarded_prestarted_cancel_supervisor=True,
                    _guarded_display_owner=owner, _guarded_xauthority=str(session.authority),
                    _guarded_cancel_transaction_timeout_s=7,
                    _guarded_recovery_retirement_reserve_ns=2_000_000_000)
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                minted = metadata(await server.call_tool('interface_guarded_mint', {
                    'alias':'field', 'source_sequence':observed['source']['sequence'],
                    'point':[30,30], 'region_size':[12,12]}))
                self.assertEqual(minted.get('status'), 'minted', minted)
                action = metadata(await server.call_tool('interface_guarded_input', {
                    'alias':'field', 'offset':minted['offset'], 'interaction':'keyboard',
                    'observe_after':False, 'wait_for_result_ms':0,
                    'tail':[{'op':'key_state','key':'a','down':True},
                            {'op':'wait_update','timeout_ms':5000},
                            {'op':'key_state','key':'a','down':False}]}))
                self.assertEqual(action['status'], 'pending', action)
                code = app.keysym_to_keycode(XK.string_to_keysym('a'))
                end = time.monotonic()+3; pressed = False
                while time.monotonic()<end:
                    bits = app.query_keymap()
                    while app.pending_events():
                        ev = app.next_event()
                        if ev.type == X.KeyPress and ev.detail == code: pressed = True
                    if pressed and bits[code//8] & (1 << (code%8)): break
                    await asyncio.sleep(.01)
                self.assertTrue(pressed and bits[code//8] & (1 << (code%8)))
                signal.pidfd_send_signal(owner._pidfd, signal.SIGSTOP)
                end = time.monotonic()+2; state = ''
                while time.monotonic()<end:
                    state = next(x for x in Path('/proc',str(owner._process.pid),'status').read_text().splitlines() if x.startswith('State:'))
                    if state.split()[1] in ('T','t'): break
                    await asyncio.sleep(.01)
                self.assertIn(state.split()[1], ('T','t'))
                cancel_started_ns = time.monotonic_ns()
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {'call_id':action['call_id']}))
                operation_id = cancel['operation_id']
                end = time.monotonic()+9; terminal = None
                while time.monotonic()<end:
                    row = metadata(await server.call_tool('interface_results', {'call_id':action['call_id']}))
                    terminal = row.get('cancellation')
                    if terminal and terminal['status'] != 'pending': break
                    await asyncio.sleep(.02)
                evidence_dir = os.environ.get('AGENT_INTERFACE_MCP_RECOVERY_TEST_OUTPUT')
                if evidence_dir:
                    evidence = {'old_press_observed':bool(pressed),
                        'old_key_down':bool(bits[code//8] & (1 << (code%8))),
                        'old_display_state':state, 'display_pid':owner._process.pid,
                        'initial_action':action, 'cancel_response':cancel,
                        'last_results':row, 'cancellation_terminal':terminal,
                        'terminal_elapsed_ms':(time.monotonic_ns()-cancel_started_ns)/1e6}
                    Path(evidence_dir, 'mcp-recovery-result.json').write_text(
                        json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
                self.assertEqual(terminal['status'], 'completed', terminal)
                self.assertEqual(terminal['operation_id'], operation_id)
                result = terminal['result']
                self.assertEqual(result['status'], 'unknown')
                self.assertTrue(result['fresh_display_allowed'], result)
                self.assertEqual(result['display_retirement']['status'], 'retired')
                self.assertTrue(result['cancellation']['owner_process_retired'])
                self.assertFalse(result['release_confirmed'])
                self.assertFalse(result['replay_allowed'])
                self.assertIsNone(result['task_success'])
                archived = json.loads((root/'mcp'/action['call_id']/'cancellation.json').read_text())
                self.assertEqual(archived['operation_id'], operation_id)
                self.assertEqual(archived['result'], result)
                # Only after retirement authorizes it, start a separate display,
                # target process and MCP server; never replay the old action.
                fresh_owner = PrivateDisplayOwner(root/'fresh-display')
                fresh_session = fresh_owner.start(timeout_s=5)
                fresh_pidfd = os.dup(fresh_owner._pidfd)
                fresh_dir = root/'fresh-target'; fresh_dir.mkdir()
                env = dict(os.environ, DISPLAY=fresh_session.display,
                           XAUTHORITY=str(fresh_session.authority), TARGET_OUT=str(fresh_dir))
                fresh_target = subprocess.Popen([sys.executable, '-B',
                    str(Path(__file__).with_name('mcp_recovery_test_target.py'))], env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                end = time.monotonic()+5
                while not (fresh_dir/'target-ready.json').exists() and time.monotonic()<end:
                    if fresh_target.poll() is not None: break
                    await asyncio.sleep(.01)
                self.assertTrue((fresh_dir/'target-ready.json').exists())
                target_info = json.loads((fresh_dir/'target-ready.json').read_text())
                initial = json.loads((fresh_dir/'target-state.json').read_text())
                with patch.dict(os.environ, {'XAUTHORITY':str(fresh_session.authority)}):
                    fresh_app = display.Display(fresh_session.display)
                fresh_window = fresh_app.create_resource_object('window',target_info['xid'])
                fresh_window.set_input_focus(X.RevertToParent,X.CurrentTime); fresh_app.sync()
                fresh_server = create_server({'app':target_info['xid']}, root/'fresh-mcp',
                    display_name=fresh_session.display, session_mode='guarded-x11',
                    guarded_owned_process=True, guarded_process_identity=True,
                    guarded_query_worker=True, guarded_prestarted_cancel_supervisor=True,
                    _guarded_display_owner=fresh_owner, _guarded_xauthority=str(fresh_session.authority))
                fresh_observed = metadata(await fresh_server.call_tool('interface_guarded_observe',{}))
                fresh_minted = metadata(await fresh_server.call_tool('interface_guarded_mint',{
                    'alias':'fresh','source_sequence':fresh_observed['source']['sequence'],
                    'point':[30,30],'region_size':[12,12]}))
                self.assertEqual(fresh_minted.get('status'),'minted',fresh_minted)
                fresh_action = metadata(await fresh_server.call_tool('interface_guarded_input',{
                    'alias':'fresh','offset':fresh_minted['offset'],'interaction':'keyboard',
                    'observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]}))
                end = time.monotonic()+3; events=[]
                while time.monotonic()<end:
                    if (fresh_dir/'target-events.json').exists():
                        events=json.loads((fresh_dir/'target-events.json').read_text())
                    if any(e['type']=='release' and e['key']=='a' for e in events): break
                    await asyncio.sleep(.01)
                final=json.loads((fresh_dir/'target-state.json').read_text())
                fresh_code=fresh_app.keysym_to_keycode(XK.string_to_keysym('a'))
                fresh_bits=fresh_app.query_keymap()
                key_up=not bool(fresh_bits[fresh_code//8] & (1 << (fresh_code%8)))
                fresh_close=metadata(await fresh_server.call_tool('interface_close',{}))
                if evidence_dir:
                    evidence.update(fresh_display_pid=fresh_owner._process.pid,
                        fresh_target=target_info, fresh_initial=initial, fresh_final=final,
                        fresh_action=fresh_action, fresh_events=events, fresh_key_up=key_up,
                        fresh_close=fresh_close)
                    Path(evidence_dir,'mcp-recovery-result.json').write_text(
                        json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
                self.assertEqual(fresh_action.get('status'),'completed',fresh_action)
                self.assertEqual(initial,{'count':0}); self.assertEqual(final,{'count':1})
                self.assertTrue(any(e['type']=='press' and e['key']=='a' for e in events))
                self.assertTrue(any(e['type']=='release' and e['key']=='a' for e in events))
                self.assertTrue(key_up)
                self.assertTrue(fresh_close.get('verified'),fresh_close)
            finally:
                try:
                    await cleanup_fresh()
                finally:
                    close_result = None
                    try:
                        close_result = owner.close(timeout_s=3)
                    finally:
                        try:
                            if owner._process is not None and owner._process.poll() is None and cleanup_pidfd is not None:
                                try: signal.pidfd_send_signal(cleanup_pidfd, signal.SIGKILL)
                                except ProcessLookupError: pass
                                try: owner._process.wait(timeout=3)
                                except subprocess.TimeoutExpired: pass
                        finally:
                            if cleanup_pidfd is not None: os.close(cleanup_pidfd)
                        if owner._process is None or owner._process.poll() is not None:
                            try:
                                if server is not None:
                                    await asyncio.wait_for(server.call_tool('interface_close', {}), 5)
                            finally:
                                if app is not None:
                                    try: app.close()
                                    except ConnectionClosedError: pass
                        else:
                            self.fail('owned display remained alive; client close skipped')
                    self.assertEqual(close_result['status'], 'retired', close_result)
