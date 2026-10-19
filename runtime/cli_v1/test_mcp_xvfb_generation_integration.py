"""Standard guarded MCP process/window identity against a private live Xvfb."""
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from Xlib import X, Xatom, XK, display
from Xlib.ext import res
from Xlib.ext import xtest
from PIL import Image, ImageStat

from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
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


def _xvfb_recovery_fault_owner_factory(targets, directory, display_name, options):
    """Inject one post-press error and one failed automatic release on real Xvfb."""
    owner = GuardedSessionOwner(targets, directory, display_name, **options)
    original_get = owner.get
    arm_path = Path(directory) / 'arm-recovery-fault'
    state = {'installed':False, 'press_flushed':False, 'cleanup_failed':False}

    def get_with_recovery_fault():
        session = original_get()
        if state['installed']:
            return session
        backend = session.backend
        original_fake_input = xtest.fake_input
        original_release_all = backend.release_all

        def fake_input(display_connection, event_type, detail=0, time=0,
                       root=0, x=0, y=0):
            result = original_fake_input(
                display_connection, event_type, detail=detail, time=time,
                root=root, x=x, y=y)
            if (arm_path.exists() and not state['press_flushed']
                    and event_type == X.KeyPress):
                display_connection.flush()
                state['press_flushed'] = True
                arm_path.unlink(missing_ok=True)
                raise OSError('injected post-press acknowledgement failure')
            return result

        def release_all_with_one_failure():
            if state['press_flushed'] and not state['cleanup_failed']:
                state['cleanup_failed'] = True
                raise OSError('injected one-shot automatic release failure')
            return original_release_all()

        xtest.fake_input = fake_input
        backend.release_all = release_all_with_one_failure
        state['installed'] = True
        return session

    owner.get = get_with_recovery_fault
    return owner


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
        recovery_effect_committed = threading.Event()
        recovery_release_seen = threading.Event()
        continuation_effect_committed = threading.Event()
        continuation_release_seen = threading.Event()
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
            window.map()
            window.set_input_focus(X.RevertToParent, X.CurrentTime)
            root.warp_pointer(x + 48, y + 48)
            # The supported observer returns a full-screen root capture. Root
            # writes beneath this opaque child did not change the captured pixels,
            # so texture the mapped child surface that covers the mint location.
            gc = window.create_gc(foreground=0xFFFFFF)
            for row in range((height + 15) // 16):
                for column in range((width + 15) // 16):
                    if (row + column) % 2 == 0:
                        window.fill_rectangle(gc, column * 16, row * 16,
                            min(16, width - column * 16),
                            min(16, height - row * 16))
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
            recovery_keycode = observer.keysym_to_keycode(XK.string_to_keysym('b'))
            continuation_keycode = observer.keysym_to_keycode(XK.string_to_keysym('c'))
            if any(type(code) is not int or code <= 0
                   for code in (recovery_keycode, continuation_keycode)):
                raise AssertionError('Xvfb has no keycode for recovery task keys')
            report['target']['keycode_a'] = keycode
            report['target']['keycode_b'] = recovery_keycode
            report['target']['keycode_c'] = continuation_keycode
            task_values = {keycode:1, recovery_keycode:2, continuation_keycode:3}
            effect_events = {recovery_keycode:recovery_effect_committed,
                             continuation_keycode:continuation_effect_committed}
            release_events = {keycode:key_release_seen,
                              recovery_keycode:recovery_release_seen,
                              continuation_keycode:continuation_release_seen}

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
                    if event.type == X.KeyPress and event.detail in task_values:
                        window.change_property(effect_atom, Xatom.CARDINAL, 32,
                                               [task_values[event.detail]])
                        app_display.sync()
                        with app_lock:
                            app_events[-1]['effect_committed_ns'] = time.monotonic_ns()
                            app_events[-1]['effect_value'] = task_values[event.detail]
                        (effect_committed if event.detail == keycode
                         else effect_events[event.detail]).set()
                    elif event.type == X.KeyRelease and event.detail in release_events:
                        release_events[event.detail].set()

            app_thread = threading.Thread(target=run_synthetic_application,
                                          name='xvfb-test-application', daemon=True)
            app_thread.start()
            server = create_server({'app':window.id}, Path(temporary.name)/'mcp',
                session_mode='guarded-x11', guarded_process_identity=True,
                guarded_query_worker=True, guarded_window_lifecycle=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_xvfb_recovery_fault_owner_factory)

            report['monotonic_ns']['observe_started'] = time.monotonic_ns()
            observation_response = await server.call_tool('interface_guarded_observe', {})
            observed = _metadata(observation_response)
            report['monotonic_ns']['observe_returned'] = time.monotonic_ns()
            report['observe'] = observed
            self.assertEqual(observed['status'], 'observed', observed)
            image_artifact = observed['observation_report']['observation']['artifact']
            image_path = Path(image_artifact['path'])
            image_bytes = image_path.read_bytes()
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            mint_box = (x + 48 - 12, y + 48 - 12,
                        x + 48 + 12, y + 48 + 12)
            patch = image.crop(mint_box)
            patch_stddev = ImageStat.Stat(patch).stddev
            report['mint_source_patch'] = {
                'image_size':list(image.size), 'box':list(mint_box),
                'patch_size':list(patch.size), 'stddev':patch_stddev,
                'minimum_required_stddev':8.0,
                'capture_artifact_sha256':image_artifact['sha256'],
                'capture_artifact_bytes':image_artifact['bytes']}
            image_output = os.environ.get('AGENT_INTERFACE_MCP_XVFB_IMAGE_RESULT')
            if image_output:
                output_path = Path(image_output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(image_path, output_path)
                report['mint_source_patch']['retained_image_sha256'] = hashlib.sha256(
                    output_path.read_bytes()).hexdigest()
            self.assertEqual(patch.size, (24, 24))
            self.assertGreaterEqual(max(patch_stddev), 8.0,
                f"selected screenshot patch is too flat: {report['mint_source_patch']}")
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

            recovery_source = _metadata(await server.call_tool(
                'interface_guarded_observe', {}))
            recovery_mint = _metadata(await server.call_tool(
                'interface_guarded_mint', {
                    'alias':'recovery_b',
                    'source_sequence':recovery_source['source']['sequence'],
                    'point':[x+48,y+48], 'region_size':[24,24]}))
            self.assertEqual(recovery_mint['status'], 'minted', recovery_mint)
            recovery_fault_arm = Path(temporary.name)/'mcp'/'arm-recovery-fault'
            recovery_fault_arm.parent.mkdir(parents=True, exist_ok=True)
            recovery_fault_arm.write_text('arm once', encoding='ascii')
            report['monotonic_ns']['recovery_fault_input_started'] = time.monotonic_ns()
            recovery_fault = _metadata(await asyncio.wait_for(server.call_tool(
                'interface_guarded_input', {
                    'alias':'recovery_b', 'offset':recovery_mint['offset'],
                    'interaction':'keyboard', 'observe_after':False,
                    'tail':[{'op':'key_chord','keys':['b']}]}), timeout=5.0))
            report['monotonic_ns']['recovery_fault_input_returned'] = time.monotonic_ns()
            report['recovery_fault_input'] = recovery_fault
            self.assertNotEqual(recovery_fault.get('status'), 'completed', recovery_fault)
            self.assertTrue(recovery_fault.get('session', {}).get('recovery_required'),
                            recovery_fault)
            self.assertTrue(recovery_fault.get('session', {}).get('review_required'),
                            recovery_fault)
            failed_execution = recovery_fault.get('result', {}).get('execution')
            self.assertIsInstance(failed_execution, dict, recovery_fault)
            self.assertIn('injected post-press acknowledgement failure',
                          failed_execution.get('error', ''), recovery_fault)
            failed_releases = failed_execution.get('releases', [])
            self.assertTrue(failed_releases, recovery_fault)
            self.assertIn('injected one-shot automatic release failure',
                          failed_releases[-1].get('error', ''), recovery_fault)
            self.assertEqual(recovery_fault['session']['owner_input_obligations']['keys'].get('b'),
                             recovery_keycode, recovery_fault)
            report['injected_fault_evidence'] = {
                'post_press_error':failed_execution.get('error'),
                'automatic_release_error':failed_releases[-1].get('error'),
                'retained_key_obligation':recovery_fault['session'][
                    'owner_input_obligations']['keys'].get('b')}
            self.assertTrue(recovery_effect_committed.wait(2.0),
                            'synthetic app did not independently observe recovery press')
            keymap = observer.query_keymap()
            report['held_before_recovery'] = {
                'keycode_b_down':bool(keymap[recovery_keycode//8]
                                      & (1 << (recovery_keycode%8))),
                'reader_connection':'independent X client'}
            self.assertTrue(report['held_before_recovery']['keycode_b_down'], report)
            effect = observer.create_resource_object('window', window.id).get_full_property(
                effect_atom, X.AnyPropertyType)
            report['effect_before_recovery'] = {
                'value':list(effect.value) if effect is not None else None,
                'reader_connection':'independent X client'}
            self.assertEqual(report['effect_before_recovery']['value'], [2], report)
            with app_lock:
                recovery_key_events = [event for event in app_events
                    if event.get('type') in (X.KeyPress, X.KeyRelease)
                    and event.get('detail') == recovery_keycode]
            self.assertEqual([event['type'] for event in recovery_key_events],
                             [X.KeyPress], recovery_key_events)
            recovery_effect_event = next(event for event in recovery_key_events
                if event['type'] == X.KeyPress)
            recovery_effect_latency_ms = (
                recovery_effect_event['effect_committed_ns']
                - report['monotonic_ns']['recovery_fault_input_started']) / 1_000_000
            self.assertGreaterEqual(recovery_effect_latency_ms, 0.0, report)
            report['recovery_app_effect_before_release'] = {
                'observed_key_events':recovery_key_events,
                'property_value':[2],
                'reader':'independent synthetic application event loop',
                'call_start_to_effect_commit_ms':recovery_effect_latency_ms}

            current_revision = recovery_fault['session']['binding_revision']
            report['monotonic_ns']['recovery_started'] = time.monotonic_ns()
            recovered = _metadata(await asyncio.wait_for(server.call_tool(
                'interface_guarded_recover_input', {
                    'current_binding_revision':current_revision}), timeout=3.0))
            report['monotonic_ns']['recovery_returned'] = time.monotonic_ns()
            self.assertEqual(recovered.get('status'), 'input_recovered', recovered)
            self.assertEqual(recovered.get('recovery_required'), False, recovered)
            self.assertTrue(recovered.get('release', {}).get('verified'), recovered)
            self.assertIsNone(recovered.get('task_success'), recovered)
            self.assertFalse(recovered.get('replay_allowed'), recovered)
            self.assertTrue(recovery_release_seen.wait(2.0),
                            'synthetic app did not observe the recovery KeyRelease')
            with app_lock:
                recovered_key_events = [event for event in app_events
                    if event.get('type') in (X.KeyPress, X.KeyRelease)
                    and event.get('detail') == recovery_keycode]
            self.assertEqual([event['type'] for event in recovered_key_events],
                             [X.KeyPress, X.KeyRelease], recovered_key_events)
            report['recovery_app_effect'] = {
                'observed_key_events':recovered_key_events,
                'property_value':[2],
                'reader':'independent synthetic application event loop',
                'call_start_to_effect_commit_ms':recovery_effect_latency_ms}
            keymap = observer.query_keymap()
            report['independent_recovery_readback'] = {
                'keycode_b_down':bool(keymap[recovery_keycode//8]
                                      & (1 << (recovery_keycode%8))),
                'reader_connection':'independent X client'}
            report['monotonic_ns']['recovery_independent_readback'] = time.monotonic_ns()
            self.assertFalse(report['independent_recovery_readback']['keycode_b_down'], report)
            recovery_elapsed_ms = (
                report['monotonic_ns']['recovery_independent_readback']
                - report['monotonic_ns']['recovery_started'])/1_000_000
            report['recovery_elapsed_ms'] = recovery_elapsed_ms
            self.assertLess(recovery_elapsed_ms, 3000.0, report)
            report['recovery'] = {
                'result':recovered, 'release_observed_by_synthetic_app':True,
                'release_read_by_independent_x_client':True,
                'task_success_api':recovered.get('task_success'),
                'replay_allowed':recovered.get('replay_allowed')}

            reviewed = _metadata(await server.call_tool(
                'interface_guarded_review_window', {'window_id':window.id}))
            self.assertEqual(reviewed.get('status'), 'reviewed', reviewed)
            report['recovery_review'] = {
                'status':reviewed.get('status'),
                'binding_revision':reviewed.get('session', {}).get('binding_revision'),
                'source_sequence':reviewed.get('source', {}).get('sequence')}
            stale_after_recovery = _metadata(await server.call_tool(
                'interface_guarded_input', {
                    'alias':'recovery_b', 'offset':recovery_mint['offset'],
                    'interaction':'keyboard', 'observe_after':False,
                    'tail':[{'op':'key_chord','keys':['b']}]}))
            report['stale_alias_after_recovery'] = stale_after_recovery
            self.assertEqual(stale_after_recovery.get('status'), 'refused',
                             stale_after_recovery)
            self.assertFalse(stale_after_recovery.get('result', {}).get(
                'input_dispatched', True), stale_after_recovery)

            fresh_mint = _metadata(await server.call_tool('interface_guarded_mint', {
                'alias':'post_recovery_c',
                'source_sequence':reviewed['source']['sequence'],
                'point':[x+48,y+48], 'region_size':[24,24]}))
            self.assertEqual(fresh_mint.get('status'), 'minted', fresh_mint)
            report['monotonic_ns']['post_recovery_input_started'] = time.monotonic_ns()
            post_recovery = _metadata(await asyncio.wait_for(server.call_tool(
                'interface_guarded_input', {
                    'alias':'post_recovery_c', 'offset':fresh_mint['offset'],
                    'interaction':'keyboard', 'observe_after':False,
                    'tail':[{'op':'key_chord','keys':['c']}]}), timeout=5.0))
            report['monotonic_ns']['post_recovery_input_returned'] = time.monotonic_ns()
            self.assertEqual(post_recovery.get('status'), 'completed', post_recovery)
            post_recovery_release = post_recovery['result']['execution']['releases'][-1]
            self.assertTrue(post_recovery_release.get('verified'), post_recovery_release)
            self.assertTrue(continuation_effect_committed.wait(2.0),
                            'synthetic app did not observe post-recovery action')
            self.assertTrue(continuation_release_seen.wait(2.0),
                            'synthetic app did not observe post-recovery release')
            effect = observer.create_resource_object('window', window.id).get_full_property(
                effect_atom, X.AnyPropertyType)
            report['post_recovery_task_oracle'] = {
                'expected_property_value':[3],
                'observed_property_value':list(effect.value) if effect is not None else None,
                'reader_connection':'independent X client',
                'key_press_then_release':True,
                'runtime_task_success_api':post_recovery.get('task_success')}
            self.assertEqual(report['post_recovery_task_oracle']['observed_property_value'],
                             [3], report)
            self.assertIsNone(report['post_recovery_task_oracle']['runtime_task_success_api'])
            with app_lock:
                continuation_key_events = [event for event in app_events
                    if event.get('type') in (X.KeyPress, X.KeyRelease)
                    and event.get('detail') == continuation_keycode]
            self.assertEqual([event['type'] for event in continuation_key_events],
                             [X.KeyPress, X.KeyRelease], continuation_key_events)
            continuation_effect_event = next(event for event in continuation_key_events
                if event['type'] == X.KeyPress)
            continuation_effect_latency_ms = (
                continuation_effect_event['effect_committed_ns']
                - report['monotonic_ns']['post_recovery_input_started']) / 1_000_000
            self.assertGreaterEqual(continuation_effect_latency_ms, 0.0, report)
            report['post_recovery_task_oracle'].update(
                observed_key_events=continuation_key_events,
                call_start_to_effect_commit_ms=continuation_effect_latency_ms)

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
            report['status'] = 'PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY'
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
