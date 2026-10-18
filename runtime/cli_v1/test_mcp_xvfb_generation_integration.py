"""Standard guarded MCP process/window identity against a private live Xvfb."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from Xlib import X, Xatom, XK, display
from Xlib.ext import res

from runtime.cli_v1.mcp_server import create_server


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


@unittest.skipUnless(sys.platform == 'linux'
    and os.environ.get('AGENT_INTERFACE_MCP_XVFB_TEST') == '1',
    'requires the explicitly enabled private Linux Xvfb integration job')
class StandardCallerXvfbGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_and_window_generation_flow_through_standard_mcp(self):
        report = {'schema':'agent-interface/standard-mcp-xvfb-generation-v1',
                  'status':'RUNNING', 'conditions':{
                      'session_mode':'guarded-x11', 'process_identity':True,
                      'query_worker':True, 'window_lifecycle':True,
                      'owned_process':True, 'task_model':'synthetic app toggles X property on a KeyPress',
                  }, 'xvfb':_xvfb_provenance(), 'monotonic_ns':{}}
        app_display = observer = None
        server = None
        server_closed = False
        app_thread = None
        app_stop = threading.Event()
        effect_committed = threading.Event()
        key_release_seen = threading.Event()
        app_events = []
        app_lock = threading.Lock()
        temporary = tempfile.TemporaryDirectory()
        try:
            app_display = display.Display()
            screen = app_display.screen()
            root = screen.root
            x, y, width, height = 40, 40, 240, 180
            window = root.create_window(
                x, y, width, height, 0, X.CopyFromParent, X.InputOutput,
                X.CopyFromParent, background_pixel=0,
                event_mask=(X.KeyPressMask | X.KeyReleaseMask | X.StructureNotifyMask))
            effect_atom = app_display.intern_atom('AI_RUNTIME_XVFB_EFFECT')
            window.change_property(effect_atom, Xatom.CARDINAL, 32, [0])
            gc = window.create_gc(foreground=0xFFFFFF)
            for row in range(8):
                for column in range(8):
                    if (row + column) % 2 == 0:
                        window.fill_rectangle(gc, 32 + column * 4,
                                              32 + row * 4, 4, 4)
            window.map()
            window.set_input_focus(X.RevertToParent, X.CurrentTime)
            root.warp_pointer(x + 48, y + 48)
            app_display.sync()

            observer = display.Display()
            xres_version = observer.res_query_version()
            pid_reply = observer.res_query_client_ids([
                {'client':window.id, 'mask':res.LocalClientPIDMask}])
            if len(pid_reply.ids) != 1 or len(pid_reply.ids[0].value) != 1:
                raise AssertionError('XRes did not return one target owner PID')
            target_pid = pid_reply.ids[0].value[0]
            if target_pid != os.getpid():
                raise AssertionError('target PID namespace did not match test process')
            stat = Path('/proc', str(target_pid), 'stat').read_text(encoding='ascii')
            closing = stat.rfind(')')
            start_ticks = int(stat[closing + 1:].split()[19])
            expected_process_digest = hashlib.sha256(json.dumps({
                'scheme':'xres-linux-process-v1', 'xid':window.id,
                'pid':target_pid, 'start_ticks':start_ticks}, sort_keys=True,
                separators=(',', ':')).encode('ascii')).hexdigest()
            report.update(server={'vendor':observer.display.info.vendor,
                'release':observer.display.info.release_number,
                'xres_version':[xres_version.server_major,xres_version.server_minor]},
                target={'xid':window.id, 'creator_pid':os.getpid(),
                        'xres_pid':target_pid, 'start_ticks':start_ticks,
                        'expected_process_generation':expected_process_digest,
                        'window_geometry':[x,y,width,height]})
            keycode = observer.keysym_to_keycode(XK.string_to_keysym('a'))
            if type(keycode) is not int or keycode <= 0:
                raise AssertionError('Xvfb has no keycode for lowercase a')
            report['target']['keycode_a'] = keycode

            def run_synthetic_application():
                while not app_stop.is_set():
                    if not app_display.pending_events():
                        time.sleep(0.002)
                        continue
                    event = app_display.next_event()
                    now = time.monotonic_ns()
                    with app_lock:
                        app_events.append({'type':event.type,
                                           'detail':getattr(event,'detail',None),
                                           'monotonic_ns':now})
                    if event.type == X.KeyPress and event.detail == keycode:
                        window.change_property(effect_atom, Xatom.CARDINAL, 32, [1])
                        app_display.sync()
                        with app_lock:
                            app_events[-1]['effect_committed_ns'] = time.monotonic_ns()
                        effect_committed.set()
                    elif event.type == X.KeyRelease and event.detail == keycode:
                        key_release_seen.set()

            app_thread = threading.Thread(target=run_synthetic_application,
                                          name='xvfb-test-application', daemon=True)
            app_thread.start()
            server = create_server({'app':window.id}, Path(temporary.name)/'mcp',
                session_mode='guarded-x11', guarded_process_identity=True,
                guarded_query_worker=True, guarded_window_lifecycle=True,
                guarded_owned_process=True)

            report['monotonic_ns']['observe_started'] = time.monotonic_ns()
            observed = _metadata(await server.call_tool('interface_guarded_observe', {}))
            report['monotonic_ns']['observe_returned'] = time.monotonic_ns()
            report['observe'] = observed
            self.assertEqual(observed['status'], 'observed', observed)
            source = observed['source']
            binding = source['pointer_binding']
            self.assertEqual(binding['process_generation'], expected_process_digest)
            self.assertRegex(binding['window_generation'], r'^[0-9a-f]{64}$')
            self.assertEqual(observed['session']['process_identity'], True)
            self.assertEqual(observed['session']['query_worker'], True)
            self.assertEqual(observed['session']['window_lifecycle'], True)

            report['monotonic_ns']['mint_started'] = time.monotonic_ns()
            minted = _metadata(await server.call_tool('interface_guarded_mint', {
                'alias':'field', 'source_sequence':source['sequence'],
                'point':[x+48,y+48], 'region_size':[24,24]}))
            report['monotonic_ns']['mint_returned'] = time.monotonic_ns()
            report['mint'] = minted
            self.assertEqual(minted['status'], 'minted', minted)

            report['monotonic_ns']['input_started'] = time.monotonic_ns()
            input_result = _metadata(await server.call_tool('interface_guarded_input', {
                'alias':'field', 'offset':minted['offset'], 'interaction':'keyboard',
                'observe_after':False, 'tail':[{'op':'key_chord','keys':['a']}]}))
            report['monotonic_ns']['input_returned'] = time.monotonic_ns()
            report['input'] = input_result
            self.assertEqual(input_result['status'], 'completed', input_result)
            release_rows = input_result['result']['execution']['releases']
            report['runtime_release_receipts'] = release_rows
            self.assertTrue(release_rows)
            self.assertTrue(release_rows[-1]['verified'], release_rows[-1])
            self.assertEqual(release_rows[-1]['keys_down'], [])
            self.assertEqual(release_rows[-1]['buttons_down'], [])
            self.assertTrue(effect_committed.wait(2.0), 'synthetic app saw no keypress')
            self.assertTrue(key_release_seen.wait(2.0), 'synthetic app saw no key release')
            with app_lock:
                key_events = [event for event in app_events
                              if event.get('type') in (X.KeyPress, X.KeyRelease)
                              and event.get('detail') == keycode]
            self.assertEqual([event['type'] for event in key_events],
                             [X.KeyPress, X.KeyRelease], key_events)
            report['synthetic_app_key_events'] = key_events

            report['monotonic_ns']['effect_read_started'] = time.monotonic_ns()
            effect = observer.create_resource_object('window', window.id).get_full_property(
                effect_atom, X.AnyPropertyType)
            report['monotonic_ns']['effect_read_returned'] = time.monotonic_ns()
            report['independent_effect'] = {
                'property_type':getattr(effect,'property_type',None),
                'format':getattr(effect,'format',None),
                'value':list(effect.value) if effect is not None else None,
                'reader_connection':'independent X client'}
            self.assertIsNotNone(effect)
            self.assertEqual(list(effect.value), [1])
            keymap = observer.query_keymap()
            report['independent_release_readback'] = {
                'keycode_a_down':bool(keymap[keycode//8] & (1 << (keycode%8))),
                'reader_connection':'independent X client'}
            self.assertFalse(report['independent_release_readback']['keycode_a_down'])

            old_lifecycle = binding['window_generation']
            observed_again = _metadata(await server.call_tool('interface_guarded_observe', {}))
            second_source = observed_again['source']
            second_mint = _metadata(await server.call_tool('interface_guarded_mint', {
                'alias':'stale', 'source_sequence':second_source['sequence'],
                'point':[x+48,y+48], 'region_size':[24,24]}))
            self.assertEqual(second_mint['status'], 'minted', second_mint)
            observer.create_resource_object('window', window.id).destroy()
            observer.sync()
            report['monotonic_ns']['stale_input_started'] = time.monotonic_ns()
            stale = _metadata(await server.call_tool('interface_guarded_input', {
                'alias':'stale', 'offset':second_mint['offset'],
                'interaction':'keyboard', 'observe_after':False,
                'tail':[{'op':'key_chord','keys':['a']}]}))
            report['monotonic_ns']['stale_input_returned'] = time.monotonic_ns()
            report['stale_generation'] = {
                'prior_window_generation':old_lifecycle,
                'destroyed_window_id':window.id, 'result':stale,
                'target_queries_retired':stale.get('session',{}).get(
                    'target_queries',{}).get('retired'),
                'review_required':stale.get('session',{}).get('review_required')}
            self.assertEqual(stale['status'], 'refused', stale)
            self.assertEqual(stale.get('result',{}).get('input_dispatched'), False)
            self.assertTrue(report['stale_generation']['target_queries_retired'])
            self.assertTrue(report['stale_generation']['review_required'])
            report['close'] = _metadata(await server.call_tool('interface_close', {}))
            self.assertEqual(report['close']['status'], 'closed', report['close'])
            server_closed = True
            report['status'] = 'PASS_SCOPED_XVFB_STANDARD_CALLER'
        except BaseException as error:
            report.update(status='FAIL', error_type=type(error).__name__,
                          error=str(error))
            raise
        finally:
            app_stop.set()
            if app_thread is not None:
                app_thread.join(1.0)
            if server is not None and not server_closed:
                try:
                    report['close'] = _metadata(await server.call_tool('interface_close', {}))
                except BaseException as error:
                    report['close_error'] = repr(error)
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
            with app_lock:
                report['synthetic_app_events'] = list(app_events)
            report['monotonic_ns']['finished'] = time.monotonic_ns()
            result_path = os.environ.get('AGENT_INTERFACE_MCP_XVFB_RESULT')
            if result_path:
                path = Path(result_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n',
                                encoding='utf-8')
            temporary.cleanup()


if __name__ == '__main__':
    unittest.main()
