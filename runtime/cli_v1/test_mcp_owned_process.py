"""Standard MCP composition over one explicitly owned guarded-X11 process."""
import asyncio
import hashlib
import io
import threading
from unittest.mock import Mock, patch
import json
import multiprocessing
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from PIL import Image

from Xlib import X

from runtime.cli_v1.mcp_server import create_server, main
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.backends.x11_v1.backend import X11Backend
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata
from runtime.guarded_x11_v1.process_identity import (
    process_generation_from_identity,process_incarnation_from_identity)

_CALC_TEST_PID=4321
_CALC_TEST_START_TICKS=98765
_CALC_TEST_PROCESS_GENERATION=process_generation_from_identity(
    20,_CALC_TEST_PID,_CALC_TEST_START_TICKS)
_CALC_TEST_PROCESS_INCARNATION=process_incarnation_from_identity(
    _CALC_TEST_PID,_CALC_TEST_START_TICKS)
_CALC_TASK_FODS=(b'<?xml version="1.0"?><office:document-content '
    b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    b'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">'
    b'<office:body><office:spreadsheet><table:table table:name="Sheet1">'
    b'<table:table-row><table:table-cell office:value-type="float" office:value="731"/>'
    b'</table:table-row><table:table-row>'
    b'<table:table-cell office:value-type="float" office:value="864"/>'
    b'</table:table-row></table:table></office:spreadsheet></office:body>'
    b'</office:document-content>')


def _blocked_release_worker(_send_connection):
    while True:
        time.sleep(0.01)


def _delayed_release_worker(send_connection):
    time.sleep(0.35)
    send_connection.send({
        'status':'released',
        'release':{'verified':True, 'keys_down':[], 'buttons_down':[]},
    })


def _release_then_delayed_shutdown_worker(send_connection):
    send_connection.send({
        'status':'released',
        'release':{'verified':True, 'keys_down':[], 'buttons_down':[]},
    })
    time.sleep(0.15)


def _fake_prestarted_cancel_worker(request):
    """Independent Fake X effect log for the public supervisor composition."""
    root = Path(request['owner_data_directory'])
    _write_json(root/'cleanup-supervisor-entered.json', {
        'operation_id':request['operation_id'],
        'session_id':request['session_id'],
        'deadline_monotonic_ns':request['deadline_monotonic_ns']})
    if (root/'block-cleanup-supervisor').exists():
        while not (root/'continue-cleanup-supervisor').exists():
            time.sleep(0.01)
    state_path = root/'supervisor-fake-x.json'
    state = _read_json(state_path, {'down':[1], 'effects':[]})
    if (root/'bystander-reuse').exists():
        # Synthetic XRes identity for composed-caller refusal coverage; the
        # real XRes predicate is covered separately by test_cancel_supervisor.
        observed_pid = request['owner_pid'] + 100000
        disconnect = {
            'status':'unknown',
            'reason':'resource_base_reused_by_unrelated_client',
            'expected_pid':request['owner_pid'],
            'observed_pid':observed_pid,
            'observer_pid':os.getpid(),
            'resource_base':request['x_resource_base'],
        }
        release = {'status':'not_attempted',
                   'reason':'stale_owner_identity'}
        receipt = {
            'status':'unknown', 'reason':'stale_owner_identity',
            'operation_id':request['operation_id'],
            'session_id':request['session_id'],
            'owner_client_disconnect':disconnect,
            'owner_release_attempt':release,
            'release_confirmed':False, 'cleanup_status':'UNKNOWN',
            'task_success':None, 'replay_allowed':False,
        }
        state.setdefault('refused', []).append(receipt)
        _write_json(state_path, state)
        return receipt
    stale = (root/'stale-cleanup-supervisor-generation').exists()
    expired = time.monotonic_ns() >= request['deadline_monotonic_ns']
    if stale or expired:
        reason = 'stale_generation' if stale else 'expired_deadline'
        receipt = {'status':'unknown', 'reason':reason,
                   'operation_id':request['operation_id'],
                   'session_id':request['session_id'],
                   'release_confirmed':False, 'task_success':None,
                   'replay_allowed':False,
                   'owner_client_disconnect':{'status':'unknown','reason':reason},
                   'owner_release_attempt':{'status':'not_attempted','reason':reason}}
        state.setdefault('refused', []).append(receipt)
        _write_json(state_path, state)
        return receipt
    state['down'] = [code for code in state.get('down', [])
                     if code not in request.get('keys', {}).values()]
    effect = {'kind':'KeyRelease', 'operation_id':request['operation_id'],
              'session_id':request['session_id'],
              'binding_revision':request['binding_revision'],
              'accepted_monotonic_ns':time.monotonic_ns()}
    state.setdefault('effects', []).append(effect)
    _write_json(state_path, state)
    return {'status':'completed', 'operation_id':request['operation_id'],
            'session_id':request['session_id'],
            'binding_revision':request['binding_revision'],
            'release_confirmed':False, 'task_success':None,
            'replay_allowed':False,
            'owner_client_disconnect':{'status':'disconnected',
                'resource_base':request['x_resource_base'],
                'expected_pid':request['owner_pid']},
            'owner_release_attempt':{'status':'readback_verified',
                'release':{'verified':True, 'keys_down':[],
                           'buttons_down':[],
                           'independent_fake_x_readback':True}}}


def _retain_prestarted_trial(name, terminal, state, *, response_seconds=None,
                              heartbeat_count=None,
                              duplicate_operation_reused=None):
    destination = os.environ.get('AGENT_INTERFACE_SUPERVISOR_EVIDENCE_DIR')
    if not destination:
        return
    cancellation = terminal.get('cancellation', {})
    result = cancellation.get('result', {})
    disconnect = result.get('owner_client_disconnect', {})
    release_attempt = result.get('owner_release_attempt', {})
    release = release_attempt.get('release', {})
    record = {
        'schema':'agent-interface/public-mcp-prestarted-supervisor-trial-v1',
        'trial':name,
        'cancel_response_seconds':response_seconds,
        'heartbeat_count':heartbeat_count,
        'duplicate_operation_reused':duplicate_operation_reused,
        'cancellation':{
            'status':cancellation.get('status'),
            'operation_id_present':bool(cancellation.get('operation_id')),
            'transaction_deadline_monotonic_ns':cancellation.get(
                'transaction_deadline_monotonic_ns'),
            'owner_generation_fields':sorted((cancellation.get(
                'owner_generation') or {}).keys()),
            'result_status':result.get('status'),
            'cleanup_status':result.get('cleanup_status'),
            'release_confirmed':result.get('release_confirmed'),
            'task_success':result.get('task_success'),
            'replay_allowed':result.get('replay_allowed'),
            'owner_process_retired':result.get('owner_process_retired'),
            'owner_client_disconnect_status':disconnect.get('status'),
            'owner_client_disconnect_reason':disconnect.get('reason'),
            'owner_release_attempt_status':release_attempt.get('status'),
            'release_readback_verified':release.get('verified'),
            'release_keys_down':release.get('keys_down'),
            'release_buttons_down':release.get('buttons_down'),
            'supervisor_worker_retired':result.get('worker_retired'),
            'supervisor_reason':result.get('reason'),
            'completed_monotonic_ns':cancellation.get(
                'completed_monotonic_ns')},
        'independent_fake_x':{
            'keys_down':state.get('down'),
            'accepted_effect_count':len(state.get('effects', [])),
            'accepted_effect_kinds':sorted({effect.get('kind')
                for effect in state.get('effects', [])}),
            'refused_effect_count':len(state.get('refused', [])),
            'refused_reasons':sorted({row.get('reason')
                for row in state.get('refused', [])})}}
    target = Path(destination) / (name + '.json')
    target.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n',
                      encoding='utf-8')


class _Cleanup:
    def __init__(self):
        self.callbacks = []

    def addCleanup(self, callback, *args, **kwargs):
        self.callbacks.append((callback, args, kwargs))

    def doCleanups(self):
        while self.callbacks:
            callback, args, kwargs = self.callbacks.pop()
            callback(*args, **kwargs)


class _FakeQueries:
    def __init__(self, root):
        self.root = Path(root)

    def read(self, operation, xid):
        if operation == 'windows_for_process':
            if (type(xid) is not dict or set(xid) != {'pid','title_hint'}
                    or xid.get('pid') != _CALC_TEST_PID
                    or xid.get('title_hint') != 'Book1'):
                raise ValueError('unexpected synthetic process discovery request')
            process_generation_path=self.root/'fake-process-generation'
            window_incarnation_path=self.root/'fake-window-incarnation'
            process_pid_path=self.root/'fake-process-pid'
            process_start_path=self.root/'fake-process-start-ticks'
            return [{
                'schema':'agent-interface/x11-window-metadata-cues-v1',
                'xid':20,'process_pid':(int(process_pid_path.read_text(
                    encoding='ascii')) if process_pid_path.exists()
                    else _CALC_TEST_PID),
                'process_start_ticks':(int(process_start_path.read_text(
                    encoding='ascii')) if process_start_path.exists()
                    else _CALC_TEST_START_TICKS),
                'process_generation':(process_generation_path.read_text(
                    encoding='utf-8') if process_generation_path.exists()
                    else _CALC_TEST_PROCESS_GENERATION),
                'window_incarnation':(window_incarnation_path.read_text(
                    encoding='utf-8') if window_incarnation_path.exists()
                    else 'c'*64),'mapped':True,
                'focused_before':True,'focused_after':True,
                'discovery_title_hint':'Book1','discovery_title_xid':20,
                'input_authority':False,'authenticated_role':False}]
        if operation == 'process_identity':
            marker = self.root/'fake-process-generation'
            return marker.read_text(encoding='utf-8') if marker.exists() else 'a'*64
        if operation == 'focus':
            return True
        if operation == 'window_incarnation':
            if xid != 20:
                raise ValueError('unknown synthetic window')
            marker=self.root/'fake-window-incarnation'
            return marker.read_text(encoding='utf-8') if marker.exists() else 'c'*64
        if operation == 'process_incarnation':
            marker = self.root/'fake-process-incarnation'
            return marker.read_text(encoding='utf-8') if marker.exists() else (
                _CALC_TEST_PROCESS_INCARNATION if (self.root/'calc-profile-mode').exists()
                else 'b'*64)
        if operation == 'window_metadata':
            count_path=self.root/'window-metadata-query-count'
            count=int(count_path.read_text(encoding='ascii')) if count_path.exists() else 0
            count_path.write_text(str(count+1),encoding='ascii')
            if (count >= 1
                    and (self.root/'fake-window-metadata-delay-second-query').exists()):
                time.sleep(0.6)
            if xid != 20:
                raise ValueError('unknown synthetic window')
            observed=time.monotonic_ns()
            if (self.root/'fake-window-metadata-stale').exists():
                observed-=1_000_000_000
            changed=(self.root/'fake-window-metadata-changed').exists()
            changed_calc=(self.root/'fake-window-metadata-changed-calc').exists()
            process_marker=self.root/'fake-process-incarnation'
            process_pid_path=self.root/'fake-process-pid'
            process_start_path=self.root/'fake-process-start-ticks'
            process_pid=(int(process_pid_path.read_text(encoding='ascii'))
                if process_pid_path.exists() else _CALC_TEST_PID)
            process_start_ticks=(int(process_start_path.read_text(encoding='ascii'))
                if process_start_path.exists() else _CALC_TEST_START_TICKS)
            process_incarnation=(process_marker.read_text(encoding='utf-8')
                if process_marker.exists() else (
                    _CALC_TEST_PROCESS_INCARNATION
                    if (self.root/'calc-profile-mode').exists() else 'b'*64))
            if (self.root/'fake-window-metadata-change-incarnation').exists():
                process_marker.write_text('d'*64,encoding='utf-8')
            return {'schema':'agent-interface/x11-window-metadata-cues-v1',
                'query_started_monotonic_ns':observed-1_000,
                'observed_monotonic_ns':observed,
                'xid':20,'parent_xid':1,'transient_for_xid':None,
                'wm_class':['soffice','LibreOffice'],
                'title_cue':('Different Window' if changed else
                    'Book1 - Calc — updated' if changed_calc else 'Book1 - Calc'),
                'role_cue':None,'mapped':True,
                'process_incarnation':process_incarnation,
                'process_generation':((self.root/'fake-process-generation').read_text(
                    encoding='utf-8') if (self.root/'fake-process-generation').exists()
                    else _CALC_TEST_PROCESS_GENERATION
                    if (self.root/'calc-profile-mode').exists() else 'a'*64),
                'process_pid':(process_pid
                    if (self.root/'calc-profile-mode').exists() else 1234),
                'process_start_ticks':(process_start_ticks
                    if (self.root/'calc-profile-mode').exists() else 1),
                'window_incarnation':((self.root/'fake-window-incarnation').read_text(
                    encoding='utf-8') if (self.root/'fake-window-incarnation').exists()
                    else 'c'*64),'focused_before':True,
                'focused_after':True,'input_authority':False,
                'authenticated_role':False}
        raise ValueError(operation)

    def close(self):
        return None


def _fake_owner_factory(targets, directory, display_name, options):
    """Rebuild only the transport fake inside the spawned owner process."""
    cleanup = _Cleanup()
    fake = FakeX(cleanup)
    fake.backend.d.get_display_name = lambda:'fake-display'
    fake.backend.d.get_input_focus = lambda:SimpleNamespace(focus=SimpleNamespace(id=20))
    fake.backend.d.display = SimpleNamespace(
        info=SimpleNamespace(resource_id_base=0x1200000))
    root = Path(directory)
    generation_path = root/'fake-process-generation'
    if generation_path.exists():
        fake.generation = generation_path.read_text(encoding='utf-8')
    if (root/'compiled-profile-mode').exists():
        (root/'synthetic-application-initial.rgb').write_bytes(fake.raw)
    def sync():
        if (root/'block-owner-io').exists():
            (root/'owner-io-entered.json').write_text(
                json.dumps(sorted(fake.down)), encoding='utf-8')
            while not (root/'resume-owner-io').exists():
                time.sleep(0.005)
    fake.backend.d.sync = sync
    original_emit=fake.emit
    def compiled_emit(display,kind,code):
        original_emit(display,kind,code)
        if ((root/'compiled-profile-mode').exists() and kind==X.KeyPress
                and code==1):
            image=Image.frombytes('RGB',(32,32),fake.raw,'raw','BGRX')
            image.putpixel((1,1),(255,0,0))
            fake.raw=image.tobytes('raw','BGRX')
            (root/'synthetic-application-state.rgb').write_bytes(fake.raw)
            _write_json(root/'synthetic-effect-receipt.json',{
                'event':'synthetic_app_pixel_commit',
                'monotonic_ns':time.monotonic_ns(),
                'pixel':[1,1], 'rgb':[255,0,0], 'key_code':code})
            if (root/'compiled-flip-generation-after-input').exists():
                (root/'fake-process-generation').write_text('b'*64,encoding='utf-8')
    input_patcher=patch('runtime.backends.x11_v1.backend.xtest.fake_input',
                        side_effect=compiled_emit)
    input_patcher.start();cleanup.addCleanup(input_patcher.stop)
    patcher = patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries',
                    return_value=_FakeQueries(root))
    patcher.start()
    cleanup.addCleanup(patcher.stop)
    owner = GuardedSessionOwner(targets, directory, display_name, **options)
    owner._owned_process_test_cleanup = cleanup
    if (root/'calc-profile-mode').exists():
        _configure_calc_profile_fake(owner, fake, root, options.get('test_input_obligations_state'))
    if (root/'fake-target-exit-receipt').exists():
        original_calc_profile = owner.run_registered_calc_profile
        def profile_with_exact_exit_receipt(*args, **kwargs):
            report = original_calc_profile(*args, **kwargs)
            descriptor = report['task_artifact_admission']
            save_request = report['task_save_request']
            target_pid = descriptor['target_pid']
            report['target_process_exit_receipt'] = {
                'schema':'agent-interface/calc-target-exit-receipt-v2',
                'status':'exited','verified':True,
                'process_generation':descriptor['process_generation'],
                'xid':descriptor['target_xid'],'pid':target_pid,
                'start_ticks':descriptor['target_start_ticks'],
                'exit_code':0,
                'observed_monotonic_ns':max(time.monotonic_ns(),
                    save_request['save_request_monotonic_ns'] + 1),
                'custody':'libreoffice-oosplash-direct-child-v1',
                'launcher_pid':target_pid+100,
                'launcher_start_ticks':123456,
                'launcher_executable':'/usr/lib/libreoffice/program/oosplash',
                'launcher_package_version':'4:7.4.7-1+deb12u14',
                'launcher_exit_code':0,'replacement_observed':False}
            return report
        owner.run_registered_calc_profile = profile_with_exact_exit_receipt
    return owner


def _configure_calc_profile_fake(owner, fake, root, obligation_state=None):
    """Use a synthetic 1280x800 Calc-like source in the spawned owner only."""
    from runtime.guarded_x11_v1.calc_profile_v1 import CalcPrimaryProfile
    from runtime.guarded_x11_v1.bridge import NativeHandleBridge
    from runtime.guarded_x11_v1.compiled import _Adapter

    generation_path=root/'fake-process-generation'
    if not generation_path.exists():
        generation_path.write_text(_CALC_TEST_PROCESS_GENERATION,encoding='utf-8')
    fake.generation=generation_path.read_text(encoding='utf-8')
    incarnation_path=root/'fake-process-incarnation'
    if not incarnation_path.exists():
        incarnation_path.write_text(_CALC_TEST_PROCESS_INCARNATION,encoding='utf-8')

    image = Image.new('RGB', (1280, 800), 'white')
    for left, top, right, bottom in ((4,23,28,39),(35,143,90,160),(127,143,215,160),
                                    (185,190,216,221)):
        for y in range(top, bottom):
            for x in range(left, right):
                if (x + y) % 2:
                    image.putpixel((x,y), (225,225,225))
    fake.raw = image.tobytes('raw', 'BGRX')
    fake.calc_pointer = {'x':0, 'y':0, 'mask':0}
    fake.calc_state = {'entered':False, 'both_entered':False,
                       'save_requested':False, 'artifact_written_on_save':False,
                       'completed_entries':[], 'events':[], 'typed':[],
                       'task_values':json.loads((root/'calc-task-values.json').read_text(
                           encoding='utf-8')) if (root/'calc-task-values.json').exists()
                           else {'A1':'731','A2':'864'}}
    fake.backend.geometry = lambda _target:dict(x=0, y=0, width=1280, height=800)
    fake.backend.d.screen = lambda:SimpleNamespace(width_in_pixels=1280,
                                                    height_in_pixels=800)
    visual = SimpleNamespace(visual_id=1, red_mask=0xff0000,
        green_mask=0x00ff00, blue_mask=0x0000ff, visual_class=X.TrueColor)
    fake.backend.d.display.info = SimpleNamespace(resource_id_base=0x1200000,
        image_byte_order=0,
        pixmap_formats=[SimpleNamespace(depth=24,bits_per_pixel=32,scanline_pad=32)],
        roots=[SimpleNamespace(allowed_depths=[SimpleNamespace(visuals=[visual])])])
    fake.backend.root.get_image = lambda *_args:SimpleNamespace(
        data=fake.raw, depth=24, visual=1)
    fake.backend.root.query_pointer = lambda:SimpleNamespace(
        root_x=fake.calc_pointer['x'], root_y=fake.calc_pointer['y'],
        mask=fake.calc_pointer['mask'])
    keycodes = {}
    names = {}
    def keycode(name):
        if name not in keycodes:
            code = 20 + len(keycodes)
            keycodes[name] = code
            names[code] = name
        return keycodes[name]
    fake.backend._keycode = keycode
    fake.backend._keyboard_mapping_snapshot = lambda:('synthetic-calc-keymap',)
    fake.backend.keysym_to_keycode = lambda _keysym: keycode('mapped')
    fake.backend.keycode_to_keysym = lambda _code, _index: 0

    def image_with_marker(points):
        current = Image.frombytes('RGB', (1280, 800), fake.raw, 'raw', 'BGRX')
        for point, color in points:
            current.putpixel(point, color)
        fake.raw = current.tobytes('raw', 'BGRX')

    from runtime.backends.x11_v1.backend import X11Backend
    fake.backend.observe_read_only = lambda target, frame, region: X11Backend.capture(
        fake.backend, target, frame, *region)
    original_bridge_init = NativeHandleBridge.__init__
    def calc_bridge_init(bridge, *args, **kwargs):
        original_bridge_init(bridge, *args, **kwargs)
        bridge._window_title = lambda:'primary-values.xlsx — LibreOffice Calc'
        if (root/'fake-calc-record-point-resolution').exists():
            original_resolve=bridge.store.resolve_point
            def record_resolution(alias, offset, observation, image, now_ns,
                                  session_scope=None):
                result=original_resolve(alias,offset,observation,image,now_ns,
                    session_scope=session_scope)
                row={'alias':alias,'offset':offset,'observation_sequence':
                    observation.get('sequence') if isinstance(observation,dict) else None,
                    'observation_box':observation.get('box') if isinstance(observation,dict) else None,
                    'result':result}
                with (root/'calc-point-resolutions.jsonl').open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
                return result
            bridge.store.resolve_point=record_resolution
    NativeHandleBridge.__init__ = calc_bridge_init

    original_init = CalcPrimaryProfile.__init__
    def fake_ocr(command, *, input, capture_output, timeout, check):
        assert command[0] == 'test-tesseract'
        assert command[command.index('--psm') + 1] == '6'
        assert 'tessedit_char_whitelist=0123456789' in command
        assert capture_output is True and check is False and timeout > 0
        pixels = Image.open(io.BytesIO(input)).convert('RGB')
        assert pixels.size == (180, 68)
        filled = fake.calc_state['both_entered']
        header = b'level\tleft\ttop\twidth\theight\tconf\ttext\n'
        mode = (root/'calc-profile-mode').read_text(encoding='utf-8').strip()
        if mode == 'block-ocr':
            (root/'calc-ocr-entered.json').write_text(
                json.dumps({'at_ns':time.monotonic_ns(),
                            'input_bytes':len(input)}), encoding='utf-8')
            deadline = time.monotonic() + 2
            while not (root/'resume-calc-ocr').exists() and time.monotonic() < deadline:
                time.sleep(0.005)
        low_once = (mode == 'settle-after-low-confidence'
                    and fake.calc_state['both_entered']
                    and not (root/'post-release-settle-observed').exists())
        ambiguous_after_input = (mode == 'ambiguous-after-input'
                                 and fake.calc_state['both_entered'])
        task_values=fake.calc_state['task_values']
        a1=task_values['A1'].encode('ascii')
        a2=task_values['A2'].encode('ascii')
        wrong_a2=str(int(task_values['A2'])+1).encode('ascii')
        if not filled or mode == 'unknown-after-input':
            stdout=header
        elif mode == 'no-match-after-input':
            # OCR returned text inside the reviewed cell, but it cannot be
            # interpreted as the expected decimal value. This is a no-match,
            # not evidence that the task effect failed.
            stdout=(header+b'5\t8\t4\t44\t24\t95\tnoise\n')
        elif low_once:
            stdout=(header+b'5\t8\t4\t44\t24\t70\t'+a1+b'\n'
                    +b'5\t8\t38\t44\t24\t70\t'+a2+b'\n')
        else:
            if ambiguous_after_input:
                stdout=(header+b'5\t8\t4\t44\t24\t95\t'+a1+b'\n'
                        +b'5\t8\t38\t44\t24\t95\t'+a2+b'\n'
                        +b'5\t8\t38\t44\t24\t95\t'+wrong_a2+b'\n')
            else:
                second=wrong_a2 if mode == 'wrong-after-input' else a2
                stdout=(header+b'5\t8\t4\t44\t24\t95\t'+a1+b'\n'
                        +b'5\t8\t38\t44\t24\t95\t'+second+b'\n')
        evidence=(root/'fake-ocr-observations.jsonl')
        with evidence.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps({'pixels_filled':filled,'low_once':low_once,
                'output':stdout.decode('utf-8')})+'\n')
        return SimpleNamespace(returncode=0, stdout=stdout, stderr=b'')
    def init_with_fake_ocr(profile, *args, **kwargs):
        kwargs['ocr_runner'] = fake_ocr
        original_init(profile, *args, **kwargs)
    CalcPrimaryProfile.__init__ = init_with_fake_ocr
    original_settle = _Adapter._settle_after_release
    def observe_settle(adapter):
        (root/'post-release-settle-observed').write_text(
            str(time.monotonic_ns()),encoding='ascii')
        return original_settle(adapter)
    _Adapter._settle_after_release = observe_settle
    import runtime.guarded_x11_v1.calc_profile_v1 as calc_profile
    original_which = calc_profile.shutil.which
    calc_profile.shutil.which = lambda name: (
        'test-tesseract' if name == 'tesseract' else original_which(name))

    original_emit = fake.emit
    def calc_emit(display, kind, code=0, **kwargs):
        original_emit(display, kind, code)
        if kind == X.MotionNotify:
            fake.calc_pointer.update(x=kwargs.get('x', 0), y=kwargs.get('y', 0))
        elif kind in (X.ButtonPress, X.ButtonRelease):
            mask = {1:X.Button1Mask, 2:X.Button2Mask, 3:X.Button3Mask}.get(code, 0)
            if kind == X.ButtonPress:
                fake.calc_pointer['mask'] |= mask
            else:
                fake.calc_pointer['mask'] &= ~mask
        elif kind == X.KeyPress:
            name = names.get(code)
            fake.calc_state['events'].append({'kind':'KeyPress', 'key':name})
            if name in {'Return', 'ENTER'} and fake.calc_state['typed']:
                value = ''.join(fake.calc_state['typed'])
                fake.calc_state['typed'] = []
                if value == fake.calc_state['task_values']['A1'] and not fake.calc_state['entered']:
                    fake.calc_state['entered'] = True
                    fake.calc_state['completed_entries'].append(value)
                    image_with_marker([((40,145),(20,20,20))])
                elif value == fake.calc_state['task_values']['A2'] and fake.calc_state['entered']:
                    fake.calc_state['both_entered'] = True
                    fake.calc_state['completed_entries'].append(value)
                    image_with_marker([((40,162),(30,30,30))])
            elif name == 's' and fake.calc_state['entered']:
                fake.calc_state['save_requested'] = True
                if (fake.calc_state['both_entered'] and
                        (root/'fake-calc-save-writes-artifact').exists()):
                    artifacts=list(root.rglob('task-artifact.fods'))
                    if len(artifacts)==1:
                        dynamic_fods=_CALC_TASK_FODS.replace(
                            b'office:value="731"',
                            ('office:value="'+fake.calc_state['task_values']['A1']+'"').encode())
                        dynamic_fods=dynamic_fods.replace(
                            b'office:value="864"',
                            ('office:value="'+fake.calc_state['task_values']['A2']+'"').encode())
                        artifacts[0].write_bytes(dynamic_fods)
                        fake.calc_state['artifact_written_on_save']=True
                if not (root/'calc-save-frame-unchanged').exists():
                    image_with_marker([((300,300),(40,40,40))])
            elif name and len(name) == 1:
                fake.calc_state['typed'].append(name)
        elif kind == X.KeyRelease:
            fake.calc_state['events'].append({'kind':'KeyRelease', 'key':names.get(code)})
        _write_json(root/'calc-fake-state.json', {
            **fake.calc_state, 'down':sorted(fake.down),
            'pointer':dict(fake.calc_pointer)})
    fake_input = patch('runtime.backends.x11_v1.backend.xtest.fake_input',
                       side_effect=calc_emit)
    fake_input.start()
    owner._owned_process_test_cleanup.addCleanup(fake_input.stop)
    owner._owned_process_test_cleanup.addCleanup(
        lambda:setattr(CalcPrimaryProfile, '__init__', original_init))
    owner._owned_process_test_cleanup.addCleanup(
        lambda:setattr(_Adapter, '_settle_after_release', original_settle))
    owner._owned_process_test_cleanup.addCleanup(
        lambda:setattr(NativeHandleBridge, '__init__', original_bridge_init))
    owner._owned_process_test_cleanup.addCleanup(
        lambda:setattr(calc_profile.shutil, 'which', original_which))


def _read_json(path, default):
    path = Path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True), encoding='utf-8')


def _write_test_obligation_state(shared, state):
    payload = json.dumps(state, separators=(',', ':')).encode('utf-8')
    digest = hashlib.sha256(payload).digest()
    record = b'AIOL' + len(payload).to_bytes(4, 'big') + digest + payload
    shared[0] = 0
    for index, byte in enumerate(record[1:], start=1):
        shared[index] = byte
    shared[0] = record[0]


def _compiled_profile_payload(scope,surface,offset):
    from runtime.core_v1.test_compiled_gui import interface
    spec=interface();spec.update(interface_id='owned-compiled-profile',
        session_scope=scope,surface=surface)
    spec['predicates']=['phase','present']
    spec['symbols']['field'].update(identity_predicate='present',dependencies=['present'])
    spec['actions']={'enter':{'target_symbol':'field','operation':'enter',
        'expected_effect':{'phase':1}}}
    spec['method']={'name':'one-visible-transition','version':'1',
        'initial_state':'before','max_transitions':1,'max_runtime_ms':5000,
        'states':{
            'before':{'branches':[{'when':{'phase':0},'outcome':'action',
                'action':'enter','next_state':'done','reason':None}]},
            'done':{'branches':[{'when':{'phase':1},'outcome':'complete',
                'action':None,'next_state':None,'reason':None}]}}}
    return {'interface':spec,
        'bindings':{'enter':{'interaction':'keyboard','offset':offset,
            'tail':[{'op':'key_chord','keys':['CTRL','a']}]}},
        'predicate_rules':{
            'phase':{'point':[1,1],'states':[
                {'rgb':[31,29,1],'value':0},{'rgb':[255,0,0],'value':1}]},
            'present':{'point':[2,2],'states':[{'rgb':[62,58,4],'value':True}]}},
        'effect_rules':{'enter':{'point':[1,1],'rgb':[255,0,0]}}}


def _preserve_fake_x_run(name, root):
    """Optionally retain exact synthetic call receipts in a fresh evidence folder."""
    destination=os.environ.get('AGENT_INTERFACE_FAKE_X_EVIDENCE')
    if destination is None:
        return
    target=Path(destination)/name
    target.mkdir(parents=True,exist_ok=False)
    shutil.copytree(root,target/'run')


def _queued_fake_owner_factory(targets, directory, display_name, options):
    """Hold a fake XTEST request in a per-connection queue before sync."""
    cleanup = _Cleanup()
    fake = FakeX(cleanup)
    root = Path(directory)
    fake.backend.d.get_display_name = lambda:'fake-display'
    fake.backend.d.display = SimpleNamespace(
        info=SimpleNamespace(resource_id_base=0x1200000))
    child_queue = root/'child-x-queue.json'

    def enqueue(_display, kind, code):
        events = _read_json(child_queue, [])
        events.append({'kind':kind, 'code':code})
        _write_json(child_queue, events)

    queue_patcher = patch('runtime.backends.x11_v1.backend.xtest.fake_input',
                          side_effect=enqueue)
    queue_patcher.start()
    cleanup.addCleanup(queue_patcher.stop)

    def sync():
        if (root/'block-owner-io').exists():
            _write_json(root/'owner-io-entered.json',
                        {'queued':_read_json(child_queue, []), 'down':sorted(fake.down)})
            while not (root/'resume-owner-io').exists():
                time.sleep(0.005)

    fake.backend.d.sync = sync
    query_patcher = patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries',
                          return_value=_FakeQueries(root))
    query_patcher.start()
    cleanup.addCleanup(query_patcher.stop)
    owner = GuardedSessionOwner(targets, directory, display_name, **options)
    owner._owned_process_test_cleanup = cleanup
    return owner


class _QueuedCleanupDisplay:
    def __init__(self, root):
        self.root = Path(root)

    def sync(self):
        queue_path = self.root/'cleanup-x-queue.json'
        state_path = self.root/'fake-x-state.json'
        state = _read_json(state_path, {'down':[]})
        for event in _read_json(queue_path, []):
            if event['kind'] == X.KeyPress:
                state['down'] = sorted(set(state['down']) | {event['code']})
            elif event['kind'] == X.KeyRelease:
                state['down'] = [code for code in state['down'] if code != event['code']]
        _write_json(state_path, state)
        _write_json(queue_path, [])

    def query_keymap(self):
        state = _read_json(self.root/'fake-x-state.json', {'down':[]})
        bitmap = bytearray(32)
        for code in state['down']:
            bitmap[code//8] |= 1 << (code%8)
        return bitmap


def _apply_queued_child_requests(root):
    state_path = Path(root)/'fake-x-state.json'
    state = _read_json(state_path, {'down':[]})
    for event in _read_json(Path(root)/'child-x-queue.json', []):
        if event['kind'] == X.KeyPress:
            state['down'] = sorted(set(state['down']) | {event['code']})
        elif event['kind'] == X.KeyRelease:
            state['down'] = [code for code in state['down'] if code != event['code']]
    _write_json(state_path, state)


class OwnedProcessMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_owned_process_window_discovery_is_read_only_and_uses_query_worker(self):
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            owner=OwnedGuardedSessionOwner({'app':20},root,':fake',
                process_identity=True,query_worker=True,
                _owner_factory=_fake_owner_factory)
            try:
                report=owner.windows_for_process(_CALC_TEST_PID,'Book1')
                self.assertEqual(report['status'],'discovered',report)
                self.assertEqual(report['process_pid'],_CALC_TEST_PID)
                self.assertFalse(report['input_dispatched'],report)
                self.assertFalse(report['authority_granted'],report)
                self.assertIsNone(report['task_success'],report)
                self.assertFalse(report['replay_allowed'],report)
                self.assertEqual([row['xid'] for row in report['windows']],[20])
                self.assertEqual(report['windows'][0]['process_generation'],
                    _CALC_TEST_PROCESS_GENERATION)
            finally:
                owner.close()

    async def test_calc_preparation_expires_and_old_handle_is_rejected_preinput(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
                _calc_preparation_ttl_ns=1)
            try:
                first=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{'attempt_id':'attempt-expired'}))
                self.assertEqual(first['status'],'prepared',first)
                self.assertEqual(first['expires_in_ms'],0,first)
                second=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{'attempt_id':'attempt-current'}))
                self.assertEqual(second['status'],'prepared',second)
                self.assertNotEqual(second['call_id'],first['call_id'],second)
                stale=metadata(await server.call_tool(
                    'interface_guarded_calc_compiled',{
                        'profile_id':'calc-ocr-save-v1',
                        'bindings':{'entry':{'alias':'entry','offset':[0,0]},
                                    'save':{'alias':'save','offset':[0,0]}},
                        'reviewed_sequence':1,'reviewed_artifact_sha256':'a'*64,
                        'blank_reviewed':True,'attempt_id':'attempt-expired',
                        'prepared_call_id':first['call_id'],
                        'wait_for_result_ms':10000}))
                self.assertEqual(stale['status'],'invalid_request',stale)
                self.assertFalse(stale['operation_invoked'],stale)
                self.assertFalse(stale['input_dispatched'],stale)
                self.assertFalse(list(root.glob('*/compiled/')))
            finally:
                await server.call_tool('interface_close',{})

    async def test_window_metadata_revalidation_rejects_source_expiring_during_query(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'fake-window-metadata-delay-second-query').write_text(
                'yes',encoding='utf-8')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                source=metadata(await server.call_tool(
                    'interface_guarded_window_metadata',{'window_id':20}))
                self.assertEqual(source['status'],'inspected',source)
                result=metadata(await server.call_tool(
                    'interface_guarded_window_metadata_revalidate',
                    {'metadata_call_id':source['call_id']}))
                self.assertEqual(result['status'],'stale_or_unfocused',result)
                self.assertEqual(result['reason'],
                    'source_expired_during_revalidation',result)
                self.assertFalse(result['same_window'],result)
                self.assertFalse(result['authority_granted'],result)
                self.assertFalse(result['input_dispatched'],result)
                self.assertIsNone(result['task_success'],result)
                self.assertEqual((root/'window-metadata-query-count').read_text(), '2')
            finally:
                await server.call_tool('interface_close',{})

    async def test_window_metadata_revalidation_rejects_expired_source_before_query(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'fake-window-metadata-stale').write_text('yes',encoding='utf-8')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                  guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                source=metadata(await server.call_tool(
                    'interface_guarded_window_metadata',{'window_id':20}))
                self.assertEqual(source['status'],'inspected',source)
                stale=metadata(await server.call_tool(
                    'interface_guarded_window_metadata_revalidate',
                    {'metadata_call_id':source['call_id']}))
                self.assertEqual(stale['status'],'stale_or_unfocused',stale)
                self.assertFalse(stale['operation_invoked'],stale)
                self.assertFalse(stale['input_dispatched'],stale)
                self.assertFalse(stale['authority_granted'],stale)
                self.assertIsNone(stale['task_success'],stale)
                self.assertEqual((root/'window-metadata-query-count').read_text(), '1')
            finally:
                await server.call_tool('interface_close',{})

    async def test_window_metadata_tool_returns_cues_without_authority_or_input(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                result=metadata(await server.call_tool(
                    'interface_guarded_window_metadata',{'window_id':20}))
                self.assertEqual(result['status'],'inspected',result)
                cue=result['window_metadata']
                self.assertEqual(cue['xid'],20)
                self.assertEqual(cue['wm_class'],['soffice','LibreOffice'])
                self.assertEqual(cue['title_cue'],'Book1 - Calc')
                self.assertFalse(cue['input_authority'])
                self.assertFalse(cue['authenticated_role'])
                self.assertFalse(result['input_dispatched'])
                self.assertFalse(result['authority_granted'])
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
                report_path=Path(result['call_directory'])/'report.json'
                retained=json.loads(report_path.read_text(encoding='utf-8'))
                retained['window_metadata']['title_cue']='forged on disk'
                report_path.write_text(json.dumps(retained),encoding='utf-8')
                stable=metadata(await server.call_tool(
                    'interface_guarded_window_metadata_revalidate',
                    {'metadata_call_id':result['call_id']}))
                self.assertEqual(stable['status'],'revalidated',stable)
                self.assertTrue(stable['same_window'],stable)
                self.assertEqual(stable['metadata_call_id'],result['call_id'],stable)
                self.assertFalse(stable['input_dispatched'],stable)
                self.assertFalse(stable['authority_granted'],stable)
                self.assertIsNone(stable['task_success'],stable)
                (root/'fake-window-metadata-changed').write_text('yes',encoding='utf-8')
                changed=metadata(await server.call_tool(
                    'interface_guarded_window_metadata_revalidate',
                    {'metadata_call_id':result['call_id']}))
                self.assertEqual(changed['status'],'needs_review',changed)
                self.assertFalse(changed['same_window'],changed)
                self.assertFalse(changed['authority_granted'],changed)
                unknown=metadata(await server.call_tool(
                    'interface_guarded_window_metadata',{'window_id':21}))
                self.assertEqual(unknown['status'],'needs_review',unknown)
                self.assertFalse(unknown['input_dispatched'],unknown)
                self.assertFalse(unknown['authority_granted'],unknown)
            finally:
                await server.call_tool('interface_close',{})

    def test_snapshot_does_not_report_unconfirmed_retirement_as_retired(self):
        with tempfile.TemporaryDirectory() as directory:
            owner=OwnedGuardedSessionOwner({'app':20},directory)
            owner._process=Mock(pid=1234,exitcode=None)
            owner._process.is_alive.return_value=True
            self.assertIs(owner.snapshot()['owner_process']['retired'],False)
            owner._retirement={'retired':False,'exitcode':None,'reason':'not confirmed'}
            process=owner.snapshot()['owner_process']
            self.assertTrue(process['alive'])
            self.assertIsNone(process['retired'])
            self.assertIsNone(json.loads(json.dumps(process))['retired'])
            owner._retirement={'retired':True,'exitcode':-15,'reason':'confirmed'}
            owner._process.is_alive.return_value=False
            owner._process.exitcode=-15
            self.assertIs(owner.snapshot()['owner_process']['retired'],True)

    def test_close_does_not_replay_uncertain_release_without_display_fence(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.close_report = None
        owner._process = Mock()
        owner._process.is_alive.return_value = False
        owner._process.exitcode = -15
        owner._retirement = {'reason':'cancel unconfirmed', 'retired':True, 'exitcode':-15}
        owner._owner_client_disconnect = {'status':'unknown', 'reason':'deadline'}
        owner._owner_release_attempt = {'status':'unknown', 'reason':'deadline'}
        owner._cleanup_after_owner_retirement = Mock(return_value=({}, {}))
        owner._owner_input_obligations = {'keys':{'w':25}, 'buttons':[]}
        owner._owner_input_obligations_source = 'retired_child_shared_state'
        owner._owner_input_obligations_live_read = {'status':'snapshot'}
        owner.session_id = 'stale-release-without-display-fence'
        owner.error = 'cancel unconfirmed'
        owner._execution_unknown = True
        owner.review_required = True
        report = owner.close()
        owner._cleanup_after_owner_retirement.assert_not_called()
        self.assertEqual(report['owner_release_attempt']['reason'], 'deadline')
        self.assertEqual(report['cleanup_status'], 'UNKNOWN')
        self.assertFalse(report['replay_allowed'])

    def test_process_liveness_snapshot_records_its_observation_time(self):
        class LiveProcess:
            pid = 12345
            exitcode = None
            def is_alive(self):
                return True

        owner = object.__new__(OwnedGuardedSessionOwner)
        owner._snapshot_cache = {}
        owner._process = LiveProcess()
        owner.state = 'open'
        owner._execution_unknown = False
        owner._retirement = None
        owner.session_id = 'test-session'
        owner.binding_revision = 0
        owner.targets = {}
        owner.error = None
        owner.review_required = False
        owner._owner_client_disconnect = None
        owner._owner_input_obligations = {'keys':{}, 'buttons':[]}
        owner._owner_input_obligations_source = 'child_rpc_snapshot'
        owner._owner_input_obligations_live_read = {'status':'not_read'}
        owner._owner_release_attempt = None

        before = time.monotonic_ns()
        snapshot = owner.snapshot()
        after = time.monotonic_ns()

        observed_ns = snapshot['owner_process'].get(
            'liveness_observed_monotonic_ns')
        self.assertIsInstance(observed_ns, int, snapshot)
        self.assertLessEqual(before, observed_ns, snapshot)
        self.assertLessEqual(observed_ns, after, snapshot)

    async def test_compiled_profile_tool_is_absent_without_owned_process(self):
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True)
            names={tool.name for tool in await server.list_tools()}
            self.assertNotIn('interface_guarded_compiled',names)
            self.assertNotIn('interface_guarded_calc_compiled',names)
            await server.call_tool('interface_close',{})

    async def test_parent_custodied_calc_launch_is_opt_in_and_gates_profile(self):
        with tempfile.TemporaryDirectory() as td, patch(
                'runtime.cli_v1.mcp_server._x11_root_window_id',return_value=20), patch(
                'runtime.cli_v1.mcp_server.os',SimpleNamespace(name='posix')):
            server=create_server({'app':20},td,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
                _calc_launch_factory=lambda _artifact:None)
            try:
                names={tool.name for tool in await server.list_tools()}
                self.assertIn('interface_guarded_calc_launch',names)
                prepared=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{'attempt_id':'launch-gate-01'}))
                self.assertEqual(prepared['status'],'prepared',prepared)
                observed=metadata(await server.call_tool(
                    'interface_guarded_observe',{}))
                self.assertEqual(observed['status'],'observed',observed)
                source=observed['source']
                entry=metadata(await server.call_tool(
                    'interface_guarded_mint',{
                        'alias':'entry','source_sequence':source['sequence'],
                        'point':[8,8],'region_size':[4,4]}))
                save=metadata(await server.call_tool(
                    'interface_guarded_mint',{
                        'alias':'save','source_sequence':source['sequence'],
                        'point':[20,20],'region_size':[4,4]}))
                self.assertEqual(entry['status'],'minted',entry)
                self.assertEqual(save['status'],'minted',save)
                result=metadata(await server.call_tool(
                    'interface_guarded_calc_compiled',{
                        'profile_id':'calc-ocr-save-v1',
                        'bindings':{'entry':{'alias':'entry','offset':entry['offset']},
                                    'save':{'alias':'save','offset':save['offset']}},
                        'reviewed_sequence':source['sequence'],
                        'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                        'blank_reviewed':True,'attempt_id':'launch-gate-01',
                        'prepared_call_id':prepared['call_id']}))
                self.assertEqual(result['status'],'needs_review',result)
                self.assertEqual(result['error'],'CALC_LAUNCH_REVIEW_BIND_REQUIRED',result)
                self.assertFalse(result['operation_invoked'],result)
                self.assertFalse(result['input_dispatched'],result)
                self.assertIsNone(result['task_success'],result)
                self.assertTrue(Path(prepared['artifact_path']).is_file())
            finally:
                await server.call_tool('interface_close',{})

    async def test_public_calc_launch_review_and_close_keep_cleanup_separate_from_exit(self):
        lifecycle_order=[]
        class FakeCalcLaunch:
            launched=False
            def launch(self,artifact):
                self.launched=True
                return {'status':'launched','pid':4500,'start_ticks':700,
                    'input_dispatched':False,'task_success':None,
                    'replay_allowed':False}
            def retain_initial_process_group_custody(self,owner):
                owner._calc_process_group_custody={'fixture':'parent-custody'}
                owner._calc_process_group_cleanup_target=self.cleanup_owned_process_group
                return {'status':'launcher_retained','custody':{'fixture':'parent-custody'},
                    'authority_granted':False,'input_dispatched':False,
                    'task_success':None,'replay_allowed':False}
            def discover_owned_window(self,_owner,**_kwargs):
                return {'status':'candidate_found','candidate':{
                    'xid':91,'process_pid':4501,'process_start_ticks':701,
                    'mapped':True},'input_dispatched':False,
                    'authority_granted':False,'task_success':None,
                    'replay_allowed':False}
            def review_and_bind_owned_window(self,_owner,window_id,**_kwargs):
                return {'status':'reviewed','candidate':{'xid':window_id},
                    'input_dispatched':False,'authority_granted':False,
                    'task_success':None,'replay_allowed':False}
            def wait_for_verified_exit(self,*,timeout_s):
                self.assert_timeout=timeout_s
                lifecycle_order.append(('target_exit_wait',timeout_s))
                return {'status':'unknown','reason':'calc_target_exit_timeout',
                    'task_success':None,'replay_allowed':False}
            def cleanup_owned_process_group(self,custody):
                return {'status':'terminated','verified_empty':True,
                    'clean_exit_verified':False,'custody':custody,
                    'task_success':None,'replay_allowed':False}
            def close(self):
                return None

        original_owner_close=OwnedGuardedSessionOwner.close
        def tracked_owner_close(owner):
            result=original_owner_close(owner)
            lifecycle_order.append(('input_owner_closed',result.get('status'),
                                    result.get('verified')))
            return result

        with tempfile.TemporaryDirectory() as td, patch(
                'runtime.cli_v1.mcp_server._x11_root_window_id',return_value=20), patch(
                'runtime.cli_v1.mcp_server.os',SimpleNamespace(name='posix')):
            launches=[]
            def factory(artifact):
                launch=FakeCalcLaunch();launches.append(launch);return launch
            server=create_server({'app':20},td,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
                _calc_launch_factory=factory)
            close_patcher=patch.object(OwnedGuardedSessionOwner,'close',tracked_owner_close)
            close_patcher.start()
            try:
                prepared=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{'attempt_id':'launch-live-route-01'}))
                launch=metadata(await server.call_tool(
                    'interface_guarded_calc_launch',{
                        'prepared_call_id':prepared['call_id'],
                        'wait_for_result_ms':10000}))
                self.assertEqual(launch['status'],'candidate_found',launch)
                self.assertEqual(launch['parent_process_custody'],'retained',launch)
                self.assertFalse(launch['input_dispatched'],launch)
                self.assertFalse(launch['authority_granted'],launch)
                reviewed=metadata(await server.call_tool(
                    'interface_guarded_review_window',{'window_id':91}))
                self.assertEqual(reviewed['status'],'reviewed',reviewed)
                self.assertTrue(launches[0].launched)
                closed=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(closed['status'],'closed',closed)
                lifecycle=closed['calc_target_lifecycle'][0]
                self.assertEqual(lifecycle['process_group_cleanup']['status'],
                    'terminated',lifecycle)
                self.assertTrue(lifecycle['process_group_cleanup']['verified_empty'])
                self.assertFalse(lifecycle['process_group_cleanup']['clean_exit_verified'])
                self.assertEqual(lifecycle['target_process_exit_receipt']['reason'],
                    'forced_cleanup_is_not_clean_exit')
                self.assertIsNone(closed.get('task_success'))
                self.assertEqual(lifecycle_order[0][0],'input_owner_closed',lifecycle_order)
                self.assertEqual(lifecycle_order[1],('target_exit_wait',5.0),lifecycle_order)
            finally:
                try:
                    await server.call_tool('interface_close',{})
                finally:
                    close_patcher.stop()

    async def test_invalid_compiled_profile_is_rejected_before_call_admission(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                result=metadata(await server.call_tool('interface_guarded_compiled',{
                    'interface':{'format':'not-a-compiled-interface'},
                    'bindings':{},'predicate_rules':{},'effect_rules':{},
                    'wait_for_result_ms':0}))
                self.assertEqual(result['status'],'invalid_request',result)
                self.assertFalse(result['operation_invoked'])
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
                self.assertFalse(list(root.glob('calls/*/request.json')))
            finally:
                await server.call_tool('interface_close',{})

    async def test_unregistered_calc_profile_is_refused_before_owner_call(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                result=metadata(await server.call_tool('interface_guarded_calc_compiled',{
                    'profile_id':'client-module:callback',
                    'bindings':{'entry':{'alias':'field','offset':[1,1]},
                                'save':{'alias':'field2','offset':[2,2]}},
                    'reviewed_sequence':1,
                    'reviewed_artifact_sha256':'a'*64,
                    'blank_reviewed':True,'attempt_id':'attempt-1'}))
                self.assertEqual(result['status'],'invalid_request',result)
                self.assertFalse(result['operation_invoked'])
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
                self.assertFalse(list(root.glob('*/request.json')))
            finally:
                await server.call_tool('interface_close',{})

    async def test_registered_calc_profile_runs_through_owned_mcp_and_releases(self):
        from runtime.guarded_x11_v1.test_calc_symbolic_plan_v1 import (
            plan as calc_symbolic_plan)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            task_values={'A1':'24680','A2':'13579'}
            task_plan=calc_symbolic_plan()
            from runtime.guarded_x11_v1.calc_symbolic_plan_v1 import (
                validate_and_bind_calc_plan)
            result_digest=validate_and_bind_calc_plan(task_plan,
                session_scope='prepared-scope',surface='prepared-surface',
                target_aliases={'entry':'prepared_entry','save':'prepared_save'})[
                    'plan_sha256']
            (root/'calc-task-values.json').write_text(
                json.dumps(task_values),encoding='utf-8')
            (root/'calc-profile-mode').write_text('enabled',encoding='utf-8')
            (root/'fake-target-exit-receipt').write_text('enabled',encoding='utf-8')
            (root/'calc-save-frame-unchanged').write_text('enabled',encoding='utf-8')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)
            try:
                prepared=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{
                        'attempt_id':'calc-offline-e2e-01',
                        'task_values':task_values,
                        'task_plan':task_plan}))
                self.assertEqual(prepared['status'],'prepared',prepared)
                self.assertEqual(prepared['task_values'],task_values,prepared)
                self.assertEqual(prepared['task_plan_sha256'],result_digest,prepared)
                self.assertFalse(prepared['operation_invoked'],prepared)
                self.assertFalse(prepared['input_dispatched'],prepared)
                prepared_path=Path(prepared['artifact_path'])
                self.assertEqual(prepared_path.name,'task-artifact.fods',prepared)
                self.assertEqual(prepared_path.parent.name,prepared['call_id'],prepared)
                self.assertTrue(prepared_path.is_file(),prepared)
                self.assertEqual(prepared['expires_in_ms'],300000,prepared)
                self.assertEqual(prepared['target_launch_status'],
                                 'not_attempted',prepared)
                self.assertEqual(prepared['parent_process_custody'],
                                 'not_established',prepared)
                second_preparation=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{'attempt_id':'other-attempt'}))
                self.assertEqual(second_preparation['status'],'busy',second_preparation)
                self.assertFalse(second_preparation['operation_invoked'],
                                 second_preparation)
                mismatch=metadata(await server.call_tool(
                    'interface_guarded_calc_compiled',{
                        'profile_id':'calc-ocr-save-v1',
                        'bindings':{'entry':{'alias':'calc_entry','offset':[0,0]},
                                    'save':{'alias':'calc_save','offset':[0,0]}},
                        'reviewed_sequence':1,'reviewed_artifact_sha256':'a'*64,
                        'blank_reviewed':True,'attempt_id':'different-attempt',
                        'prepared_call_id':prepared['call_id'],
                        'wait_for_result_ms':10000}))
                self.assertEqual(mismatch['status'],'invalid_request',mismatch)
                self.assertFalse(mismatch['operation_invoked'],mismatch)
                self.assertFalse(mismatch['input_dispatched'],mismatch)
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(observed['status'],'observed',observed)
                source=observed['source']
                entry=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_entry',source_sequence=source['sequence'],
                    point=[16,31],region_size=[24,16])))
                save=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_save',source_sequence=source['sequence'],
                    point=[200,205],region_size=[16,12])))
                self.assertEqual(entry['status'],'minted',entry)
                self.assertEqual(save['status'],'minted',save)
                result=metadata(await server.call_tool('interface_guarded_calc_compiled',{
                    'profile_id':'calc-ocr-save-v1',
                    'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                                'save':{'alias':'calc_save','offset':save['offset']}},
                    'reviewed_sequence':source['sequence'],
                    'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                    'blank_reviewed':True,'attempt_id':'calc-offline-e2e-01',
                    'prepared_call_id':prepared['call_id'],
                    'wait_for_result_ms':10000}))
                self.assertIn('profile_id',result,result)
                self.assertEqual(result['profile_id'],'calc-ocr-save-v1',result)
                self.assertEqual(result['attempt_id'],'calc-offline-e2e-01',result)
                self.assertEqual(result['task_effect_verification']['status'],
                                 'not_configured',result)
                self.assertEqual(result['task_artifact_admission']['call_id'],
                                 prepared['call_id'],result)
                self.assertEqual(result['task_artifact_admission']['attempt_id'],
                                 result['attempt_id'],result)
                self.assertEqual(result['task_artifact_admission']['task_plan_sha256'],
                                 result_digest,result)
                self.assertEqual(result['method_receipt']['task_plan_sha256'],
                                 result_digest,result)
                self.assertEqual(result['method_receipt']['task_plan_interface']
                                 ['interface_id'],
                                 'planner-calc-two-cell-v1',result)
                self.assertEqual(result['task_artifact_admission']['process_generation'],
                                 source['pointer_binding']['process_generation'],result)
                self.assertEqual(result['task_artifact_admission']['window_generation'],
                                 source['pointer_binding']['window_generation'],result)
                self.assertEqual(result['task_artifact_root_call_id'],
                                 prepared['call_id'],result)
                self.assertEqual(result['method_receipt']['reason'],
                                 'effect_unavailable',result)
                graph_observations=result['method_receipt']['observations']
                self.assertGreaterEqual(len(graph_observations),2,result)
                self.assertEqual(graph_observations[-2]['evidence_digest'],
                                 graph_observations[-1]['evidence_digest'],result)
                same_frame_save_checks=[event for event in
                    result['method_receipt']['critical_events']
                    if event.get('event')=='effect_checked'
                    and event.get('action')=='persist_document']
                self.assertEqual(len(same_frame_save_checks),1,result)
                self.assertEqual(same_frame_save_checks[0]['status'],
                                 'unavailable',result)
                self.assertEqual(result['feedback']['image_status'],'image',result)
                self.assertGreater(result['feedback']['owner_feedback_sequence'],
                    result['method_receipt']['observations'][-1]['sequence'],result)
                self.assertEqual(
                    result['feedback']['image_reference']['observation_id'],
                    result['feedback']['owner_feedback_observation_id'],result)
                self.assertIsInstance(result['task_save_request'],dict,result)
                self.assertEqual(result['target_process_exit_receipt']['schema'],
                    'agent-interface/calc-target-exit-receipt-v2',result)
                self.assertIsNone(result['task_success'],result)
                self.assertFalse(result['replay_allowed'],result)
                self.assertNotEqual(result['method_receipt']['outcome'],
                                    'TASK_SUCCEEDED',result)
                fake_state_paths=list(root.rglob('calc-fake-state.json'))
                self.assertEqual(result['method_receipt']['completed_transitions'],2,result)
                self.assertEqual(result['method_receipt']['outcome'],'SAFE_YIELD',result)
                self.assertEqual(result['method_receipt']['reason'],'effect_unavailable',result)
                self.assertTrue(all(row['release_verified'] is True
                                    for row in result['method_receipt']['transitions']),result)
                self.assertTrue(any(row['predicates'].get('cells_match') is True
                                    for row in result['method_receipt']['observations']),result)
                ocr_paths=list(Path(result['call_directory']).glob('calc-ocr/*.json'))
                ocr_records=[json.loads(path.read_text()) for path in ocr_paths]
                self.assertGreater(len(ocr_records),1,ocr_records)
                self.assertTrue(all(row['input_dispatched'] is False and
                                    row['authority_granted'] is False
                                    for row in ocr_records),ocr_records)
                self.assertTrue(fake_state_paths)
                fake_state=json.loads(fake_state_paths[0].read_text())
                self.assertTrue(fake_state['entered'],fake_state)
                self.assertTrue(fake_state['save_requested'],fake_state)
                self.assertEqual(fake_state['down'],[],fake_state)
                self.assertTrue(list(Path(result['call_directory']).glob('calc-ocr/*.tsv')))
                self.assertTrue(list(Path(result['call_directory']).glob('compiled/images/*.png')))
                lookup=metadata(await server.call_tool('interface_results',{
                    'call_id':result['call_id']}))
                self.assertEqual(lookup['profile_id'],'calc-ocr-save-v1',lookup)
                self.assertEqual(lookup['attempt_id'],'calc-offline-e2e-01',lookup)
                self.assertEqual(lookup['task_artifact_admission'],
                                 result['task_artifact_admission'],lookup)
                self.assertEqual(lookup['task_save_request'],
                                 result['task_save_request'],lookup)
                self.assertEqual(lookup['target_process_exit_receipt'],
                    result['target_process_exit_receipt'],lookup)
                self.assertIsNone(lookup['task_success'],lookup)
                preclose=metadata(await server.call_tool('interface_verify_task',{
                    'call_id':result['call_id']}))
                self.assertEqual(preclose['status'],'unknown',preclose)
                self.assertEqual(preclose['reason'],'verified_close_required',preclose)
                replay=metadata(await server.call_tool('interface_guarded_calc_compiled',{
                    'profile_id':'calc-ocr-save-v1',
                    'bindings':{'entry':{'alias':'calc_entry','offset':[0,0]},
                                'save':{'alias':'calc_save','offset':[0,0]}},
                    'reviewed_sequence':1,'reviewed_artifact_sha256':'a'*64,
                    'blank_reviewed':True,'attempt_id':'calc-offline-e2e-01',
                    'prepared_call_id':prepared['call_id'],'wait_for_result_ms':10000}))
                self.assertEqual(replay['status'],'invalid_request',replay)
                self.assertFalse(replay['operation_invoked'],replay)
                self.assertFalse(replay['input_dispatched'],replay)
            finally:
                closed=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(closed['status'],'closed',closed)
                self.assertTrue(closed['verified'],closed)
                self.assertTrue(closed['owner_process_retired'],closed)
                self.assertTrue(closed['release_confirmed'],closed)
            # FakeX simulates the target writing the saved document. The
            # verifier must join these parsed bytes to the parent-held action
            # and exit receipts, not the presentation report file.
            artifact_path=Path(prepared['artifact_path'])
            dynamic_fods=_CALC_TASK_FODS.replace(
                b'office:value="731"',
                ('office:value="'+task_values['A1']+'"').encode())
            dynamic_fods=dynamic_fods.replace(
                b'office:value="864"',
                ('office:value="'+task_values['A2']+'"').encode())
            artifact_path.write_bytes(dynamic_fods)
            report_path=Path(result['call_directory'])/'report.json'
            report_path.write_text(json.dumps({
                'task_artifact_admission':{'forged':True},
                'task_save_request':{'forged':True},
                'target_process_exit_receipt':{'forged':True}}),encoding='utf-8')
            verified=metadata(await server.call_tool('interface_verify_task',{
                'call_id':result['call_id']}))
            self.assertEqual(verified['status'],'verified',verified)
            self.assertIs(verified['task_success'],True,verified)
            self.assertEqual(verified['task_effect']['reason'],
                             'registered_calc_saved_artifact_verified',verified)
            self.assertEqual(verified['task_effect']['parsed_effect']['cells'],
                             task_values,verified)
            self.assertEqual(verified['task_effect']['save_controller']['call_id'],
                             prepared['call_id'],verified)
            self.assertFalse(verified['operation_invoked'],verified)

            repeated=metadata(await server.call_tool('interface_verify_task',{
                'call_id':result['call_id']}))
            self.assertEqual(repeated['status'],'verified',repeated)
            self.assertIs(repeated['task_success'],True,repeated)
            self.assertFalse(repeated['operation_invoked'],repeated)
            wrong_profile=metadata(await server.call_tool('interface_verify_task',{
                'call_id':'0'*32}))
            self.assertEqual(wrong_profile['status'],'unknown_call',wrong_profile)
            self.assertFalse(wrong_profile['operation_invoked'],wrong_profile)
            retain_evidence = os.environ.get(
                'AGENT_INTERFACE_RETAIN_CALC_PROFILE_EVIDENCE')
            if retain_evidence:
                (root/'task-verification-result.json').write_text(json.dumps({
                    'call_id':verified['call_id'],
                    'attempt_id':verified['attempt_id'],
                    'status':verified['status'],
                    'reason':verified['task_effect']['reason'],
                    'task_success':verified['task_success'],
                    'artifact_sha256':verified['task_effect'].get('artifact_sha256'),
                    'report_file_was_tampered':True,
                    'close':{'verified':closed['verified'],
                        'owner_process_retired':closed['owner_process_retired'],
                        'release_confirmed':closed['release_confirmed']},
                },sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
                evidence_root=Path(retain_evidence).resolve()
                evidence_root.mkdir(parents=True,exist_ok=False)
                shutil.copytree(root,evidence_root/'raw-runtime')
                source_root=Path(__file__).resolve().parents[2]
                source_files=(
                    'runtime/guarded_x11_v1/calc_profile_v1.py',
                    'runtime/guarded_x11_v1/calc_task_artifact_v1.py',
                    'runtime/cli_v1/mcp_guarded.py',
                    'runtime/cli_v1/mcp_server.py',
                    'runtime/cli_v1/owned_guarded_session.py',
                    'runtime/cli_v1/test_mcp_owned_process.py')
                manifest={
                    'schema':'agent-interface/calc-owned-mcp-offline-evidence-v1',
                    'environment':'synthetic FakeX in an owned child process; no live GUI',
                    'profile_id':'calc-ocr-save-v1',
                    'attempt_id':'calc-offline-e2e-01',
                    'call_id':result['call_id'],
                    'graph':{'outcome':result['method_receipt']['outcome'],
                        'reason':result['method_receipt']['reason'],
                        'completed_transitions':result['method_receipt']['completed_transitions'],
                        'release_verified':[row['release_verified'] for row in
                                            result['method_receipt']['transitions']],
                        'recognized_filled_observation':any(
                            row['predicates'].get('cells_filled') is True for row in
                            result['method_receipt']['observations'])},
                    'synthetic_environment':{'values_entered':'A1=731; A2=864',
                        'save_requested':True,'all_fake_inputs_released':True},
                    'task_effect_verification':result['task_effect_verification'],
                    'parent_verification':{'status':verified['status'],
                        'reason':verified['task_effect']['reason'],
                        'task_success':verified['task_success'],
                        'report_file_was_tampered':True},
                    'task_success':result['task_success'],
                    'ocr_record_count':len(list(Path(result['call_directory']).glob(
                        'calc-ocr/*.json'))),
                    'owner_elapsed_ns':result.get('owner_timing',{}).get('elapsed_ns'),
                    'raw_evidence':'raw-runtime/ (call reports, PNG captures, OCR TSV and receipts)',
                    'source_sha256':{name:hashlib.sha256(
                        (source_root/name).read_bytes()).hexdigest()
                        for name in source_files}}
                (evidence_root/'manifest.json').write_text(json.dumps(
                    manifest,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')

    async def test_semantic_plan_reuse_across_fresh_calc_owners_scores_each_task(self):
        from runtime.guarded_x11_v1.test_calc_symbolic_plan_v1 import (
            plan as calc_symbolic_plan)
        from runtime.guarded_x11_v1.calc_symbolic_plan_v1 import (
            validate_and_bind_calc_plan)

        with tempfile.TemporaryDirectory() as td:
            parent=Path(td)
            task_plan=calc_symbolic_plan()
            canonical_plan_bytes=json.dumps(task_plan,sort_keys=True,
                separators=(',',':'),allow_nan=False).encode('utf-8')
            boundary_values=(
                ('0','999999999'), ('1','100000000'), ('9','99999999'),
                ('10','10000000'), ('99','9999999'), ('100','999999'),
                ('999','99999'), ('1000','9999'),
                ('99999999','1'), ('999999999','0'))
            task_rows=tuple((f'warm-task-{index+1:02d}',
                {'A1':a1,'A2':a2},f'{index+1:064x}')
                for index,(a1,a2) in enumerate(boundary_values))
            receipts=[]
            benchmark_started_ns=time.monotonic_ns()
            for index,(attempt_id,task_values,incarnation) in enumerate(task_rows):
                task_started_ns=time.monotonic_ns()
                plan_origin=('fixture_seed' if index==0 else
                             'prior_attempt_reuse')
                plan_source_attempt_id=(None if index==0 else
                                        task_rows[0][0])
                supplied_plan=json.loads(canonical_plan_bytes)
                root=parent/f'owner-{index+1}'
                root.mkdir()
                (root/'calc-task-values.json').write_text(
                    json.dumps(task_values),encoding='utf-8')
                (root/'calc-profile-mode').write_text('enabled',encoding='utf-8')
                (root/'fake-target-exit-receipt').write_text('enabled',encoding='utf-8')
                (root/'fake-calc-save-writes-artifact').write_text(
                    'enabled',encoding='utf-8')
                (root/'fake-process-incarnation').write_text(
                    incarnation,encoding='ascii')
                server=create_server({'app':20},root,session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,
                    guarded_window_lifecycle=True,guarded_owned_process=True,
                    _guarded_owner_factory=_fake_owner_factory)
                closed=False
                try:
                    prepared=metadata(await server.call_tool(
                        'interface_guarded_calc_prepare',{
                            'attempt_id':attempt_id,'task_values':task_values,
                            'task_plan':supplied_plan}))
                    self.assertEqual(prepared['status'],'prepared',prepared)
                    observed=metadata(await server.call_tool(
                        'interface_guarded_observe',{}))
                    self.assertEqual(observed['status'],'observed',observed)
                    source=observed['source']
                    entry_alias=f'entry_{index+1}'
                    save_alias=f'save_{index+1}'
                    entry=metadata(await server.call_tool(
                        'interface_guarded_mint',{
                            'alias':entry_alias,'source_sequence':source['sequence'],
                            'point':[16,31],'region_size':[24,16]}))
                    save=metadata(await server.call_tool(
                        'interface_guarded_mint',{
                            'alias':save_alias,'source_sequence':source['sequence'],
                            'point':[200,205],'region_size':[16,12]}))
                    self.assertEqual(entry['status'],'minted',entry)
                    self.assertEqual(save['status'],'minted',save)
                    expected_binding=validate_and_bind_calc_plan(supplied_plan,
                        session_scope=observed['session']['compiled_scope'],
                        surface=observed['session']['compiled_surface'],
                        target_aliases={'entry':entry_alias,'save':save_alias})
                    result=metadata(await server.call_tool(
                        'interface_guarded_calc_compiled',{
                            'profile_id':'calc-ocr-save-v1',
                            'bindings':{
                                'entry':{'alias':entry_alias,'offset':entry['offset']},
                                'save':{'alias':save_alias,'offset':save['offset']}},
                            'reviewed_sequence':source['sequence'],
                            'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                            'blank_reviewed':True,'attempt_id':attempt_id,
                            'prepared_call_id':prepared['call_id'],
                            'wait_for_result_ms':10000}))
                    self.assertEqual(result['method_receipt']['task_plan_sha256'],
                                     prepared['task_plan_sha256'],result)
                    self.assertEqual(prepared['task_plan_sha256'],
                                     expected_binding['plan_sha256'],prepared)
                    self.assertEqual(result['method_receipt']['task_plan_interface'],
                                     expected_binding['interface'],result)
                    self.assertEqual(result['method_receipt']['completed_transitions'],2,
                                     result)
                    self.assertTrue(all(row['release_verified'] is True for row in
                        result['method_receipt']['transitions']),result)
                    self.assertIsNone(result['task_success'],result)
                    closed_result=metadata(await server.call_tool(
                        'interface_close',{}))
                    closed=True
                    self.assertEqual(closed_result['status'],'closed',closed_result)
                    self.assertTrue(closed_result['verified'],closed_result)
                    self.assertTrue(closed_result['release_confirmed'],closed_result)
                    artifact_path=Path(prepared['artifact_path'])
                    self.assertTrue(artifact_path.is_file(),artifact_path)
                    fake_state=json.loads(next(root.rglob(
                        'calc-fake-state.json')).read_text(encoding='utf-8'))
                    self.assertTrue(fake_state['save_requested'],fake_state)
                    self.assertTrue(fake_state['artifact_written_on_save'],fake_state)
                    self.assertEqual(fake_state['completed_entries'],
                                     [task_values['A1'],task_values['A2']],fake_state)
                    verified=metadata(await server.call_tool(
                        'interface_verify_task',{'call_id':result['call_id']}))
                    self.assertEqual(verified['status'],'verified',verified)
                    self.assertIs(verified['task_success'],True,verified)
                    self.assertEqual(verified['task_effect']['parsed_effect']['cells'],
                                     task_values,verified)
                    receipts.append({'attempt_id':attempt_id,
                        'prepared':prepared,'observed':observed,'result':result,
                        'close':closed_result,'verified':verified,
                        'plan_interface':result['method_receipt']['task_plan_interface'],
                        'plan_origin':plan_origin,
                        'plan_source_attempt_id':plan_source_attempt_id,
                        'task_elapsed_ns':time.monotonic_ns()-task_started_ns})
                finally:
                    if not closed:
                        await server.call_tool('interface_close',{})

            first,second=receipts[:2]
            self.assertEqual(len(receipts),10)
            self.assertTrue(all(row['verified']['task_success'] is True
                                for row in receipts))
            self.assertEqual(len({row['verified']['task_effect']['artifact_sha256']
                                  for row in receipts}),len(receipts))
            self.assertEqual(len({row['observed']['session']['session_id']
                                  for row in receipts}),len(receipts))
            self.assertEqual(len({row['attempt_id'] for row in receipts}),len(receipts))
            self.assertEqual(len({row['prepared']['task_plan_sha256']
                                  for row in receipts}),1)
            for row in receipts[1:]:
                self.assertEqual(row['plan_origin'],'prior_attempt_reuse')
                self.assertEqual(row['plan_source_attempt_id'],first['attempt_id'])
            self.assertNotEqual(first['prepared']['call_id'],
                                second['prepared']['call_id'])
            self.assertNotEqual(first['result']['call_id'],second['result']['call_id'])
            self.assertNotEqual(first['observed']['session']['session_id'],
                                second['observed']['session']['session_id'])
            self.assertNotEqual(first['plan_interface']['session_scope'],
                                second['plan_interface']['session_scope'])
            self.assertNotEqual(first['plan_interface']['symbols']['cell_entry']
                                ['target_reference'],
                                second['plan_interface']['symbols']['cell_entry']
                                ['target_reference'])
            self.assertEqual(first['prepared']['task_plan_sha256'],
                             second['prepared']['task_plan_sha256'])
            self.assertEqual(first['plan_origin'],'fixture_seed')
            self.assertIsNone(first['plan_source_attempt_id'])
            self.assertEqual(second['plan_origin'],'prior_attempt_reuse')
            self.assertEqual(second['plan_source_attempt_id'],
                             first['attempt_id'])
            retain=os.environ.get('AGENT_INTERFACE_RETAIN_CALC_PLAN_REUSE_EVIDENCE')
            if retain:
                evidence_root=Path(retain).resolve()
                evidence_root.mkdir(parents=True,exist_ok=False)
                shutil.copytree(parent,evidence_root/'raw-runtime')
                source_root=Path(__file__).resolve().parents[2]
                source_files=(
                    'runtime/cli_v1/test_mcp_owned_process.py',
                    'runtime/cli_v1/mcp_guarded.py',
                    'runtime/cli_v1/mcp_server.py',
                    'runtime/guarded_x11_v1/calc_profile_v1.py',
                    'runtime/guarded_x11_v1/calc_task_artifact_v1.py',
                    'runtime/guarded_x11_v1/calc_symbolic_plan_v1.py')
                manifest={'schema':'agent-interface/calc-semantic-plan-fresh-owner-reuse-v1',
                    'conditions':{'environment':'Windows Fake X owned-process fixtures',
                        'owners':len(receipts),'task_artifacts_per_owner':1,
                        'retained_plan_sha256':first['prepared']['task_plan_sha256'],
                        'provider_generation_count':0,
                        'provider_usage':'not measured; no provider was invoked',
                        'task_values':[row[1] for row in task_rows],
                        'task_elapsed_ns':[row['task_elapsed_ns'] for row in receipts],
                        'total_elapsed_ns':time.monotonic_ns()-benchmark_started_ns,
                        'successful_task_count':sum(
                            row['verified']['task_success'] is True for row in receipts),
                        'reuse_scope':'semantic plan only; all sessions, aliases, artifacts and calls are fresh',
                        'model_tokens':'not measured','efficiency_claim':False},
                    'tasks':[{'attempt_id':row['attempt_id'],
                        'prepared_call_id':row['prepared']['call_id'],
                        'compiled_call_id':row['result']['call_id'],
                        'session_id':row['observed']['session']['session_id'],
                        'session_scope':row['plan_interface']['session_scope'],
                        'plan_origin':row['plan_origin'],
                        'plan_source_attempt_id':row['plan_source_attempt_id'],
                        'plan_sha256':row['prepared']['task_plan_sha256'],
                        'task_success':row['verified']['task_success'],
                        'artifact_sha256':row['verified']['task_effect']['artifact_sha256'],
                        'release_verified':[event['release_verified'] for event in
                            row['result']['method_receipt']['transitions']],
                        'owner_close_verified':row['close']['verified'],
                        'owner_release_confirmed':row['close']['release_confirmed']}
                        for row in receipts],
                    'raw_evidence':'raw-runtime/ (ten owner call trees and generated task artifacts)',
                    'source_sha256':{name:hashlib.sha256(
                        (source_root/name).read_bytes()).hexdigest()
                        for name in source_files}}
                (evidence_root/'manifest.json').write_text(json.dumps(
                    manifest,sort_keys=True,indent=2,allow_nan=False)+'\n',
                    encoding='utf-8')
    async def test_registered_calc_profile_requires_window_lifecycle_at_startup(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                result=metadata(await server.call_tool(
                    'interface_guarded_calc_compiled',{
                        'profile_id':'calc-ocr-save-v1',
                        'bindings':{'entry':{'alias':'entry','offset':[1,1]},
                                    'save':{'alias':'save','offset':[2,2]}},
                        'reviewed_sequence':1,
                        'reviewed_artifact_sha256':'a'*64,
                        'blank_reviewed':True,
                        'attempt_id':'calc-lifecycle-required'}))
                self.assertEqual(result['status'],'invalid_request',result)
                self.assertEqual(result['error'],'CALC_WINDOW_LIFECYCLE_REQUIRED',result)
                self.assertFalse(result['operation_invoked'],result)
                self.assertFalse(result['input_dispatched'],result)
                self.assertIsNone(result['task_success'],result)
                self.assertFalse(list(root.rglob('request.json')))
            finally:
                await server.call_tool('interface_close',{})

    async def test_registered_calc_profile_settles_once_after_low_confidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'calc-profile-mode').write_text(
                'settle-after-low-confidence',encoding='utf-8')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)
            try:
                prepared=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{'attempt_id':'calc-settle-low-01'}))
                source=metadata(await server.call_tool(
                    'interface_guarded_observe',{}))['source']
                entry=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_entry',source_sequence=source['sequence'],
                    point=[16,31],region_size=[24,16])))
                save=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_save',source_sequence=source['sequence'],
                    point=[200,205],region_size=[16,12])))
                result=metadata(await server.call_tool(
                    'interface_guarded_calc_compiled',{
                        'profile_id':'calc-ocr-save-v1',
                        'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                                    'save':{'alias':'calc_save','offset':save['offset']}},
                        'reviewed_sequence':source['sequence'],
                        'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                        'blank_reviewed':True,'attempt_id':'calc-settle-low-01',
                        'prepared_call_id':prepared['call_id'],
                        'wait_for_result_ms':10000}))
                self.assertEqual(result['method_receipt']['outcome'],'SAFE_YIELD',result)
                self.assertEqual(result['method_receipt']['reason'],'effect_unavailable',result)
                self.assertEqual(result['method_receipt']['completed_transitions'],2,result)
                settles=list(root.rglob('*-post-release-settle.json'))
                self.assertEqual(len(settles),2,[p.name for p in settles])
                for path in settles:
                    row=json.loads(path.read_text(encoding='utf-8'))
                    self.assertEqual(row['requested_ms'],250,row)
                    self.assertIn(row['status'],('settled','budget_limited'),row)
                ocr=list(Path(result['call_directory']).glob('calc-ocr/*.json'))
                self.assertGreaterEqual(len(ocr),4,[p.name for p in ocr])
                report=metadata(await server.call_tool('interface_results',{
                    'call_id':result['call_id']}))
                self.assertIsNone(report['task_success'],report)
            finally:
                closed=metadata(await server.call_tool('interface_close',{}))
                self.assertTrue(closed['release_confirmed'],closed)

    async def test_registered_calc_profile_stops_on_wrong_unknown_no_match_or_ambiguous_ocr(self):
        from runtime.guarded_x11_v1.test_calc_symbolic_plan_v1 import (
            plan as calc_symbolic_plan)
        for mode,expected_reason in (('wrong-after-input','effect_failed'),
                                     ('unknown-after-input','effect_unavailable'),
                                     ('no-match-after-input','effect_unavailable'),
                                     ('ambiguous-after-input','effect_unavailable')):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                root=Path(td)
                (root/'calc-profile-mode').write_text(mode,encoding='utf-8')
                server=create_server({'app':20},root,session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,
                    guarded_window_lifecycle=True,guarded_owned_process=True,
                    _guarded_owner_factory=_fake_owner_factory)
                try:
                    observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                    self.assertEqual(observed['status'],'observed',observed)
                    source=observed['source']
                    entry=metadata(await server.call_tool('interface_guarded_mint',dict(
                        alias='calc_entry',source_sequence=source['sequence'],
                        point=[16,31],region_size=[24,16],freshness_ms=5000)))
                    save=metadata(await server.call_tool('interface_guarded_mint',dict(
                        alias='calc_save',source_sequence=source['sequence'],
                        point=[200,205],region_size=[16,12],freshness_ms=5000)))
                    self.assertEqual(entry['status'],'minted',entry)
                    self.assertEqual(save['status'],'minted',save)
                    task_plan=calc_symbolic_plan()
                    prepared=metadata(await server.call_tool(
                        'interface_guarded_calc_prepare',{
                            'attempt_id':f'calc-offline-{mode}',
                            'task_values':{'A1':'731','A2':'864'},
                            'task_plan':task_plan}))
                    self.assertEqual(prepared['status'],'prepared',prepared)
                    result=metadata(await server.call_tool('interface_guarded_calc_compiled',{
                        'profile_id':'calc-ocr-save-v1',
                        'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                                    'save':{'alias':'calc_save','offset':save['offset']}},
                        'reviewed_sequence':source['sequence'],
                        'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                        'blank_reviewed':True,'attempt_id':f'calc-offline-{mode}',
                        'prepared_call_id':prepared['call_id'],
                        'wait_for_result_ms':10000}))
                    self.assertIn('method_receipt',result,result)
                    self.assertEqual(result['method_receipt']['outcome'],'SAFE_YIELD',result)
                    self.assertEqual(result['method_receipt']['reason'],expected_reason,result)
                    self.assertEqual(result['method_receipt']['completed_transitions'],1,result)
                    self.assertIsNone(result['task_success'],result)
                    self.assertFalse(result['replay_allowed'],result)
                    terminals=[event for event in result['method_receipt']['critical_events']
                               if event.get('event')=='action_terminal']
                    self.assertTrue(terminals, result)
                    self.assertTrue(all(event.get('release_verified') is True
                                        for event in terminals),result)
                    fake_state=json.loads(next(root.rglob('calc-fake-state.json')).read_text())
                    self.assertTrue(fake_state['entered'],fake_state)
                    self.assertFalse(fake_state['save_requested'],fake_state)
                    self.assertEqual(fake_state['down'],[],fake_state)
                finally:
                    await server.call_tool('interface_close',{})
                retain_negative = os.environ.get(
                    'AGENT_INTERFACE_RETAIN_CALC_PROFILE_NEGATIVE_EVIDENCE')
                if retain_negative:
                    evidence_root=Path(retain_negative).resolve()/mode
                    evidence_root.mkdir(parents=True,exist_ok=False)
                    shutil.copytree(root,evidence_root/'raw-runtime')
                    source_root=Path(__file__).resolve().parents[2]
                    source_files=(
                        'runtime/guarded_x11_v1/calc_profile_v1.py',
                        'runtime/cli_v1/mcp_guarded.py',
                        'runtime/cli_v1/mcp_server.py',
                        'runtime/cli_v1/owned_guarded_session.py',
                        'runtime/cli_v1/test_mcp_owned_process.py')
                    manifest={
                        'schema':'agent-interface/calc-owned-mcp-offline-evidence-v1',
                        'environment':'synthetic FakeX in an owned child process; no live GUI',
                        'profile_id':result['profile_id'],
                        'attempt_id':result['attempt_id'],
                        'call_id':result['call_id'],
                        'ocr_mode':mode,
                        'graph':{'outcome':result['method_receipt']['outcome'],
                            'reason':result['method_receipt']['reason'],
                            'completed_transitions':result['method_receipt']['completed_transitions'],
                            'release_verified':[event['release_verified'] for event in terminals]},
                        'synthetic_environment':{'save_requested':fake_state['save_requested'],
                            'all_fake_inputs_released':not fake_state['down']},
                        'task_effect_verification':result['task_effect_verification'],
                        'task_success':result['task_success'],
                        'raw_evidence':'raw-runtime/ (call reports, PNG captures, OCR TSV and receipts)',
                        'source_sha256':{name:hashlib.sha256(
                            (source_root/name).read_bytes()).hexdigest()
                            for name in source_files}}
                    (evidence_root/'manifest.json').write_text(json.dumps(
                        manifest,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')

    async def test_registered_calc_profile_rejects_stale_review_after_model_wait(self):
        """A provider response grounded on a superseded source cannot enter Calc."""
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'calc-profile-mode').write_text('enabled',encoding='utf-8')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)
            try:
                old=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(old['status'],'observed',old)
                old_source=old['source']
                entry=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_entry',source_sequence=old_source['sequence'],
                    point=[16,31],region_size=[24,16])))
                save=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_save',source_sequence=old_source['sequence'],
                    point=[200,205],region_size=[16,12])))
                self.assertEqual(entry['status'],'minted',entry)
                self.assertEqual(save['status'],'minted',save)

                # Stand in for the interval while a model response is pending:
                # the title/modal dependency changes before its old request arrives.
                (root/'fake-window-metadata-changed').write_text(
                    'provider-wait mutation',encoding='utf-8')
                await asyncio.sleep(0.02)
                fresh=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(fresh['status'],'observed',fresh)
                self.assertGreater(fresh['source']['sequence'],old_source['sequence'])

                result=metadata(await server.call_tool(
                    'interface_guarded_calc_compiled',{
                        'profile_id':'calc-ocr-save-v1',
                        'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                                    'save':{'alias':'calc_save','offset':save['offset']}},
                        'reviewed_sequence':old_source['sequence'],
                        'reviewed_artifact_sha256':old_source['native']['artifact']['sha256'],
                        'blank_reviewed':True,
                        'attempt_id':'calc-offline-stale-review-after-wait',
                        'wait_for_result_ms':10000}))
                self.assertEqual(result['status'],'invalid_request',result)
                self.assertEqual(result['error'],'CALC_REVIEW_SOURCE_STALE',result)
                self.assertFalse(result['operation_invoked'],result)
                self.assertFalse(result['input_dispatched'],result)
                self.assertIsNone(result['release_confirmed'],result)
                self.assertIsNone(result.get('task_success'),result)
                self.assertFalse(result.get('replay_allowed',True),result)
                self.assertFalse(list(root.rglob('calc-fake-state.json')))
            finally:
                closed=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(closed['status'],'closed',closed)
                self.assertTrue(closed['verified'],closed)
                # No input was dispatched, so a release receipt is N/A rather
                # than fabricated as verified. The fake app emitted no input state.
                self.assertIsNone(closed['release_confirmed'],closed)
                self.assertEqual(closed['session']['owner_input_obligations'],
                                 {'keys':{},'buttons':[]},closed)
            retained=os.environ.get(
                'AGENT_INTERFACE_RETAIN_CALC_PROFILE_NEGATIVE_EVIDENCE')
            if retained:
                evidence_root=Path(retained).resolve()/'stale-review-after-model-wait'
                evidence_root.mkdir(parents=True,exist_ok=False)
                shutil.copytree(root,evidence_root/'raw-runtime')
                source_root=Path(__file__).resolve().parents[2]
                source_files=(
                    'runtime/guarded_x11_v1/calc_profile_v1.py',
                    'runtime/cli_v1/mcp_guarded.py',
                    'runtime/cli_v1/mcp_server.py',
                    'runtime/cli_v1/owned_guarded_session.py',
                    'runtime/cli_v1/test_mcp_owned_process.py')
                manifest={
                    'schema':'agent-interface/calc-stale-review-after-wait-v1',
                    'environment':'synthetic Fake X; no model/provider request was sent',
                    'wait_simulation':'20 ms bounded test delay plus changed window title metadata',
                    'old_sequence':old_source['sequence'],
                    'new_sequence':fresh['source']['sequence'],
                    'compiled_result':result,
                    'owner_close':closed,
                    'no_input_state_artifact':not bool(list(
                        root.rglob('calc-fake-state.json'))),
                    'release_confirmed':closed.get('release_confirmed'),
                    'raw_evidence':'raw-runtime/ (observations, owner RPC receipts, calls)',
                    'source_sha256':{name:hashlib.sha256(
                        (source_root/name).read_bytes()).hexdigest()
                        for name in source_files}}
                (evidence_root/'manifest.json').write_text(json.dumps(
                    manifest,sort_keys=True,indent=2,allow_nan=False)+'\n',
                    encoding='utf-8')

    async def test_registered_calc_profile_cancel_during_ocr_keeps_release_and_effect_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'calc-profile-mode').write_text('block-ocr',encoding='utf-8')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                guarded_retention_mode='journal',
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(observed['status'],'observed',observed)
                source=observed['source']
                entry=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_entry',source_sequence=source['sequence'],
                    point=[16,31],region_size=[24,16])))
                save=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_save',source_sequence=source['sequence'],
                    point=[200,205],region_size=[16,12])))
                self.assertEqual(entry['status'],'minted',entry)
                self.assertEqual(save['status'],'minted',save)
                pending=metadata(await server.call_tool('interface_guarded_calc_compiled',{
                    'profile_id':'calc-ocr-save-v1',
                    'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                                'save':{'alias':'calc_save','offset':save['offset']}},
                    'reviewed_sequence':source['sequence'],
                    'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                    'blank_reviewed':True,'attempt_id':'calc-cancel-during-ocr',
                    'wait_for_result_ms':0}))
                self.assertEqual(pending['status'],'pending',pending)
                deadline=time.monotonic()+3
                while not (root/'calc-ocr-entered.json').exists() and time.monotonic()<deadline:
                    await asyncio.sleep(0.005)
                self.assertTrue((root/'calc-ocr-entered.json').exists())
                with patch('runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                           return_value={'status':'disconnected','worker_retired':True,
                                         'elapsed_ms':2.5}), \
                     patch('runtime.cli_v1.owned_guarded_session.OwnedGuardedSessionOwner._release_retired_owner_inputs',
                           return_value={'status':'readback_verified',
                               'release':{'verified':True,'keys_down':[],
                                          'buttons_down':[],'monotonic_ns':12}}):
                    cancel=metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))
                self.assertIn(cancel['status'],
                    ('pending','cancel_unconfirmed','cancel_requested','runtime_failed'),cancel)
                self.assertFalse(cancel.get('release_confirmed',False),cancel)
                self.assertIsNone(cancel.get('task_success'),cancel)
                self.assertFalse(cancel.get('replay_allowed',False),cancel)
                terminal=await self._wait_for_cancel_terminal(server,pending['call_id'])
                cleanup=terminal['cancellation']['result']
                self.assertTrue(cleanup['owner_process_retired'],cleanup)
                self.assertFalse(cleanup['release_confirmed'],cleanup)
                self.assertEqual(cleanup['cleanup_status'],'UNKNOWN',cleanup)
                self.assertIsNone(cleanup['task_success'],cleanup)
                self.assertFalse(cleanup['replay_allowed'],cleanup)
                self.assertEqual(cleanup.get('owner_input_obligations'),
                    {'keys':{},'buttons':[]})
                # OCR is held before yielding a result. No Calc input or save
                # command can follow cancellation from this retired owner.
                state_paths=list(root.rglob('calc-fake-state.json'))
                if state_paths:
                    state=json.loads(state_paths[0].read_text())
                    self.assertFalse(state['save_requested'],state)
                    self.assertEqual(state['down'],[],state)
                compiled_root=Path(terminal['call_directory'])/'compiled'
                if compiled_root.exists():
                    self.assertFalse(list(compiled_root.rglob('*.json')))
            finally:
                (root/'resume-calc-ocr').write_text('resume',encoding='utf-8')
                await server.call_tool('interface_close',{})
                _preserve_fake_x_run('calc-cancel-during-ocr',root)

    async def test_registered_calc_profile_cancel_after_first_transition_keeps_effect_unknown(self):
        from runtime.guarded_x11_v1.test_calc_symbolic_plan_v1 import (
            plan as calc_symbolic_plan)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'calc-profile-mode').write_text('enabled',encoding='utf-8')
            _write_json(root/'supervisor-fake-x.json',{'down':[1], 'effects':[], 'refused':[]})
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                guarded_prestarted_cancel_supervisor=True,
                _guarded_cancel_supervisor_target=_fake_prestarted_cancel_worker,
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                source=observed['source']
                entry=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_entry',source_sequence=source['sequence'],
                    point=[16,31],region_size=[24,16])))
                save=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_save',source_sequence=source['sequence'],
                    point=[200,205],region_size=[16,12])))
                prepared=metadata(await server.call_tool(
                    'interface_guarded_calc_prepare',{
                        'attempt_id':'calc-cancel-after-transition',
                        'task_values':{'A1':'731','A2':'864'},
                        'task_plan':calc_symbolic_plan()}))
                self.assertEqual(prepared['status'],'prepared',prepared)
                pending=metadata(await server.call_tool('interface_guarded_calc_compiled',{
                    'profile_id':'calc-ocr-save-v1',
                    'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                                'save':{'alias':'calc_save','offset':save['offset']}},
                    'reviewed_sequence':source['sequence'],
                    'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                    'blank_reviewed':True,'attempt_id':'calc-cancel-after-transition',
                    'prepared_call_id':prepared['call_id'],
                    'wait_for_result_ms':0}))
                self.assertEqual(pending['status'],'pending',pending)
                deadline=time.monotonic()+3
                save_seen=False
                while time.monotonic()<deadline:
                    states=list(root.rglob('calc-fake-state.json'))
                    if states:
                        try:
                            state=json.loads(states[0].read_text())
                        except (OSError,json.JSONDecodeError):
                            await asyncio.sleep(0.005)
                            continue
                        save_seen=state['save_requested']
                        if save_seen:
                            break
                    await asyncio.sleep(0.005)
                self.assertTrue(save_seen,'test did not reach Save boundary')
                (root/'block-owner-io').write_text('block',encoding='utf-8')
                deadline=time.monotonic()+3
                while not (root/'owner-io-entered.json').exists() and time.monotonic()<deadline:
                    await asyncio.sleep(0.005)
                self.assertTrue((root/'owner-io-entered.json').exists())
                cancel=metadata(await server.call_tool('interface_guarded_cancel',
                    {'call_id':pending['call_id']}))
                self.assertIn(cancel['status'],
                    ('pending','cancel_unconfirmed','cancel_requested','runtime_failed'),cancel)
                terminal=await self._wait_for_cancel_terminal(server,pending['call_id'])
                cleanup=terminal['cancellation']['result']
                self.assertTrue(cleanup['owner_process_retired'],cleanup)
                self.assertFalse(cleanup['release_confirmed'],cleanup)
                self.assertEqual(cleanup['cleanup_status'],'UNKNOWN',cleanup)
                self.assertIsNone(cleanup['task_success'],cleanup)
                self.assertFalse(cleanup['replay_allowed'],cleanup)
                retained=metadata(await server.call_tool('interface_results',{
                    'call_id':pending['call_id'],'include_image':False}))
                self.assertIsNone(retained['task_success'],retained)
                self.assertFalse(retained['replay_allowed'],retained)
                retained_call=retained.get('retained_call',{})
                self.assertEqual(retained_call.get('operation'),
                                 'guarded_calc_compiled',retained_call)
                self.assertEqual(retained_call.get('profile_id'),
                                 'calc-ocr-save-v1',retained_call)
                self.assertEqual(retained_call.get('attempt_id'),
                                 'calc-cancel-after-transition',retained_call)
                self.assertEqual(retained_call.get('state'),'finished',retained_call)
                report=json.loads((root/pending['call_id']/'report.json').read_text())
                self.assertFalse(report.get('replay_allowed',True),report)
                self.assertIsNone(report.get('task_success'),report)
                self.assertNotEqual(report.get('method_receipt',{}).get('outcome'),
                                    'TASK_SUCCEEDED',report)
            finally:
                (root/'resume-owner-io').write_text('resume',encoding='utf-8')
                await self._wait_for_cancel_terminal(server,pending['call_id'])
                await server.call_tool('interface_close',{})
                _preserve_fake_x_run('calc-cancel-after-save-request',root)

    async def test_registered_calc_profile_refuses_changed_process_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'calc-profile-mode').write_text('enabled',encoding='utf-8')
            (root/'fake-process-incarnation').write_text('b'*64,encoding='utf-8')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(observed['status'],'observed',observed)
                source=observed['source']
                entry=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_entry',source_sequence=source['sequence'],
                    point=[16,31],region_size=[24,16])))
                save=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='calc_save',source_sequence=source['sequence'],
                    point=[200,205],region_size=[16,12])))
                self.assertEqual(entry['status'],'minted',entry)
                self.assertEqual(save['status'],'minted',save)
                (root/'fake-window-metadata-change-incarnation').write_text(
                    'yes',encoding='utf-8')
                result=metadata(await server.call_tool('interface_guarded_calc_compiled',{
                    'profile_id':'calc-ocr-save-v1',
                    'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                                'save':{'alias':'calc_save','offset':save['offset']}},
                    'reviewed_sequence':source['sequence'],
                    'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                    'blank_reviewed':True,'attempt_id':'calc-offline-generation-change',
                    'wait_for_result_ms':10000}))
                # The Calc artifact adapter now rechecks process identity
                # before graph admission, so this mutation is rejected before
                # the method emits any observation or transition receipt.
                self.assertEqual(result['status'],'runtime_failed',result)
                self.assertFalse(result.get('input_dispatched',False),result)
                self.assertIn('target generation',result.get('error',''),result)
                self.assertIsNone(result['task_success'],result)
                self.assertFalse(result['replay_allowed'],result)
                self.assertFalse(list(root.rglob('calc-fake-state.json')))
            finally:
                closed=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(closed['status'],'closed',closed)
                self.assertTrue(closed['verified'],closed)
                self.assertTrue(closed['owner_process_retired'],closed)
            retain_negative = os.environ.get(
                'AGENT_INTERFACE_RETAIN_CALC_PROFILE_NEGATIVE_EVIDENCE')
            if retain_negative:
                evidence_root=Path(retain_negative).resolve()/'source-generation-change'
                evidence_root.mkdir(parents=True,exist_ok=False)
                shutil.copytree(root,evidence_root/'raw-runtime')
                source_root=Path(__file__).resolve().parents[2]
                source_files=(
                    'runtime/guarded_x11_v1/calc_profile_v1.py',
                    'runtime/guarded_x11_v1/calc_task_artifact_v1.py',
                    'runtime/cli_v1/mcp_guarded.py',
                    'runtime/cli_v1/mcp_server.py',
                    'runtime/cli_v1/owned_guarded_session.py',
                    'runtime/cli_v1/test_mcp_owned_process.py')
                manifest={
                    'schema':'agent-interface/calc-owned-mcp-offline-evidence-v1',
                    'environment':'synthetic FakeX in an owned child process; no live GUI',
                    'profile_id':'calc-ocr-save-v1',
                    'attempt_id':'calc-offline-generation-change',
                    'call_id':result['call_id'],
                    'condition':'process generation changed after observation and mint, before graph input',
                    'preflight':{'status':result['status'],
                        'error':result.get('error'),
                        'input_dispatched':result.get('input_dispatched',False),
                        'fake_input_state_file_created':bool(list(root.rglob('calc-fake-state.json')))},
                    'task_success':result['task_success'],
                    'raw_evidence':'raw-runtime/ (call reports, PNG captures and receipts)',
                    'source_sha256':{name:hashlib.sha256(
                        (source_root/name).read_bytes()).hexdigest()
                        for name in source_files}}
                (evidence_root/'manifest.json').write_text(json.dumps(
                    manifest,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')

    def test_retired_release_accepts_verified_reply_from_delayed_worker(self):
        from runtime.guarded_x11_v1.xres_client_fence import supervise_xres_worker

        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.display_name = 'fake-display'

        def run_delayed_worker(_target, _args, **kwargs):
            return supervise_xres_worker(
                _delayed_release_worker, (), timeout_s=kwargs['timeout_s'],
                terminate_grace_s=kwargs['terminate_grace_s'],
                accepted_statuses=kwargs['accepted_statuses'])

        with patch('runtime.cli_v1.owned_guarded_session.supervise_xres_worker',
                   side_effect=run_delayed_worker):
            result = owner._release_retired_owner_inputs(
                {'keys':{'a':38}, 'buttons':[]})

        self.assertEqual(result['status'], 'readback_verified', result)
        self.assertEqual(result['release'], {
            'verified':True, 'keys_down':[], 'buttons_down':[]})
        self.assertTrue(result['worker_retired'])
        self.assertEqual(result['worker_exitcode'], 0)
        self.assertGreaterEqual(result['elapsed_ms'], 300)
        self.assertLess(result['elapsed_ms'], 1500)

    def test_retired_release_waits_boundedly_for_clean_worker_shutdown(self):
        from runtime.guarded_x11_v1.xres_client_fence import supervise_xres_worker

        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.display_name = 'fake-display'

        def run_worker(_target, _args, **kwargs):
            return supervise_xres_worker(
                _release_then_delayed_shutdown_worker, (),
                timeout_s=kwargs['timeout_s'],
                terminate_grace_s=kwargs['terminate_grace_s'],
                accepted_statuses=kwargs['accepted_statuses'])

        with patch('runtime.cli_v1.owned_guarded_session.supervise_xres_worker',
                   side_effect=run_worker) as supervisor:
            result = owner._release_retired_owner_inputs(
                {'keys':{'a':38}, 'buttons':[]})

        self.assertEqual(result['status'], 'readback_verified', result)
        self.assertEqual(result['release'], {
            'verified':True, 'keys_down':[], 'buttons_down':[]})
        self.assertTrue(result['worker_retired'], result)
        self.assertEqual(result['worker_exitcode'], 0)
        self.assertEqual(supervisor.call_args.kwargs['terminate_grace_s'], 0.25)

    def test_retired_release_preserves_shutdown_diagnostics_without_accepting_release(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.display_name = 'fake-display'
        worker = {
            'status':'unknown',
            'reason':'worker_did_not_exit_cleanly',
            'worker_retired':True,
            'worker_exitcode':-15,
            'elapsed_ms':669.189222,
            'worker_result_status':'released',
            'worker_result_received_monotonic_ns':1200000000,
            'worker_exit_observed_monotonic_ns':1300000000,
            'worker_shutdown_wait_ms':100.0,
        }

        with patch('runtime.cli_v1.owned_guarded_session.supervise_xres_worker',
                   return_value=worker):
            result = owner._release_retired_owner_inputs(
                {'keys':{'a':38}, 'buttons':[]})

        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'worker_did_not_exit_cleanly', result)
        self.assertEqual(result['worker_exitcode'], -15, result)
        self.assertEqual(result['worker_result_status'], 'released', result)
        self.assertEqual(result['worker_result_received_monotonic_ns'],
                         1200000000, result)
        self.assertEqual(result['worker_exit_observed_monotonic_ns'],
                         1300000000, result)
        self.assertEqual(result['worker_shutdown_wait_ms'], 100.0, result)
        self.assertIsNone(result['release'], result)

    def test_retire_kills_owned_process_that_ignores_terminate(self):
        class StubbornProcess:
            def __init__(self):
                self.alive = True
                self.exitcode = None
                self.terminate_calls = 0
                self.kill_calls = 0
                self.joins = []
            def is_alive(self):
                return self.alive
            def terminate(self):
                self.terminate_calls += 1
            def kill(self):
                self.kill_calls += 1
                self.alive = False
                self.exitcode = -9
            def join(self, timeout=None):
                self.joins.append(timeout)

        owner = object.__new__(OwnedGuardedSessionOwner)
        process = StubbornProcess()
        owner._process = process
        owner.state = 'open'
        owner.error = None
        owner._execution_unknown = False
        owner.review_required = False
        owner._retirement = None

        with (patch('runtime.cli_v1.owned_guarded_session._RETIRE_TERMINATE_GRACE_S', 0.01),
              patch('runtime.cli_v1.owned_guarded_session._RETIRE_KILL_GRACE_S', 0.01)):
            result = owner._retire('cancel retirement grace elapsed')

        self.assertTrue(result['retired'], result)
        self.assertEqual(result['exitcode'], -9)
        self.assertEqual(process.terminate_calls, 1)
        self.assertEqual(process.kill_calls, 1)
        self.assertEqual(process.joins, [0.01, 0.01])
        self.assertTrue(owner._execution_unknown)
        self.assertTrue(owner.review_required)

    def test_retirement_cleans_parent_retained_calc_group_separately(self):
        class ExitingProcess:
            exitcode=-9
            def is_alive(self): return False
            def join(self, timeout=None): pass
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._process=ExitingProcess()
        owner.state='open'; owner.error=None
        owner._execution_unknown=False; owner.review_required=False
        owner._retirement=None
        custody={'schema':'agent-interface/calc-process-group-custody-v1',
            'pgid':4100,'session_id':4100,
            'launcher':{'pid':4100,'start_ticks':70001},
            'target':{'pid':4101,'start_ticks':70002},
            'expected_members':{'4100':70001,'4101':70002}}
        cleanup={'schema':'agent-interface/calc-process-group-cleanup-v1',
            'status':'terminated','verified_empty':True,
            'clean_exit_verified':False,'task_success':None,
            'replay_allowed':False}
        owner._calc_process_group_custody=custody
        owner._calc_process_group_cleanup=None
        owner._calc_process_group_cleanup_target=Mock(return_value=cleanup)

        result=owner._retire('synthetic owner death')

        self.assertTrue(result['retired'])
        self.assertEqual(result['calc_process_group_cleanup'],cleanup)
        owner._calc_process_group_cleanup_target.assert_called_once_with(custody)
        self.assertTrue(owner._execution_unknown)
        self.assertTrue(owner.review_required)
        self.assertFalse(result['calc_process_group_cleanup']['clean_exit_verified'])
        self.assertIsNone(result['calc_process_group_cleanup']['task_success'])

    def test_parent_retains_only_independently_revalidated_calc_group(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._calc_process_group_custody=None
        custody={'schema':'agent-interface/calc-process-group-custody-v1',
            'pgid':4100,'session_id':4100,
            'launcher':{'pid':4100,'start_ticks':70001},
            'target':{'pid':4101,'start_ticks':70002},
            'expected_members':{'4100':70001,'4101':70002}}
        rows=[{'pid':4100,'start_ticks':70001,'process_group':4100,'session_id':4100},
            {'pid':4101,'start_ticks':70002,'process_group':4100,'session_id':4100}]
        with patch('runtime.guarded_x11_v1.calc_process_group_v1.read_linux_process_group',
                   return_value=rows) as reader:
            retained=owner.retain_calc_process_group_custody(custody)
        self.assertEqual(retained,custody)
        reader.assert_called_once_with(4100,4100)
        with self.assertRaisesRegex(RuntimeError,'one-shot'):
            owner.retain_calc_process_group_custody(dict(custody,pgid=4102))
        unretained=object.__new__(OwnedGuardedSessionOwner)
        unretained._calc_process_group_custody=None
        changed=dict(custody,target=dict(custody['target'],start_ticks=70003))
        with patch('runtime.guarded_x11_v1.calc_process_group_v1.read_linux_process_group',
                   return_value=rows):
            with self.assertRaisesRegex(ValueError,'unowned or changed'):
                unretained.retain_calc_process_group_custody(changed)

    def test_pre_review_calc_custody_advance_records_exact_child_handoff(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner.state='open';owner.binding_revision=0;owner.review_required=False
        owner._execution_unknown=False;owner._calc_process_group_cleanup=None
        owner._owner_release_attempt=None
        owner._owner_input_obligations={'keys':{},'buttons':[]}
        previous={'schema':'agent-interface/calc-process-group-custody-v1',
            'pgid':4100,'session_id':4100,
            'launcher':{'pid':4100,'start_ticks':70001},
            'target':{'pid':4101,'start_ticks':70002},
            'expected_members':{'4100':70001,'4101':70002}}
        advanced={**previous,'target':{'pid':4102,'start_ticks':70003},
            'expected_members':{'4100':70001,'4102':70003}}
        owner._calc_process_group_custody=previous
        owner._calc_process_group_custody_history=[]
        executable='/usr/lib/libreoffice/program/soffice.bin'
        argv=[executable,'--calc','/server/task-artifact.fods']
        rows=[{'pid':4100,'start_ticks':70001,'process_group':4100,
                'session_id':4100,'parent_pid':1},
              {'pid':4102,'start_ticks':70003,'process_group':4100,
                'session_id':4100,'parent_pid':4100}]
        with (patch('runtime.cli_v1.owned_guarded_session.Path.resolve',
                    return_value=PurePosixPath(executable)),
              patch('runtime.cli_v1.owned_guarded_session.Path.read_bytes',
                    return_value=b'\0'.join(value.encode() for value in argv)+b'\0'),
              patch('runtime.guarded_x11_v1.calc_process_group_v1.read_linux_process_group',
                    return_value=rows),
              patch('runtime.guarded_x11_v1.calc_process_group_v1.advance_process_group_custody',
                    return_value=advanced) as advance):
            result=owner.advance_calc_process_group_custody(target_pid=4102,
                target_start_ticks=70003,gui_executable=executable,
                expected_argv=argv)
        self.assertEqual(result['status'],'advanced')
        self.assertEqual(owner._calc_process_group_custody,advanced)
        self.assertEqual(owner._calc_process_group_custody_history[0]['target'],
            {'pid':4102,'start_ticks':70003})
        self.assertFalse(result['authority_granted'])
        self.assertFalse(result['input_dispatched'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])
        advance.assert_called_once_with(previous,target_pid=4102,
            target_start_ticks=70003,group_snapshot=rows)

    def test_pre_review_calc_custody_advance_rejects_changed_argv(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner.state='open';owner.binding_revision=0;owner.review_required=False
        owner._execution_unknown=False;owner._calc_process_group_cleanup=None
        owner._owner_release_attempt=None
        owner._owner_input_obligations={'keys':{},'buttons':[]}
        owner._calc_process_group_custody={'schema':'agent-interface/calc-process-group-custody-v1'}
        executable='/usr/lib/libreoffice/program/soffice.bin'
        with (patch('runtime.cli_v1.owned_guarded_session.Path.resolve',
                    return_value=PurePosixPath(executable)),
              patch('runtime.cli_v1.owned_guarded_session.Path.read_bytes',
                    return_value=b'/usr/lib/libreoffice/program/soffice.bin\0--calc\0wrong.fods\0'),
              patch('runtime.guarded_x11_v1.calc_process_group_v1.read_linux_process_group') as reader):
            with self.assertRaisesRegex(ValueError,'executable or launch argv changed'):
                owner.advance_calc_process_group_custody(target_pid=4102,
                    target_start_ticks=70003,gui_executable=executable,
                    expected_argv=[executable,'--calc','/server/task-artifact.fods'])
        reader.assert_not_called()

    def test_pre_review_calc_custody_advance_refuses_after_window_review(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner.state='open';owner.binding_revision=1
        owner.review_required=False;owner._execution_unknown=False
        owner._calc_process_group_cleanup=None
        owner._owner_release_attempt=None
        owner._owner_input_obligations={'keys':{},'buttons':[]}
        owner._calc_process_group_custody={'schema':'agent-interface/calc-process-group-custody-v1'}
        with patch('runtime.guarded_x11_v1.calc_process_group_v1.read_linux_process_group') as reader:
            with self.assertRaisesRegex(RuntimeError,'idle pre-review owner'):
                owner.advance_calc_process_group_custody(target_pid=4102,
                    target_start_ticks=70003,
                    gui_executable='/usr/lib/libreoffice/program/soffice.bin',
                    expected_argv=['/usr/lib/libreoffice/program/soffice.bin'])
        reader.assert_not_called()

    def test_retire_settles_brief_exit_race_after_kill(self):
        class SettlingProcess:
            def __init__(self):
                self.alive = True
                self.exitcode = None
                self.joins = []
                self.kill_calls = 0
                self.sleep_calls = []
            def is_alive(self):
                return self.alive
            def terminate(self):
                pass
            def kill(self):
                self.kill_calls += 1
            def join(self, timeout=None):
                self.joins.append(timeout)
            def settle(self, duration):
                self.sleep_calls.append(duration)
                self.alive = False
                self.exitcode = -9

        owner = object.__new__(OwnedGuardedSessionOwner)
        process = SettlingProcess()
        owner._process = process
        owner.state = 'open'
        owner.error = None
        owner._execution_unknown = False
        owner.review_required = False
        owner._retirement = None

        with (patch('runtime.cli_v1.owned_guarded_session._RETIRE_TERMINATE_GRACE_S', 0.01),
              patch('runtime.cli_v1.owned_guarded_session._RETIRE_KILL_GRACE_S', 0.01),
              patch('runtime.cli_v1.owned_guarded_session._RETIRE_KILL_SETTLE_GRACE_S',
                    0.01),
              patch('runtime.cli_v1.owned_guarded_session.time.sleep',
                    side_effect=process.settle)):
            result = owner._retire('cancel retirement grace elapsed')

        self.assertTrue(result['retired'], result)
        self.assertEqual(result['exitcode'], -9)
        self.assertEqual(process.kill_calls, 1)
        self.assertEqual(process.joins, [0.01, 0.01])
        self.assertTrue(process.sleep_calls)

    def test_retirement_receipt_reconciles_exit_between_liveness_and_exitcode_reads(self):
        class ExitingProcess:
            def __init__(self):
                self.polls = 0
                self.terminate_calls = 0
                self.joins = []
            def is_alive(self):
                self.polls += 1
                # The child is alive initially, is observed gone at the grace
                # poll, then exits just after the final poll reports it alive.
                return self.polls in (1, 3)
            @property
            def exitcode(self):
                return -15 if self.polls >= 3 else None
            def terminate(self):
                self.terminate_calls += 1
            def join(self, timeout=None):
                self.joins.append(timeout)
            def kill(self):
                raise AssertionError('kill is unnecessary after the grace poll')

        owner = object.__new__(OwnedGuardedSessionOwner)
        process = ExitingProcess()
        owner._process = process
        owner.state = 'open'
        owner.error = None
        owner._execution_unknown = False
        owner.review_required = False
        owner._retirement = None

        with patch('runtime.cli_v1.owned_guarded_session._RETIRE_TERMINATE_GRACE_S', 0.01):
            result = owner._retire('cancel retirement grace elapsed')

        self.assertTrue(result['retired'], result)
        self.assertEqual(result['exitcode'], -15)
        self.assertEqual(process.terminate_calls, 1)

    def test_close_timeout_runs_disconnect_gated_retirement_cleanup(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.close_report = None
        owner._process = Mock()
        owner._process.is_alive.return_value = True
        owner._rpc_lock = threading.Lock()
        owner._rpc_lock.acquire()
        owner._retire = Mock(return_value={'retired':True, 'exitcode':-15})
        disconnect = {'status':'disconnected', 'expected_pid':1234}
        release = {'status':'readback_verified', 'release':{'verified':True}}
        owner._cleanup_after_owner_retirement = Mock(
            return_value=(disconnect, release))
        owner._owner_input_obligations = {'keys':{'CTRL':1}, 'buttons':[]}
        owner._owner_input_obligations_source = 'retired_child_shared_state'
        owner._owner_input_obligations_live_read = {'status':'snapshot'}
        owner.session_id = 'session-close-timeout'
        owner._execution_unknown = True
        owner.review_required = True

        with patch('runtime.cli_v1.owned_guarded_session._CLOSE_TIMEOUT_S', 0):
            result = owner.close()

        owner._retire.assert_called_once_with(
            'close timed out waiting for owned operation')
        owner._cleanup_after_owner_retirement.assert_called_once_with(
            {'retired':True, 'exitcode':-15})
        self.assertEqual(result['owner_client_disconnect'], disconnect)
        self.assertEqual(result['owner_release_attempt'], release)
        self.assertEqual(result['owner_input_obligations'],
                         {'keys':{'CTRL':1}, 'buttons':[]})
        self.assertFalse(result['release_confirmed'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])
        self.assertTrue(result['late_server_request_possible'])

    def test_close_after_cancel_retirement_preserves_unconfirmed_release(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.close_report = None
        owner._process = Mock()
        owner._process.is_alive.return_value = False
        owner._process.exitcode = -15
        owner._process.pid = 1234
        owner._request_locked = Mock(side_effect=RuntimeError(
            'owned guarded session unavailable: failed'))
        owner._retirement = {'reason':'cancel control response unconfirmed',
                             'retired':True, 'exitcode':-15}
        prior_disconnect = {'status':'unknown', 'reason':'supervision_timeout'}
        prior_release = {'status':'not_attempted',
                         'reason':'owner_disconnect_not_confirmed'}
        owner._owner_client_disconnect = prior_disconnect
        owner._owner_release_attempt = prior_release
        owner._cleanup_after_owner_retirement = Mock(return_value=(
            {'status':'disconnected', 'expected_pid':1234},
            {'status':'readback_verified', 'release':{
                'verified':True, 'keys_down':[], 'buttons_down':[]}}))
        owner._owner_input_obligations = {'keys':{'a':38}, 'buttons':[]}
        owner._owner_input_obligations_source = 'retired_child_shared_state'
        owner._owner_input_obligations_live_read = {
            'status':'snapshot', 'obligations':{'keys':{'a':38}, 'buttons':[]}}
        owner.session_id = 'session-close-after-platform-resume'
        owner.error = 'cancel control response unconfirmed'
        owner._execution_unknown = True
        owner.review_required = True

        first = owner.close()
        second = owner.close()

        owner._request_locked.assert_not_called()
        owner._cleanup_after_owner_retirement.assert_not_called()
        self.assertEqual(first, second)
        self.assertEqual(first['owner_client_disconnect']['status'], 'unknown')
        self.assertEqual(first['owner_release_attempt']['status'], 'not_attempted')
        self.assertFalse(first['release_attempted'])
        self.assertFalse(first['release_confirmed'])
        self.assertEqual(first['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(first['task_success'])
        self.assertFalse(first['replay_allowed'])
        self.assertTrue(first['owner_process_retired'])

    def test_close_after_cancel_retirement_reuses_existing_cleanup_evidence(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.close_report = None
        owner._process = Mock()
        owner._process.is_alive.return_value = False
        owner._process.exitcode = -15
        owner._process.pid = 1234
        owner._rpc_lock = threading.Lock()
        owner._request_locked = Mock(side_effect=RuntimeError(
            'owned guarded session unavailable: failed'))
        owner._retirement = {
            'reason':'cancel left input or server-request obligation',
            'retired':True,
            'exitcode':-15,
        }
        owner._cleanup_after_owner_retirement = Mock(side_effect=AssertionError(
            'close must not start a second release worker'))
        disconnect = {'status':'disconnected', 'expected_pid':1234}
        release = {'status':'readback_verified',
                   'release':{'verified':True, 'keys_down':[], 'buttons_down':[]}}
        owner._owner_client_disconnect = disconnect
        owner._owner_release_attempt = release
        owner._owner_input_obligations = {'keys':{'a':38}, 'buttons':[]}
        owner._owner_input_obligations_source = 'retired_child_shared_state'
        owner._owner_input_obligations_live_read = {
            'status':'snapshot', 'obligations':{'keys':{'a':38}, 'buttons':[]}}
        owner.session_id = 'session-close-after-cancel-retirement'
        owner.error = 'cancel left input or server-request obligation'
        owner._execution_unknown = True
        owner.review_required = True

        first = owner.close()
        second = owner.close()

        owner._request_locked.assert_not_called()
        owner._cleanup_after_owner_retirement.assert_not_called()
        self.assertEqual(first, second)
        self.assertEqual(first['status'], 'cleanup_failed')
        self.assertEqual(first['cleanup_status'], 'UNKNOWN')
        self.assertFalse(first['release_confirmed'])
        self.assertIsNone(first['task_success'])
        self.assertFalse(first['replay_allowed'])
        self.assertTrue(first['owner_process_retired'])
        self.assertEqual(first['owner_client_disconnect'], disconnect)
        self.assertEqual(first['owner_release_attempt'], release)
        self.assertEqual(first['owner_input_obligations'], {'keys':{'a':38}, 'buttons':[]})

    def test_close_pipe_failure_runs_retirement_cleanup(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.close_report = None
        owner._process = Mock()
        owner._process.is_alive.return_value = False
        owner._rpc_lock = threading.Lock()
        owner._request_locked = Mock(side_effect=OSError('owner pipe closed'))
        owner._retire = Mock(return_value={'retired':True, 'exitcode':-15})
        disconnect = {'status':'unknown', 'reason':'query_timeout'}
        release = {'status':'not_attempted', 'reason':'owner_disconnect_not_confirmed'}
        owner._cleanup_after_owner_retirement = Mock(
            return_value=(disconnect, release))
        owner._owner_input_obligations = {'keys':{'CTRL':1}, 'buttons':[]}
        owner._owner_input_obligations_source = 'retired_child_shared_state'
        owner._owner_input_obligations_live_read = {'status':'snapshot'}
        owner.session_id = 'session-close-pipe-failure'
        owner._execution_unknown = False
        owner.review_required = False

        result = owner.close()

        owner._retire.assert_called_once_with('owned close result unavailable')
        owner._cleanup_after_owner_retirement.assert_called_once_with(
            {'retired':True, 'exitcode':-15})
        self.assertEqual(result['owner_client_disconnect'], disconnect)
        self.assertEqual(result['owner_release_attempt'], release)
        self.assertFalse(result['release_confirmed'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_close_forced_retirement_after_receipt_runs_cleanup(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.close_report = None
        owner._process = Mock()
        owner._process.is_alive.return_value = True
        owner._rpc_lock = threading.Lock()
        owner._request_locked = Mock(return_value={
            'status':'closed', 'release_attempted':False,
            'connection_close_attempted':True,
        })
        owner._retire = Mock(return_value={'retired':True, 'exitcode':-15})
        disconnect = {'status':'disconnected', 'expected_pid':4321}
        release = {'status':'unknown', 'reason':'supervision_timeout'}
        owner._cleanup_after_owner_retirement = Mock(
            return_value=(disconnect, release))
        owner._owner_input_obligations = {'keys':{'CTRL':1}, 'buttons':[]}
        owner._owner_input_obligations_source = 'retired_child_shared_state'
        owner._owner_input_obligations_live_read = {'status':'snapshot'}
        owner.session_id = 'session-close-retirement'
        owner._execution_unknown = False
        owner.review_required = False

        result = owner.close()

        owner._retire.assert_called_once_with(
            'owned process did not exit after close receipt')
        owner._cleanup_after_owner_retirement.assert_called_once_with(
            {'retired':True, 'exitcode':-15})
        self.assertEqual(result['owner_client_disconnect'], disconnect)
        self.assertEqual(result['owner_release_attempt'], release)
        self.assertFalse(result['release_confirmed'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_x11_backend_publishes_key_obligation_before_sync_can_block(self):
        events = []
        backend = object.__new__(X11Backend)
        backend.d = SimpleNamespace()
        backend.held_keycodes = {}
        backend.held_buttons = set()
        backend.emissions = 0
        backend._keycode = lambda _key: 1
        backend._before_input_press = lambda: None
        backend._input_obligation_publisher = lambda keys, buttons: events.append(
            ('snapshot', dict(keys), list(buttons)))

        def blocked_sync():
            events.append(('sync',))
            raise OSError('simulated blocked XSync')

        backend.d.sync = blocked_sync
        with patch('runtime.backends.x11_v1.backend.xtest.fake_input',
                   side_effect=lambda _display, kind, code: events.append(
                       ('emit', kind, code))):
            with self.assertRaisesRegex(OSError, 'simulated blocked XSync'):
                backend.key_state('CTRL', True)

        self.assertEqual(events, [
            ('snapshot', {'CTRL':1}, []),
            ('emit', X.KeyPress, 1),
            ('sync',),
        ])
        self.assertEqual(backend.held_keycodes, {'CTRL':1})

        backend.d.sync = lambda: events.append(('sync_release',))
        with patch('runtime.backends.x11_v1.backend.xtest.fake_input',
                   side_effect=lambda _display, kind, code: events.append(
                       ('emit_release', kind, code))):
            backend.key_state('CTRL', False)
        self.assertEqual(events[-3:], [
            ('emit_release', X.KeyRelease, 1),
            ('sync_release',),
            ('snapshot', {}, []),
        ])
        self.assertEqual(backend.held_keycodes, {})

    def test_x11_backend_publishes_button_obligation_before_sync_can_block(self):
        events = []
        backend = object.__new__(X11Backend)
        backend.d = SimpleNamespace(sync=lambda: events.append(('sync',)))
        backend.held_keycodes = {}
        backend.held_buttons = set()
        backend.emissions = 0
        backend._before_input_press = lambda: None
        backend._input_obligation_publisher = lambda keys, buttons: events.append(
            ('snapshot', dict(keys), list(buttons)))

        def blocked_sync():
            events.append(('sync',))
            raise OSError('simulated blocked XSync')

        backend.d.sync = blocked_sync
        with patch('runtime.backends.x11_v1.backend.xtest.fake_input',
                   side_effect=lambda _display, kind, code: events.append(
                       ('emit', kind, code))):
            with self.assertRaisesRegex(OSError, 'simulated blocked XSync'):
                backend.pointer_button('left', True)

        self.assertEqual(events, [
            ('snapshot', {}, ['left']),
            ('emit', X.ButtonPress, 1),
            ('sync',),
        ])
        self.assertEqual(backend.held_buttons, {'left'})

    def test_retired_owner_with_invalid_live_ledger_does_not_release_stale_cache(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner._owner_input_obligations = {'keys':{}, 'buttons':[]}
        owner._owner_input_obligations_source = 'child_rpc_snapshot'
        owner._owner_input_obligations_state = multiprocessing.get_context(
            'spawn').RawArray('B', 8192)
        owner._owner_client_disconnect = None
        owner._owner_release_attempt = None
        owner._observe_owner_client_disconnect = Mock(return_value={
            'status':'disconnected', 'worker_retired':True,
        })
        owner._release_retired_owner_inputs = Mock()

        client, release = owner._cleanup_after_owner_retirement({'retired':True})

        self.assertEqual(client['status'], 'disconnected')
        self.assertEqual(owner._owner_input_obligations_live_read['status'], 'unknown')
        self.assertEqual(owner._owner_input_obligations_source, 'child_rpc_snapshot')
        owner._release_retired_owner_inputs.assert_not_called()
        self.assertEqual(release['status'], 'not_attempted')
        self.assertEqual(release['reason'], 'owner_input_obligations_unavailable')

    def test_prestarted_cleanup_retains_worker_request_validation_fields(self):
        shared = multiprocessing.get_context('spawn').RawArray('B', 8192)
        _write_test_obligation_state(shared, {
            'schema':'agent-interface/owner-input-obligations-v1',
            'keys':{'a':38}, 'buttons':[],
        })
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner._prestarted_cancel_enabled = True
        owner._prestarted_cleanup_result = None
        owner._owner_input_obligations_state = shared
        owner._owner_input_obligations = {'keys':{}, 'buttons':[]}
        owner._owner_input_obligations_source = 'child_rpc_snapshot'
        owner._cleanup_supervisor = Mock()
        owner._cleanup_supervisor.run.return_value = {
            'status':'unknown', 'reason':'invalid_cleanup_request',
            'invalid_fields':['owner_pid'], 'worker_retired':True,
        }
        owner._process = Mock()
        owner._process.pid = 1234
        owner._active_cancel_deadline_ns = time.monotonic_ns() + 1_000_000_000
        owner._active_cancel_operation_id = 'operation-1'
        owner.session_id = 'session-1'
        owner.binding_revision = 0
        owner.display_name = ':88'
        owner._snapshot_cache = {
            # The refreshed child snapshot may omit the parent-owned process
            # record. Do not build owner-generation PID from that cache.
            'owner_process_pid':9999,
            'owner_x_client_resource_base':6291456,
        }
        owner._owner_root = Path(tempfile.gettempdir())

        client, release = owner._cleanup_after_owner_retirement(
            {'retired':True, 'exitcode':-15})

        self.assertEqual(client['reason'], 'invalid_cleanup_request')
        self.assertEqual(client['invalid_fields'], ['owner_pid'])
        self.assertEqual(release['invalid_fields'], ['owner_pid'])
        self.assertFalse(client.get('release_confirmed', False))
        request = owner._cleanup_supervisor.run.call_args.args[0]
        self.assertTrue(request['owner_process_retired'])
        self.assertEqual(request['owner_process_exitcode'], -15)
        self.assertEqual(request['owner_pid'], 1234)
        self.assertEqual(request['owner_generation']['child_pid'], 1234)

    def test_retired_owner_rejects_torn_live_ledger_checksum(self):
        shared = multiprocessing.get_context('spawn').RawArray('B', 8192)
        _write_test_obligation_state(shared, {
            'schema':'agent-interface/owner-input-obligations-v1',
            'keys':{'CTRL':1}, 'buttons':[],
        })
        shared[40] ^= 1

        owner = object.__new__(OwnedGuardedSessionOwner)
        owner._owner_input_obligations = {'keys':{}, 'buttons':[]}
        owner._owner_input_obligations_source = 'child_rpc_snapshot'
        owner._owner_input_obligations_state = shared
        owner._owner_client_disconnect = None
        owner._owner_release_attempt = None
        owner._observe_owner_client_disconnect = Mock(return_value={
            'status':'disconnected', 'worker_retired':True,
        })
        owner._release_retired_owner_inputs = Mock()

        owner._cleanup_after_owner_retirement({'retired':True})

        self.assertEqual(owner._owner_input_obligations_live_read, {
            'status':'unknown', 'reason':'shared_state_checksum_invalid',
        })
        owner._release_retired_owner_inputs.assert_not_called()

    def test_disconnect_observer_binds_xres_query_to_owned_process_pid(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner.display_name = ':17'
        owner._snapshot_cache = {
            'owner_x_client_resource_base': 0x1200000,
            'owner_process_pid': 2750,
        }

        def query_owner(display_name, resource_base, *, expected_pid,
                        timeout_s, terminate_grace_s):
            if (display_name, resource_base, expected_pid) == (
                    ':17', 0x1200000, 2750):
                return {'status':'disconnected', 'expected_pid':expected_pid}
            return {'status':'unknown', 'expected_pid':expected_pid}

        with patch(
                'runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                side_effect=query_owner):
            result = owner._observe_owner_client_disconnect()

        self.assertEqual(result, {'status':'disconnected', 'expected_pid':2750})

    def test_cancel_retires_owner_when_response_keeps_input_and_late_request_possible(self):
        obligations = {'keys':{'a':38}, 'buttons':[]}
        disconnect = {'status':'disconnected', 'expected_pid':1234,
                      'worker_retired':True}
        release = {'status':'readback_verified',
                   'release':{'verified':True, 'keys_down':[],
                              'buttons_down':[]}}
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner._process = Mock()
        owner._process.is_alive.return_value = True
        owner._control = Mock()
        owner._control.poll.return_value = True
        owner._control.recv.return_value = {
            'ok':True,
            'snapshot':{'owner_input_obligations':obligations},
            'result':{
                'status':'cancel_requested',
                'owner_process_retired':False,
                'owner_input_obligations':obligations,
                'release_confirmed':False,
                'late_server_request_possible':True,
                'task_success':None,
                'replay_allowed':False,
            },
        }
        owner._control_lock = threading.Lock()
        owner._rpc_lock = Mock()
        owner._snapshot_cache = {}
        owner._owner_input_obligations = obligations
        owner._owner_input_obligations_source = 'child_rpc_snapshot'
        owner._owner_input_obligations_result_fields = Mock(return_value={
            'owner_input_obligations':obligations,
            'owner_input_obligations_source':'retired_child_shared_state',
            'owner_input_obligations_live_read':{
                'status':'snapshot', 'obligations':obligations,
            },
        })
        owner._apply_snapshot = Mock()
        owner._retire = Mock(return_value={'retired':True, 'exitcode':-15})
        owner._cleanup_after_owner_retirement = Mock(
            return_value=(disconnect, release))
        owner._execution_unknown = False
        owner.review_required = False

        result = owner.cancel_guarded('cancel-token')

        owner._rpc_lock.acquire.assert_not_called()
        owner._retire.assert_called_once()
        owner._cleanup_after_owner_retirement.assert_called_once_with(
            {'retired':True, 'exitcode':-15})
        self.assertTrue(owner._execution_unknown)
        self.assertTrue(owner.review_required)
        self.assertTrue(result['owner_process_retired'])
        self.assertEqual(result['owner_client_disconnect'], disconnect)
        self.assertEqual(result['owner_release_attempt'], release)
        self.assertFalse(result['release_confirmed'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])
        self.assertTrue(result['late_server_request_possible'])

    def test_unconfirmed_cancel_wait_is_capped_by_cancel_response_budget(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner._process = Mock()
        owner._process.is_alive.return_value = True
        owner._control = Mock()
        owner._control.poll.return_value = False
        owner._control_lock = threading.Lock()
        owner._snapshot_cache = {}
        owner._owner_input_obligations = {'keys':{}, 'buttons':[]}
        owner._owner_input_obligations_source = 'parent_initial_state'
        owner._owner_input_obligations_live_read = {'status':'not_read'}
        owner._retire = Mock(return_value={'retired':True, 'exitcode':-15})
        owner._cleanup_after_owner_retirement = Mock(return_value=(
            {'status':'disconnected'}, {'status':'readback_verified'}))
        owner._execution_unknown = False
        owner.review_required = False

        result = owner.cancel_guarded('cancel-token')

        self.assertLessEqual(owner._control.poll.call_args.args[0], 0.25)
        self.assertEqual(result['status'], 'cancel_unconfirmed')
        self.assertFalse(result['release_confirmed'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_unconfirmed_cancel_retires_exact_owner_without_claiming_release(self):
        responses = (
            ('timeout', False, None),
            ('pipe_closed', True, EOFError('closed')),
            ('negative_ack', True, {'ok':False, 'error':'rejected'}),
        )
        for name, has_response, response in responses:
            with self.subTest(name=name):
                owner = object.__new__(OwnedGuardedSessionOwner)
                owner._process = Mock()
                owner._process.is_alive.return_value = True
                owner._control = Mock()
                owner._control.poll.return_value = has_response
                if isinstance(response, BaseException):
                    owner._control.recv.side_effect = response
                elif response is not None:
                    owner._control.recv.return_value = response
                owner._control_lock = threading.Lock()
                owner._snapshot_cache = {}
                owner._execution_unknown = False
                owner.review_required = False
                owner._retire = Mock(return_value={'retired':True, 'exitcode':-15})

                with patch('runtime.cli_v1.owned_guarded_session._CANCEL_CONTROL_RESPONSE_TIMEOUT_S', 0):
                    result = owner.cancel_guarded('cancel-token')

                owner._retire.assert_called_once_with(
                    'cancel control response unconfirmed')
                self.assertEqual(result['status'], 'cancel_unconfirmed')
                self.assertTrue(result['owner_process_retired'])
                self.assertEqual(result['owner_process_exitcode'], -15)
                self.assertFalse(result['release_confirmed'])
                self.assertEqual(result['cleanup_status'], 'UNKNOWN')
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
                self.assertTrue(result['late_server_request_possible'])

    def test_unconfirmed_cancel_attempts_only_disconnect_gated_best_effort_cleanup(self):
        responses = (
            ('timeout', False, None),
            ('pipe_closed', True, EOFError('closed')),
            ('negative_ack', True, {'ok':False, 'error':'rejected'}),
        )
        obligations = {'keys':{'CTRL':1}, 'buttons':[]}
        stale_obligations = {'keys':{}, 'buttons':[]}
        for name, has_response, response in responses:
            for disconnect_status in ('disconnected', 'still_connected', 'unknown'):
                with self.subTest(name=name, disconnect_status=disconnect_status):
                    owner = object.__new__(OwnedGuardedSessionOwner)
                    owner._process = Mock()
                    owner._process.is_alive.return_value = True
                    owner._control = Mock()
                    owner._control.poll.return_value = has_response
                    if isinstance(response, BaseException):
                        owner._control.recv.side_effect = response
                    elif response is not None:
                        owner._control.recv.return_value = response
                    owner._control_lock = threading.Lock()
                    owner._execution_unknown = False
                    owner.review_required = False
                    owner._owner_input_obligations = stale_obligations
                    owner._owner_client_disconnect = None
                    owner._owner_release_attempt = None
                    owner._owner_input_obligations_state = multiprocessing.get_context(
                        'spawn').RawArray('B', 8192)
                    _write_test_obligation_state(
                        owner._owner_input_obligations_state, {
                            'schema':'agent-interface/owner-input-obligations-v1',
                            'keys':obligations['keys'], 'buttons':obligations['buttons']})
                    events = []
                    owner._retire = Mock(side_effect=lambda _reason: (
                        events.append('retire') or {'retired':True, 'exitcode':-15}))
                    owner._observe_owner_client_disconnect = Mock(side_effect=lambda: (
                        events.append('disconnect') or {
                            'status':disconnect_status, 'worker_retired':True}))
                    owner._release_retired_owner_inputs = Mock(side_effect=lambda seen: (
                        events.append(('release', seen)) or {
                            'status':'readback_verified', 'worker_retired':True}))

                    with patch('runtime.cli_v1.owned_guarded_session._CANCEL_CONTROL_RESPONSE_TIMEOUT_S', 0):
                        result = owner.cancel_guarded('cancel-token')

                    owner._retire.assert_called_once_with(
                        'cancel control response unconfirmed')
                    owner._observe_owner_client_disconnect.assert_called_once_with()
                    if disconnect_status == 'disconnected':
                        owner._release_retired_owner_inputs.assert_called_once_with(obligations)
                        self.assertEqual(events, ['retire', 'disconnect', ('release', obligations)])
                        self.assertEqual(result['owner_release_attempt']['status'],
                                         'readback_verified')
                    else:
                        owner._release_retired_owner_inputs.assert_not_called()
                        self.assertEqual(events, ['retire', 'disconnect'])
                        self.assertEqual(result['owner_release_attempt']['status'],
                                         'not_attempted')
                    self.assertEqual(result['owner_client_disconnect']['status'],
                                     disconnect_status)
                    self.assertEqual(result['owner_input_obligations'], obligations)
                    self.assertEqual(result['owner_input_obligations_source'],
                                     'retired_child_shared_state')
                    self.assertEqual(result['owner_input_obligations_live_read'], {
                        'status':'snapshot', 'obligations':obligations,
                    })
                    self.assertFalse(result['release_confirmed'])
                    self.assertEqual(result['cleanup_status'], 'UNKNOWN')
                    self.assertIsNone(result['task_success'])
                    self.assertFalse(result['replay_allowed'])
                    self.assertTrue(result['late_server_request_possible'])

    def test_unknown_or_present_owner_client_never_starts_release_worker(self):
        for disconnect_status in ('still_connected', 'unknown'):
            with self.subTest(disconnect_status=disconnect_status):
                owner = object.__new__(OwnedGuardedSessionOwner)
                owner._process = Mock()
                owner._process.is_alive.return_value = True
                owner._control = Mock()
                owner._control.poll.return_value = True
                owner._control.recv.return_value = {
                    'ok':True, 'snapshot':{},
                    'result':{'status':'cancel_requested'},
                }
                owner._control_lock = threading.Lock()
                owner._rpc_lock = threading.Lock()
                owner._rpc_lock.acquire()
                owner._apply_snapshot = lambda _snapshot: None
                owner._retire = Mock(return_value={'retired':True, 'exitcode':-15})
                owner._observe_owner_client_disconnect = Mock(return_value={
                    'status':disconnect_status, 'worker_retired':True,
                })
                owner._owner_input_obligations = {'keys':{'CTRL':1}, 'buttons':[]}
                owner._owner_client_disconnect = None
                owner._owner_release_attempt = None
                owner._execution_unknown = False
                owner.review_required = False
                owner._release_retired_owner_inputs = Mock()

                with patch('runtime.cli_v1.owned_guarded_session._CANCEL_RETIRE_GRACE_S', 0):
                    result = owner.cancel_guarded('cancel-token')

                owner._release_retired_owner_inputs.assert_not_called()
                self.assertEqual(result['owner_release_attempt']['status'],
                                 'not_attempted')
                self.assertFalse(result['release_confirmed'])
                self.assertEqual(result['cleanup_status'], 'UNKNOWN')
                self.assertFalse(result['replay_allowed'])

    def test_owned_process_selection_requires_identity_and_query_worker(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)/'not-created'
            for options in ({}, {'guarded_process_identity':True},
                            {'guarded_process_identity':True,'guarded_query_worker':True,
                             'session_mode':'persistent-x11'}):
                with self.subTest(options=options), self.assertRaises(ValueError):
                    create_server({'app':20}, output,
                                  guarded_owned_process=True, **options)
            self.assertFalse(output.exists())

    def test_cli_forwards_owned_process_selection(self):
        with tempfile.TemporaryDirectory() as td:
            targets = Path(td)/'targets.json'
            output = Path(td)/'out'
            targets.write_text('{"app":20}', encoding='utf-8')
            argv = ['server','--targets',str(targets),'--output-directory',str(output),
                    '--session-mode','guarded-x11','--guarded-process-identity',
                    '--guarded-query-worker','--guarded-owned-process',
                    '--guarded-prestarted-cancel-supervisor',
                    '--guarded-retention-mode','journal']
            with patch('sys.argv', argv), patch(
                    'runtime.cli_v1.mcp_server.create_server') as create:
                main()
            create.assert_called_once_with({'app':20}, output, display_name=None,
                session_mode='guarded-x11', guarded_process_identity=True,
                guarded_query_worker=True, guarded_owned_process=True,
                guarded_retention_mode='journal',
                guarded_prestarted_cancel_supervisor=True)
            create.return_value.run.assert_called_once_with(transport='stdio')

    def test_cli_prestarted_supervisor_requires_owned_process(self):
        with tempfile.TemporaryDirectory() as td:
            targets = Path(td)/'targets.json'
            output = Path(td)/'out'
            targets.write_text('{"app":20}', encoding='utf-8')
            argv = ['server','--targets',str(targets),'--output-directory',str(output),
                    '--session-mode','guarded-x11','--guarded-prestarted-cancel-supervisor']
            with patch('sys.argv', argv), patch('sys.stderr', new_callable=io.StringIO), \
                    self.assertRaises(SystemExit) as raised:
                main()
            self.assertEqual(raised.exception.code, 2)
            self.assertFalse(output.exists())

    async def test_public_observe_preserves_unconfirmed_retirement_as_null(self):
        with tempfile.TemporaryDirectory() as directory:
            owners=[];original=OwnedGuardedSessionOwner.__init__
            def capture(owner,*args,**kwargs):
                original(owner,*args,**kwargs);owners.append(owner)
            with patch.object(OwnedGuardedSessionOwner,'__init__',capture):
                server=create_server({'app':20},directory,session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,
                    guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                first=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(first['status'],'observed')
                owners[0]._retirement={'retired':False,'exitcode':None,'reason':'unconfirmed'}
                second=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(second['status'],'observed')
                self.assertIsNone(second['session']['owner_process']['retired'])
            finally:
                await server.call_tool('interface_close',{})

    async def test_standard_guarded_tools_keep_generation_and_input_in_owned_process(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server(
                {'app':20}, td, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed_response = await server.call_tool('interface_guarded_observe', {})
                observed = metadata(observed_response)
                self.assertEqual(observed['status'], 'observed', observed)
                self.assertEqual(observed['source']['pointer_binding']['process_generation'], 'a'*64)
                owner_process = observed['session']['owner_process']
                self.assertNotEqual(owner_process['pid'], os.getpid())
                self.assertTrue(owner_process['alive'])
                self.assertEqual(owner_process['x_client_resource_base'], 0x1200000)

                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                self.assertEqual(minted['status'], 'minted', minted)
                action = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False, tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(action['status'], 'completed', action)
                self.assertTrue(action['result']['execution']['releases'][-1]['verified'])
                self.assertIsNone(action['task_success'])

                closed = metadata(await server.call_tool('interface_close', {}))
                if closed.get('status') == 'busy':
                    # The worker slot can be released just after its result is
                    # delivered. Busy is a no-op; retry close explicitly.
                    await asyncio.sleep(0.01)
                    closed = metadata(await server.call_tool('interface_close', {}))
                self.assertTrue(closed.get('verified'), closed)
                self.assertEqual(closed['status'], 'closed', closed)
                self.assertFalse(closed['session']['owner_process']['alive'], closed)
                self.assertEqual(closed['session']['state'], 'closed')
                self.assertFalse(observed['session']['owner_process']['pid'] == os.getpid())
            finally:
                await server.call_tool('interface_close', {})

    async def test_standard_compiled_profile_uses_generation_bound_owned_caller(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'compiled-profile-mode').write_text('enabled')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,guarded_retention_mode='journal',
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(observed['source']['pointer_binding']['process_generation'],'a'*64)
                self.assertTrue(observed['session']['compiled_scope'])
                self.assertEqual(observed['session']['retention_mode'],'journal')
                minted=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='field',source_sequence=observed['source']['sequence'],
                    point=[8,8],region_size=[12,12])))
                payload=_compiled_profile_payload(observed['session']['compiled_scope'],
                    observed['session']['compiled_surface'],minted['offset'])
                payload['wait_for_result_ms']=10000
                result=metadata(await server.call_tool('interface_guarded_compiled',payload))
                self.assertEqual(result['method_receipt']['outcome'],'TASK_SUCCEEDED',result)
                self.assertEqual(result['method_receipt']['completed_transitions'],1)
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
                self.assertEqual(result['session']['owner_process']['pid'],observed['session']['owner_process']['pid'])
                self.assertTrue((Path(result['call_directory'])/'compiled'/'owner-attempt-timing.json').is_file())
                lookup=metadata(await server.call_tool('interface_results',{'call_id':result['call_id']}))
                self.assertEqual(lookup['method_receipt'],result['method_receipt'])
                self.assertIsNone(lookup['task_success'])
                closed=metadata(await server.call_tool('interface_close',{}))
                if closed.get('status') == 'busy':
                    await asyncio.sleep(0.01)
                    closed=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(closed['status'],'closed',closed)
                from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal
                journal_path=(root/('guarded-session-'+observed['session']['session_id'])
                              /'retention.jsonl')
                with ReceiptJournal(journal_path) as journal:
                    refs=journal.references()
                    execution_refs=[ref for ref in refs if ref.endswith('-execution')]
                    self.assertEqual(len(execution_refs),1,refs)
                    execution=journal.lookup(execution_refs[0])
                    self.assertTrue(execution['action_id'])
                    self.assertTrue(execution['result']['execution']['releases'][-1]['verified'])
                    self.assertIn('session-close',refs)
                    close_report=journal.lookup('session-close')
                    self.assertTrue(close_report['release']['verified'])
            finally:
                await server.call_tool('interface_close',{})
                _preserve_fake_x_run(
                    'standard-compiled-success',root)

    async def test_compiled_profile_stops_mid_action_on_process_generation_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'compiled-profile-mode').write_text('enabled')
            (root/'compiled-flip-generation-after-input').write_text('enabled')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                minted=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='field',source_sequence=observed['source']['sequence'],
                    point=[8,8],region_size=[12,12])))
                payload=_compiled_profile_payload(observed['session']['compiled_scope'],
                    observed['session']['compiled_surface'],minted['offset'])
                payload['wait_for_result_ms']=10000
                result=metadata(await server.call_tool('interface_guarded_compiled',payload))
                self.assertEqual((root/'fake-process-generation').read_text(), 'b'*64)
                self.assertNotEqual(result['method_receipt']['outcome'],'TASK_SUCCEEDED',result)
                self.assertEqual(result['method_receipt']['completed_transitions'],0)
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
                retained=metadata(await server.call_tool('interface_results',
                    {'call_id':result['call_id']}))
                self.assertNotEqual(retained['method_receipt']['outcome'],'TASK_SUCCEEDED')
                self.assertIsNone(retained['task_success'])
            finally:
                await server.call_tool('interface_close',{})
                _preserve_fake_x_run(
                    'generation-change-refusal',root)

    async def test_owned_process_refuses_alias_after_target_generation_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server = create_server(
                {'app':20}, root, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True, guarded_retention_mode='journal',
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                self.assertEqual(observed['source']['pointer_binding']['process_generation'], 'a'*64)
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                self.assertEqual(minted['status'], 'minted', minted)

                (root/'fake-process-generation').write_text('b'*64, encoding='utf-8')
                result = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )

                self.assertEqual(result['status'], 'refused', result)
                self.assertFalse(result['result']['input_dispatched'], result)
                self.assertEqual(result['result']['guard_checks'][0]['reason'],
                                 'process_generation_changed_or_missing', result)
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
            finally:
                await server.call_tool('interface_close', {})

    async def test_cancel_retires_exact_blocked_owner_but_keeps_release_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server = create_server(
                {'app':20}, root, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True, guarded_retention_mode='journal',
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                (root/'block-owner-io').write_text('block', encoding='utf-8')
                pending = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False, wait_for_result_ms=0,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(pending['status'], 'pending', pending)
                deadline = time.monotonic() + 3
                while not (root/'owner-io-entered.json').exists() and time.monotonic() < deadline:
                    await asyncio.sleep(0.005)
                self.assertTrue((root/'owner-io-entered.json').exists())
                self.assertEqual(json.loads((root/'owner-io-entered.json').read_text()), [1])

                fence_result = {'status':'disconnected', 'worker_retired':True,
                                'elapsed_ms':2.5}
                release_result = {'status':'readback_verified',
                                   'release':{'verified':True, 'keys_down':[],
                                              'buttons_down':[], 'monotonic_ns':12}}
                with (patch('runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                            return_value=fence_result),
                      patch('runtime.cli_v1.owned_guarded_session.OwnedGuardedSessionOwner._release_retired_owner_inputs',
                            return_value=release_result) as release_inputs):
                    cancel_started = time.monotonic()
                    cancel = metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))
                    self.assertLess(time.monotonic() - cancel_started, 0.45, cancel)
                    if 'owner_process_retired' in cancel:
                        cleanup = cancel
                    else:
                        self.assertEqual(cancel['status'], 'pending', cancel)
                        self.assertFalse(cancel['release_confirmed'], cancel)
                        cancellation_terminal = await self._wait_for_cancel_terminal(
                            server, pending['call_id'])
                        cleanup = cancellation_terminal['cancellation']['result']
                self.assertTrue(cleanup['owner_process_retired'], cleanup)
                self.assertEqual(cleanup.get('owner_client_disconnect'), fence_result)
                self.assertEqual(cleanup.get('owner_input_obligations'),
                                 {'keys':{'CTRL':1}, 'buttons':[]})
                self.assertEqual(cleanup.get('owner_input_obligations_source'),
                                 'retired_child_shared_state')
                self.assertEqual(cleanup.get('owner_input_obligations_live_read'), {
                    'status':'snapshot',
                    'obligations':{'keys':{'CTRL':1}, 'buttons':[]},
                })
                self.assertEqual(cleanup.get('owner_release_attempt'), release_result)
                release_inputs.assert_called_once_with({'keys':{'CTRL':1}, 'buttons':[]})
                self.assertFalse(cleanup['release_confirmed'])
                self.assertEqual(cleanup['cleanup_status'], 'UNKNOWN')
                self.assertTrue(cleanup['late_server_request_possible'])

                deadline = time.monotonic() + 3
                terminal = None
                while time.monotonic() < deadline:
                    terminal = metadata(await server.call_tool('interface_results',
                        {'call_id':pending['call_id'], 'include_image':False}))
                    if terminal['status'] != 'pending':
                        break
                    await asyncio.sleep(0.005)
                self.assertEqual(terminal['status'], 'runtime_failed', terminal)
                self.assertFalse(terminal['release_confirmed'])
                self.assertEqual(terminal['cleanup_status'], 'UNKNOWN')
                self.assertIsNone(terminal['task_success'])
                self.assertFalse(terminal['replay_allowed'])
                self.assertEqual(json.loads((root/'owner-io-entered.json').read_text()), [1])
                from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal
                journal_path=(root/('guarded-session-'+observed['session']['session_id'])
                              /'retention.jsonl')
                with ReceiptJournal(journal_path) as journal:
                    refs=journal.references()
                    self.assertTrue(any(ref.startswith('observation-') for ref in refs), refs)
                    self.assertIn('mint-field', refs)
                    self.assertFalse(any(ref.endswith('-execution') for ref in refs), refs)
                    self.assertNotIn('session-close', refs)
            finally:
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_compiled_call_cancel_retires_owner_during_blocked_platform_sync(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'compiled-profile-mode').write_text('enabled')
            server=create_server({'app':20},root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                minted=metadata(await server.call_tool('interface_guarded_mint',dict(
                    alias='field',source_sequence=observed['source']['sequence'],
                    point=[8,8],region_size=[12,12])))
                payload=_compiled_profile_payload(observed['session']['compiled_scope'],
                    observed['session']['compiled_surface'],minted['offset'])
                payload['wait_for_result_ms']=0
                (root/'block-owner-io').write_text('block',encoding='utf-8')
                pending=metadata(await server.call_tool('interface_guarded_compiled',payload))
                self.assertEqual(pending['status'],'pending',pending)
                deadline=time.monotonic()+3
                while not (root/'owner-io-entered.json').exists() and time.monotonic()<deadline:
                    await asyncio.sleep(.005)
                self.assertTrue((root/'owner-io-entered.json').exists())
                self.assertEqual(json.loads((root/'owner-io-entered.json').read_text()),[1])
                fence_result={'status':'disconnected','worker_retired':True,'elapsed_ms':2.5}
                release_result={'status':'unknown','reason':'fake_transport_has_no_live_readback',
                                'worker_retired':True}
                with (patch('runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                            return_value=fence_result),
                      patch('runtime.cli_v1.owned_guarded_session.OwnedGuardedSessionOwner._release_retired_owner_inputs',
                            return_value=release_result) as release_inputs):
                    cancel=metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))
                release_inputs.assert_called_once_with({'keys':{'CTRL':1},'buttons':[]})
                self.assertTrue(cancel['owner_process_retired'],cancel)
                self.assertEqual(cancel.get('owner_client_disconnect'),fence_result)
                self.assertEqual(cancel.get('owner_input_obligations'),
                                 {'keys':{'CTRL':1},'buttons':[]})
                self.assertEqual(cancel.get('owner_release_attempt'),release_result)
                self.assertFalse(cancel['release_confirmed'])
                self.assertEqual(cancel['cleanup_status'],'UNKNOWN')
                self.assertTrue(cancel['late_server_request_possible'])
                # The cancellation receipt is immediate, while the server call
                # record becomes terminal only after its worker observes owner
                # retirement. Let the fake transport unwind, then bound that wait.
                (root/'resume-owner-io').write_text('resume',encoding='utf-8')
                deadline=time.monotonic()+2
                terminal=None
                while time.monotonic()<deadline:
                    terminal=metadata(await server.call_tool('interface_results',
                        {'call_id':pending['call_id'],'include_image':False}))
                    if terminal['status'] != 'pending':
                        break
                    await asyncio.sleep(.01)
                self.assertIsNotNone(terminal)
                self.assertNotEqual(terminal['status'],'pending',terminal)
                self.assertIsNone(terminal['task_success'])
                self.assertFalse(terminal['replay_allowed'])
            finally:
                (root/'resume-owner-io').write_text('resume',encoding='utf-8')
                await server.call_tool('interface_close',{})
                _preserve_fake_x_run(
                    'cancel-blocked-platform-sync',root)

    async def test_cancel_returns_unknown_when_separate_release_worker_blocks(self):
        """Bound caller recovery under a synthetic platform-I/O block; infer no release."""
        from runtime.guarded_x11_v1.xres_client_fence import supervise_xres_worker

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server = create_server(
                {'app':20}, root, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)
            try:
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                (root/'block-owner-io').write_text('block', encoding='utf-8')
                pending = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False, wait_for_result_ms=0,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(pending['status'], 'pending', pending)
                deadline = time.monotonic() + 3
                while not (root/'owner-io-entered.json').exists() and time.monotonic() < deadline:
                    await asyncio.sleep(0.005)
                self.assertTrue((root/'owner-io-entered.json').exists())
                self.assertEqual(json.loads((root/'owner-io-entered.json').read_text()), [1])

                fence = {'status':'disconnected', 'worker_retired':True,
                         'elapsed_ms':1.0}

                def supervise_blocked_release(_target, _args, **kwargs):
                    self.assertEqual(_target.__name__, '_release_retired_inputs_worker')
                    self.assertEqual(_args[1:], ({'CTRL':1}, []))
                    self.assertEqual(kwargs['timeout_s'], 1.5)
                    self.assertEqual(kwargs['terminate_grace_s'], 0.25)
                    self.assertEqual(kwargs['accepted_statuses'], ('released', 'unknown'))
                    return supervise_xres_worker(
                        _blocked_release_worker, (), timeout_s=kwargs['timeout_s'],
                        terminate_grace_s=kwargs['terminate_grace_s'],
                        accepted_statuses=kwargs['accepted_statuses'])

                started = time.monotonic()
                # Force a short event-loop stall just before the public deadline.
                asyncio.get_running_loop().call_later(0.290, time.sleep, 0.020)
                heartbeats = []
                async def heartbeat():
                    for _ in range(100):
                        heartbeats.append(time.monotonic_ns())
                        await asyncio.sleep(0.01)
                heartbeat_task = asyncio.create_task(heartbeat())
                with (patch('runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                            return_value=fence),
                      patch('runtime.cli_v1.owned_guarded_session.supervise_xres_worker',
                            side_effect=supervise_blocked_release) as release_supervisor):
                    cancel = metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))
                    elapsed = time.monotonic() - started
                    self.assertLess(elapsed, 0.30, cancel)
                    self.assertEqual(cancel['status'], 'pending', cancel)
                    self.assertTrue(cancel['operation_id'], cancel)
                    self.assertFalse(cancel['release_confirmed'])
                    self.assertIsNone(cancel['task_success'])
                    self.assertFalse(cancel['replay_allowed'])
                    pending_result = metadata(await server.call_tool('interface_results',
                        {'call_id':pending['call_id'], 'include_image':False}))
                    self.assertEqual(pending_result['status'], 'runtime_failed', pending_result)
                    self.assertEqual(pending_result['cancellation']['operation_id'],
                                     cancel['operation_id'])
                    self.assertEqual(pending_result['cancellation']['status'], 'pending')
                    self.assertIsNone(pending_result['task_success'])
                    self.assertFalse(pending_result['replay_allowed'])
                    duplicate = metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))
                    self.assertEqual(duplicate['operation_id'], cancel['operation_id'])
                    self.assertEqual(duplicate['status'], 'pending')

                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        pending_result = metadata(await server.call_tool('interface_results',
                            {'call_id':pending['call_id'], 'include_image':False}))
                        if pending_result['cancellation']['status'] != 'pending':
                            break
                        await asyncio.sleep(0.01)
                    self.assertEqual(pending_result['status'], 'runtime_failed', pending_result)
                    self.assertEqual(pending_result['cancellation']['status'], 'completed', pending_result)
                    self.assertNotIn('persistence_failure', pending_result['cancellation'], pending_result)
                    cancel = pending_result['cancellation']['result']
                    release_supervisor.assert_called_once()
                    await heartbeat_task
                    self.assertGreaterEqual(len(heartbeats), 50)
                    heartbeat_gaps_ms = [(right-left)/1_000_000
                        for left, right in zip(heartbeats, heartbeats[1:])]
                    self.assertLess(max(heartbeat_gaps_ms), 100.0)
                    retained_cancel = json.loads((root/pending['call_id']/'cancellation.json').read_text())
                    self.assertEqual(retained_cancel['status'], 'completed')
                    self.assertEqual(retained_cancel['result'], cancel)

                self.assertTrue(cancel['owner_process_retired'], cancel)
                self.assertEqual(cancel['owner_client_disconnect'], fence)
                self.assertEqual(cancel['owner_input_obligations'], {
                    'keys':{'CTRL':1}, 'buttons':[]})
                self.assertEqual(cancel['owner_release_attempt']['status'], 'unknown')
                self.assertEqual(cancel['owner_release_attempt']['reason'],
                                 'supervision_timeout')
                self.assertTrue(cancel['owner_release_attempt']['worker_retired'])
                self.assertFalse(cancel['release_confirmed'])
                self.assertEqual(cancel['cleanup_status'], 'UNKNOWN')
                self.assertIsNone(cancel['task_success'])
                self.assertFalse(cancel['replay_allowed'])
                self.assertTrue(cancel['late_server_request_possible'])

                self.assertEqual(pending_result['cancellation']['operation_id'],
                                 duplicate['operation_id'])
            finally:
                if 'heartbeat_task' in locals() and not heartbeat_task.done():
                    heartbeat_task.cancel()
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_cancel_request_cancellation_does_not_drop_owned_operation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server = create_server(
                {'app':20}, root, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)
            entered = threading.Event()
            finish = threading.Event()
            try:
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                (root/'block-owner-io').write_text('block', encoding='utf-8')
                action = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False, wait_for_result_ms=0,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(action['status'], 'pending', action)
                deadline = time.monotonic() + 3
                while not (root/'owner-io-entered.json').exists() and time.monotonic() < deadline:
                    await asyncio.sleep(0.005)
                self.assertTrue((root/'owner-io-entered.json').exists())

                def blocked_cancel(_call_id, **_kwargs):
                    entered.set()
                    if not finish.wait(3):
                        raise TimeoutError('test cancellation gate expired')
                    raise KeyboardInterrupt('synthetic cancellation worker interruption')

                with patch.object(OwnedGuardedSessionOwner, 'cancel_guarded',
                                  side_effect=blocked_cancel) as cancel_method:
                    request = asyncio.create_task(server.call_tool(
                        'interface_guarded_cancel', {'call_id':action['call_id']}))
                    deadline = time.monotonic() + 2
                    while not entered.is_set() and time.monotonic() < deadline:
                        await asyncio.sleep(0.005)
                    self.assertTrue(entered.is_set())
                    request.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await request

                    pending = metadata(await server.call_tool('interface_results', {
                        'call_id':action['call_id'], 'include_image':False}))
                    operation_id = pending['cancellation']['operation_id']
                    self.assertEqual(pending['cancellation']['status'], 'pending')
                    self.assertFalse(pending['cancellation']['replay_allowed'])
                    self.assertIsNone(pending['cancellation']['task_success'])

                    finish.set()
                    deadline = time.monotonic() + 2
                    while time.monotonic() < deadline:
                        terminal = metadata(await server.call_tool('interface_results', {
                            'call_id':action['call_id'], 'include_image':False}))
                        if terminal['cancellation']['status'] != 'pending':
                            break
                        await asyncio.sleep(0.005)
                    self.assertEqual(terminal['cancellation']['status'], 'unknown', terminal)
                    self.assertEqual(terminal['cancellation']['operation_id'], operation_id)
                    self.assertEqual(terminal['cancellation']['result']['status'],
                                     'cancel_unconfirmed')
                    self.assertFalse(terminal['cancellation']['release_confirmed'])
                    self.assertIsNone(terminal['cancellation']['task_success'])
                    self.assertFalse(terminal['cancellation']['replay_allowed'])

                    duplicate = metadata(await server.call_tool('interface_guarded_cancel', {
                        'call_id':action['call_id']}))
                    self.assertEqual(duplicate['operation_id'], operation_id)
                    self.assertEqual(duplicate['status'], 'cancel_unconfirmed')
                    cancel_method.assert_called_once()
                    retained = json.loads((root/action['call_id']/'cancellation.json').read_text())
                    self.assertEqual(retained['status'], 'unknown')
                    self.assertEqual(retained['operation_id'], operation_id)
                    self.assertEqual(retained['owner_generation'],
                                     terminal['cancellation']['owner_generation'])
                    self.assertEqual(retained['result']['status'], 'cancel_unconfirmed')
            finally:
                finish.set()
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                if 'action' in locals():
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        report = metadata(await server.call_tool('interface_results', {
                            'call_id':action['call_id'], 'include_image':False}))
                        if report.get('status') != 'pending':
                            break
                        await asyncio.sleep(0.01)
                await server.call_tool('interface_close', {})

    async def test_prearmed_cleanup_can_precede_retired_owners_queued_down(self):
        """A separate cleanup receipt is false if the old connection queue can arrive later."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_json(root/'fake-x-state.json', {'down':[]})
            server = create_server(
                {'app':20}, root, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_queued_fake_owner_factory)
            try:
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                (root/'block-owner-io').write_text('block', encoding='utf-8')
                pending = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False, wait_for_result_ms=0,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(pending['status'], 'pending', pending)
                deadline = time.monotonic() + 3
                while not (root/'owner-io-entered.json').exists() and time.monotonic() < deadline:
                    await asyncio.sleep(0.005)
                entered = _read_json(root/'owner-io-entered.json', {})
                self.assertEqual(entered['queued'], [{'kind':X.KeyPress, 'code':1}])
                self.assertEqual(entered['down'], [])

                cancelled = metadata(await server.call_tool('interface_guarded_cancel',
                    {'call_id':pending['call_id']}))
                self.assertTrue(cancelled['owner_process_retired'], cancelled)
                self.assertFalse(cancelled['release_confirmed'])
                self.assertTrue(cancelled['late_server_request_possible'])

                deadline = time.monotonic() + 3
                terminal = None
                while time.monotonic() < deadline:
                    terminal = metadata(await server.call_tool('interface_results',
                        {'call_id':pending['call_id'], 'include_image':False}))
                    if terminal['status'] != 'pending':
                        break
                    await asyncio.sleep(0.005)
                self.assertEqual(terminal['status'], 'runtime_failed', terminal)
                self.assertFalse(terminal['release_confirmed'])
                self.assertEqual(terminal['cleanup_status'], 'UNKNOWN')
                self.assertIsNone(terminal['task_success'])
                self.assertFalse(terminal['replay_allowed'])

                cleanup_display = _QueuedCleanupDisplay(root)
                cleanup_backend = object.__new__(X11Backend)
                cleanup_backend.d = cleanup_display
                cleanup_backend.root = SimpleNamespace(
                    query_pointer=lambda:SimpleNamespace(mask=0))
                cleanup_backend.held_keycodes = {'CTRL':1}
                cleanup_backend.held_buttons = set()
                cleanup_backend.emissions = 0

                def enqueue_cleanup(display, kind, code):
                    self.assertIs(display, cleanup_display)
                    queue_path = root/'cleanup-x-queue.json'
                    events = _read_json(queue_path, [])
                    events.append({'kind':kind, 'code':code})
                    _write_json(queue_path, events)

                with patch('runtime.backends.x11_v1.backend.xtest.fake_input',
                           side_effect=enqueue_cleanup):
                    release = X11Backend.release_all(cleanup_backend)
                self.assertTrue(release['verified'], release)
                self.assertEqual(release['keys_down'], [])
                self.assertEqual(_read_json(root/'fake-x-state.json', {})['down'], [])

                _apply_queued_child_requests(root)
                self.assertEqual(_read_json(root/'fake-x-state.json', {})['down'], [1])
            finally:
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_standard_cancel_keeps_unknown_after_release_readback_then_late_down(self):
        """A fresh client's empty readback cannot fence a retired client's queued press."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_json(root/'fake-x-state.json', {'down':[]})
            server = create_server(
                {'app':20}, root, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_queued_fake_owner_factory)
            try:
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                (root/'block-owner-io').write_text('block', encoding='utf-8')
                pending = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False, wait_for_result_ms=0,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(pending['status'], 'pending', pending)
                deadline = time.monotonic() + 3
                while not (root/'owner-io-entered.json').exists() and time.monotonic() < deadline:
                    await asyncio.sleep(0.005)
                entered = _read_json(root/'owner-io-entered.json', {})
                self.assertEqual(entered['queued'], [{'kind':X.KeyPress, 'code':1}])
                self.assertEqual(entered['down'], [])

                fence_result = {'status':'disconnected', 'worker_retired':True,
                                'elapsed_ms':2.5}
                observed_owner_pids = []

                def observe_owner(display_name, resource_base, *, expected_pid,
                                  timeout_s, terminate_grace_s):
                    observed_owner_pids.append(expected_pid)
                    return dict(fence_result, expected_pid=expected_pid)

                release_result = {'status':'readback_verified',
                                   'release':{'verified':True, 'keys_down':[],
                                              'buttons_down':[], 'monotonic_ns':12}}
                with (patch('runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                            side_effect=observe_owner),
                      patch('runtime.cli_v1.owned_guarded_session.OwnedGuardedSessionOwner._release_retired_owner_inputs',
                            return_value=release_result) as release_inputs):
                    cancelled = metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))

                self.assertTrue(cancelled['owner_process_retired'], cancelled)
                self.assertEqual(len(observed_owner_pids), 1)
                self.assertIs(type(observed_owner_pids[0]), int)
                self.assertGreater(observed_owner_pids[0], 0)
                self.assertEqual(cancelled['owner_client_disconnect'],
                                 dict(fence_result,
                                      expected_pid=observed_owner_pids[0]))
                release_inputs.assert_called_once_with({'keys':{'CTRL':1}, 'buttons':[]})
                self.assertEqual(cancelled['owner_release_attempt'], release_result)
                self.assertFalse(cancelled['release_confirmed'])
                self.assertEqual(cancelled['cleanup_status'], 'UNKNOWN')
                self.assertTrue(cancelled['late_server_request_possible'])
                self.assertFalse(cancelled['replay_allowed'])

                # The cleanup receipt describes an empty keymap before the
                # old connection's already-queued request is applied.
                self.assertEqual(_read_json(root/'fake-x-state.json', {})['down'], [])
                _apply_queued_child_requests(root)
                self.assertEqual(_read_json(root/'fake-x-state.json', {})['down'], [1])

                deadline = time.monotonic() + 3
                terminal = None
                while time.monotonic() < deadline:
                    terminal = metadata(await server.call_tool('interface_results',
                        {'call_id':pending['call_id'], 'include_image':False}))
                    if terminal['status'] != 'pending':
                        break
                    await asyncio.sleep(0.005)
                self.assertEqual(terminal['status'], 'runtime_failed', terminal)
                self.assertFalse(terminal['release_confirmed'])
                self.assertEqual(terminal['cleanup_status'], 'UNKNOWN')
                self.assertIsNone(terminal['task_success'])
                self.assertFalse(terminal['replay_allowed'])
            finally:
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def _start_prestarted_cancel_case(self, root):
        _write_json(root/'supervisor-fake-x.json', {'down':[1], 'effects':[], 'refused':[]})
        server = create_server(
            {'app':20}, root, session_mode='guarded-x11',
            guarded_process_identity=True, guarded_query_worker=True,
            guarded_owned_process=True,
            guarded_prestarted_cancel_supervisor=True,
            _guarded_cancel_supervisor_target=_fake_prestarted_cancel_worker,
            _guarded_owner_factory=_fake_owner_factory)
        observed = metadata(await server.call_tool('interface_guarded_observe', {}))
        minted = metadata(await server.call_tool('interface_guarded_mint', dict(
            alias='field', source_sequence=observed['source']['sequence'],
            point=[8,8], region_size=[12,12])))
        (root/'block-owner-io').write_text('block', encoding='utf-8')
        action = metadata(await server.call_tool('interface_guarded_input', dict(
            alias='field', offset=minted['offset'], interaction='keyboard',
            observe_after=False, wait_for_result_ms=0,
            tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
        self.assertEqual(action['status'], 'pending', action)
        deadline = time.monotonic() + 3
        while not (root/'owner-io-entered.json').exists() and time.monotonic() < deadline:
            await asyncio.sleep(0.005)
        self.assertTrue((root/'owner-io-entered.json').exists())
        return server, action

    async def _wait_for_cancel_terminal(self, server, call_id, timeout_s=4):
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            result = metadata(await server.call_tool('interface_results', {
                'call_id':call_id, 'include_image':False}))
            cancellation = result.get('cancellation')
            if cancellation and cancellation.get('status') != 'pending':
                return result
            await asyncio.sleep(0.01)
        self.fail('cancellation did not reach a terminal receipt before the test deadline')

    async def test_prestarted_supervisor_public_path_releases_once_but_keeps_runtime_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server, action = await self._start_prestarted_cancel_case(root)
            try:
                started = time.monotonic()
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {
                    'call_id':action['call_id']}))
                self.assertLess(time.monotonic() - started, 0.45, cancel)
                # Scheduling can consume the caller-response window. The
                # public contract then returns pending while the same operation
                # retains custody; retirement is asserted from its terminal
                # receipt below.
                self.assertIn(cancel['status'],
                              ('pending', 'cancel_unconfirmed', 'cancel_requested'),
                              cancel)
                duplicate = metadata(await server.call_tool(
                    'interface_guarded_cancel', {'call_id':action['call_id']}))
                self.assertEqual(duplicate['operation_id'], cancel['operation_id'])
                self.assertEqual(duplicate['cancellation']['operation_id'],
                                 cancel['operation_id'])
                self.assertFalse(cancel['release_confirmed'])
                self.assertIsNone(cancel['task_success'])
                self.assertFalse(cancel['replay_allowed'])
                result = await self._wait_for_cancel_terminal(
                    server, action['call_id'])
                public_call = result.get('retained_call', result.get('call', {}))
                self.assertNotIn('cancellation_archived', public_call)
                self.assertNotIn('cancellation_operation_id', public_call)
                cleanup = result['cancellation']['result']
                self.assertTrue(cleanup['owner_process_retired'], cleanup)
                terminal_duplicate = metadata(await server.call_tool(
                    'interface_guarded_cancel', {'call_id':action['call_id']}))
                self.assertEqual(terminal_duplicate['operation_id'],
                                 cancel['operation_id'])
                self.assertEqual(terminal_duplicate['cancellation']['operation_id'],
                                 cancel['operation_id'])
                self.assertEqual(terminal_duplicate['status'],
                                 result['cancellation']['result']['status'])
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'readback_verified', cleanup)
                self.assertFalse(cleanup['release_confirmed'])
                self.assertIsNone(cleanup['task_success'])
                self.assertFalse(cleanup['replay_allowed'])
                state = _read_json(root/'supervisor-fake-x.json', {})
                self.assertEqual(state['down'], [])
                self.assertEqual(len(state['effects']), 1)
                _retain_prestarted_trial('healthy-release', result, state,
                    response_seconds=time.monotonic() - started,
                    duplicate_operation_reused=(
                        duplicate['operation_id'] == cancel['operation_id']))
                operation = _read_json(root/'cleanup-supervisor-entered.json', {})
                self.assertEqual(operation['operation_id'], cancel['operation_id'])
                self.assertEqual(operation['session_id'],
                                 result['cancellation']['owner_generation']['session_id'])
            finally:
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_blocked_cancellation_receipt_archive_does_not_delay_release_or_caller(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server, action = await self._start_prestarted_cancel_case(root)
            from runtime.cli_v1.attempt import _write_json as write_json
            archive_entered = threading.Event()
            resume_archive = threading.Event()
            archive_payloads = []

            def block_cancellation_archive(path, value):
                if Path(path).name == 'cancellation.json':
                    archive_entered.set()
                    archive_payloads.append(json.loads(json.dumps(value)))
                    if not resume_archive.wait(5):
                        raise TimeoutError('test did not release the blocked archive')
                return write_json(path, value)

            heartbeat_ticks = []
            async def heartbeat():
                while True:
                    heartbeat_ticks.append(time.monotonic())
                    await asyncio.sleep(0.02)

            beat_task = asyncio.create_task(heartbeat())
            try:
                with patch('runtime.cli_v1.mcp_server._write_json',
                           side_effect=block_cancellation_archive):
                    started = time.monotonic()
                    cancel = metadata(await server.call_tool(
                        'interface_guarded_cancel', {'call_id':action['call_id']}))
                    response_s = time.monotonic() - started
                    self.assertLess(response_s, 0.45, cancel)
                    self.assertEqual(cancel['status'], 'pending', cancel)
                    self.assertFalse(cancel['release_confirmed'], cancel)
                    self.assertIsNone(cancel['task_success'], cancel)
                    self.assertFalse(cancel['replay_allowed'], cancel)

                    archive_started = await asyncio.to_thread(
                        archive_entered.wait, 2)
                    self.assertTrue(archive_started, 'terminal receipt write never blocked')
                    state = _read_json(root/'supervisor-fake-x.json', {})
                    self.assertEqual(state['down'], [])
                    self.assertEqual(len(state['effects']), 1)
                    self.assertFalse((root/action['call_id']/'cancellation.json').exists())

                    poll_started = time.monotonic()
                    pending = metadata(await server.call_tool('interface_results', {
                        'call_id':action['call_id'], 'include_image':False}))
                    self.assertLess(time.monotonic() - poll_started, 0.2, pending)
                    self.assertEqual(pending['cancellation']['status'], 'pending')
                    self.assertFalse(pending['cancellation']['replay_allowed'])

                    duplicate = metadata(await server.call_tool(
                        'interface_guarded_cancel', {'call_id':action['call_id']}))
                    self.assertEqual(duplicate['operation_id'], cancel['operation_id'])
                    self.assertEqual(len(_read_json(
                        root/'supervisor-fake-x.json', {})['effects']), 1)
                    self.assertGreaterEqual(len(heartbeat_ticks), 5, heartbeat_ticks)

                    resume_archive.set()
                    terminal = await self._wait_for_cancel_terminal(
                        server, action['call_id'])
                cancellation = terminal['cancellation']
                self.assertEqual(cancellation['operation_id'], cancel['operation_id'])
                self.assertEqual(cancellation['result']['cleanup_status'], 'UNKNOWN')
                self.assertFalse(cancellation['result']['release_confirmed'])
                self.assertIsNone(cancellation['result']['task_success'])
                self.assertFalse(cancellation['result']['replay_allowed'])
                archived = _read_json(
                    root/action['call_id']/'cancellation.json', {})
                self.assertEqual(len(archive_payloads), 1)
                self.assertEqual(archived, archive_payloads[0])
                self.assertEqual(archived['operation_id'], cancel['operation_id'])
                self.assertEqual(archived['status'], cancellation['status'])
                self.assertEqual(archived['result'], cancellation['result'])
                self.assertEqual(archived['completed_monotonic_ns'],
                                 cancellation['completed_monotonic_ns'])
                self.assertEqual(len(_read_json(
                    root/'supervisor-fake-x.json', {})['effects']), 1)
            finally:
                resume_archive.set()
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                if archive_entered.is_set():
                    try:
                        await self._wait_for_cancel_terminal(
                            server, action['call_id'], timeout_s=5)
                    except AssertionError:
                        pass
                beat_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await beat_task
                await server.call_tool('interface_close', {})

    async def test_fresh_standard_session_recovers_after_prior_cancel_remains_unknown(self):
        """A new generation may proceed without rewriting the old cancel receipt."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old_root = root/'old-session'
            old_root.mkdir()
            (old_root/'fake-process-generation').write_text('a'*64,
                                                              encoding='utf-8')
            old_server, old_action = await self._start_prestarted_cancel_case(old_root)
            fresh_server = None
            try:
                cancel = metadata(await old_server.call_tool('interface_guarded_cancel', {
                    'call_id':old_action['call_id']}))
                old_terminal = await self._wait_for_cancel_terminal(
                    old_server, old_action['call_id'])
                old_cancel = old_terminal['cancellation']['result']
                self.assertTrue(old_cancel['late_server_request_possible'], old_cancel)
                self.assertEqual(old_cancel['cleanup_status'], 'UNKNOWN', old_cancel)
                self.assertFalse(old_cancel['release_confirmed'], old_cancel)
                self.assertIsNone(old_cancel['task_success'], old_cancel)
                self.assertFalse(old_cancel['replay_allowed'], old_cancel)
                self.assertEqual(cancel['operation_id'],
                                 old_terminal['cancellation']['operation_id'])

                closed = metadata(await old_server.call_tool('interface_close', {}))
                self.assertEqual(closed['status'], 'cleanup_failed', closed)
                self.assertEqual(closed['cleanup_status'], 'UNKNOWN', closed)
                self.assertTrue(closed['late_server_request_possible'], closed)

                fresh_root = root/'fresh-session'
                fresh_root.mkdir()
                (fresh_root/'fake-process-generation').write_text('c'*64,
                                                                  encoding='utf-8')
                (fresh_root/'compiled-profile-mode').write_text('enabled',
                                                                 encoding='utf-8')
                fresh_server = create_server(
                    {'app':20}, fresh_root, session_mode='guarded-x11',
                    guarded_process_identity=True, guarded_query_worker=True,
                    guarded_owned_process=True,
                    _guarded_owner_factory=_fake_owner_factory)
                observed = metadata(await fresh_server.call_tool(
                    'interface_guarded_observe', {}))
                self.assertEqual(observed['status'], 'observed', observed)
                self.assertEqual(
                    observed['source']['pointer_binding']['process_generation'],
                    'c'*64, observed)
                self.assertNotEqual(
                    observed['session']['session_id'],
                    old_terminal['session']['session_id'])
                self.assertNotEqual(
                    observed['session']['owner_process']['pid'],
                    old_terminal['session']['owner_process']['pid'])

                minted = metadata(await fresh_server.call_tool(
                    'interface_guarded_mint', {
                        'alias':'field',
                        'source_sequence':observed['source']['sequence'],
                        'point':[8,8], 'region_size':[12,12]}))
                self.assertEqual(minted['status'], 'minted', minted)
                payload = _compiled_profile_payload(
                    observed['session']['compiled_scope'],
                    observed['session']['compiled_surface'], minted['offset'])
                payload['wait_for_result_ms'] = 10000
                fresh_result = metadata(await fresh_server.call_tool(
                    'interface_guarded_compiled', payload))
                self.assertEqual(fresh_result['method_receipt']['outcome'],
                                 'TASK_SUCCEEDED', fresh_result)
                self.assertEqual(fresh_result['method_receipt']['completed_transitions'],
                                 1, fresh_result)
                self.assertNotEqual(fresh_result['call_id'], old_action['call_id'])
                self.assertIsNone(fresh_result['task_success'], fresh_result)
                self.assertFalse(fresh_result['replay_allowed'], fresh_result)

                # A test-side synthetic effect receipt proves the new caller's
                # committed pixel; it does not resolve or overwrite old custody.
                fresh_effect = json.loads((fresh_root/'synthetic-effect-receipt.json')
                                          .read_text(encoding='utf-8'))
                self.assertEqual(fresh_effect['event'], 'synthetic_app_pixel_commit')
                self.assertEqual(fresh_effect['rgb'], [255, 0, 0])
                old_after = metadata(await old_server.call_tool('interface_results', {
                    'call_id':old_action['call_id'], 'include_image':False}))
                self.assertEqual(old_after['cancellation']['result'], old_cancel)
                self.assertTrue(old_after['cancellation']['result'][
                    'late_server_request_possible'])
            finally:
                if fresh_server is not None:
                    await fresh_server.call_tool('interface_close', {})
                await old_server.call_tool('interface_close', {})

    async def test_prestarted_supervisor_public_path_preserves_bystander_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server, action = await self._start_prestarted_cancel_case(root)
            (root/'bystander-reuse').write_text('inject unrelated XRes PID',
                                                  encoding='utf-8')
            try:
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {
                    'call_id':action['call_id']}))
                self.assertIn(cancel['status'],
                              ('pending', 'cancel_unconfirmed', 'cancel_requested'),
                              cancel)
                terminal = await self._wait_for_cancel_terminal(
                    server, action['call_id'])
                cleanup = terminal['cancellation']['result']
                self.assertTrue(cleanup['owner_process_retired'], cleanup)
                self.assertEqual(cleanup['owner_client_disconnect']['status'],
                                 'unknown', cleanup)
                self.assertEqual(cleanup['owner_client_disconnect']['reason'],
                                 'resource_base_reused_by_unrelated_client', cleanup)
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'not_attempted', cleanup)
                self.assertFalse(cleanup['release_confirmed'], cleanup)
                self.assertEqual(cleanup['cleanup_status'], 'UNKNOWN', cleanup)
                self.assertIsNone(cleanup['task_success'], cleanup)
                self.assertFalse(cleanup['replay_allowed'], cleanup)
                state = _read_json(root/'supervisor-fake-x.json', {})
                self.assertEqual(state['down'], [1], state)
                self.assertEqual(state['effects'], [], state)
                self.assertEqual(len(state['refused']), 1, state)
                self.assertEqual(state['refused'][0]['owner_client_disconnect']
                                 ['observed_pid'], cleanup['owner_client_disconnect']
                                 ['observed_pid'])
            finally:
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_prestarted_supervisor_rejects_stale_generation_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'stale-cleanup-supervisor-generation').write_text('stale', encoding='utf-8')
            server, action = await self._start_prestarted_cancel_case(root)
            try:
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {
                    'call_id':action['call_id']}))
                result = await self._wait_for_cancel_terminal(
                    server, action['call_id'])
                cleanup = result['cancellation']['result']
                state = _read_json(root/'supervisor-fake-x.json', {})
                self.assertEqual(cleanup['owner_client_disconnect']['reason'],
                                 'stale_generation')
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'not_attempted')
                self.assertEqual(state['down'], [1])
                self.assertEqual(state['effects'], [])
                self.assertEqual(len(state['refused']), 1)
                self.assertFalse(cancel['release_confirmed'])
                self.assertIsNone(cancel['task_success'])
                self.assertFalse(cancel['replay_allowed'])
                _retain_prestarted_trial('stale-generation', result, state)
            finally:
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_prestarted_supervisor_allows_release_to_finish_after_three_seconds(self):
        """A delayed but finite release may finish after the old 3 s budget."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'block-cleanup-supervisor').write_text('block', encoding='utf-8')
            server, action = await self._start_prestarted_cancel_case(root)
            try:
                started = time.monotonic()
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {
                    'call_id':action['call_id']}))
                self.assertLess(time.monotonic() - started, 0.45, cancel)
                self.assertEqual(cancel['status'], 'pending', cancel)
                self.assertFalse(cancel['release_confirmed'])
                self.assertIsNone(cancel['task_success'])
                self.assertFalse(cancel['replay_allowed'])

                # Keep the real public composition and supervisor alive beyond
                # the former 3 s deadline, then let its one-shot worker finish.
                await asyncio.sleep(3.2)
                (root/'continue-cleanup-supervisor').write_text(
                    'continue', encoding='utf-8')
                result = await self._wait_for_cancel_terminal(
                    server, action['call_id'], timeout_s=1.5)
                cleanup = result['cancellation']['result']
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'readback_verified', cleanup)
                self.assertFalse(cleanup['release_confirmed'])
                self.assertIsNone(cleanup['task_success'])
                self.assertFalse(cleanup['replay_allowed'])
                state = _read_json(root/'supervisor-fake-x.json', {})
                self.assertEqual(state['down'], [])
                self.assertEqual(len(state['effects']), 1)
            finally:
                (root/'continue-cleanup-supervisor').write_text(
                    'continue', encoding='utf-8')
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_prestarted_supervisor_deadline_kills_blocked_worker_and_preserves_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'block-cleanup-supervisor').write_text('block', encoding='utf-8')
            server, action = await self._start_prestarted_cancel_case(root)
            try:
                beats = []
                async def heartbeat():
                    while True:
                        beats.append(time.monotonic())
                        await asyncio.sleep(0.02)
                beat_task = asyncio.create_task(heartbeat())
                started = time.monotonic()
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {
                    'call_id':action['call_id']}))
                response_s = time.monotonic() - started
                await asyncio.sleep(0.08)
                beat_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await beat_task
                self.assertLess(response_s, 0.45, cancel)
                self.assertGreaterEqual(len(beats), 4, beats)
                pending = metadata(await server.call_tool('interface_results', {
                    'call_id':action['call_id'], 'include_image':False}))
                self.assertEqual(pending['cancellation']['status'], 'pending')
                self.assertFalse(pending['cancellation']['replay_allowed'])
                result = await self._wait_for_cancel_terminal(
                    server, action['call_id'], timeout_s=5)
                cleanup = result['cancellation']['result']
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'unknown')
                self.assertTrue(cleanup['owner_client_disconnect']['worker_retired'],
                                cleanup)
                self.assertFalse(cleanup['release_confirmed'])
                self.assertIsNone(cleanup['task_success'])
                self.assertFalse(cleanup['replay_allowed'])
                state = _read_json(root/'supervisor-fake-x.json', {})
                self.assertEqual(state['down'], [1])
                self.assertEqual(state['effects'], [])
                self.assertEqual(state['refused'], [])
                _retain_prestarted_trial('blocked-helper-deadline', result, state,
                    response_seconds=response_s, heartbeat_count=len(beats))
            finally:
                (root/'continue-cleanup-supervisor').write_text('continue', encoding='utf-8')
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_interface_close_during_pending_cancel_preserves_single_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'block-cleanup-supervisor').write_text('block', encoding='utf-8')
            server, action = await self._start_prestarted_cancel_case(root)
            try:
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {
                    'call_id':action['call_id']}))
                self.assertIn(cancel['status'], ('pending', 'cancel_unconfirmed'), cancel)
                self.assertFalse(cancel['release_confirmed'])
                self.assertIsNone(cancel['task_success'])
                self.assertFalse(cancel['replay_allowed'])

                close_started = time.monotonic()
                close = metadata(await server.call_tool('interface_close', {}))
                close_elapsed = time.monotonic() - close_started
                self.assertLess(close_elapsed, 0.5, close)
                self.assertEqual(close['status'], 'busy', close)
                self.assertEqual(close['cancellation_operation_id'],
                                 cancel['operation_id'])
                self.assertEqual(close['cleanup_status'], 'UNKNOWN', close)
                self.assertFalse(close['release_confirmed'], close)
                self.assertFalse(close['replay_allowed'], close)

                (root/'continue-cleanup-supervisor').write_text('continue', encoding='utf-8')
                result = await self._wait_for_cancel_terminal(server, action['call_id'])
                cleanup = result['cancellation']['result']
                self.assertEqual(result['cancellation']['operation_id'],
                                 cancel['operation_id'])
                self.assertFalse(cleanup['release_confirmed'])
                self.assertIsNone(cleanup['task_success'])
                self.assertFalse(cleanup['replay_allowed'])
                state = _read_json(root/'supervisor-fake-x.json', {})
                self.assertEqual(len(state['effects']), 1, state)
                self.assertEqual(state['effects'][0]['kind'], 'KeyRelease', state)
                self.assertEqual(state['effects'][0]['operation_id'],
                                 cancel['operation_id'], state)
                self.assertEqual(len(state['refused']), 0)
                operation = _read_json(root/'cleanup-supervisor-entered.json', {})
                self.assertEqual(operation['operation_id'], cancel['operation_id'])
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'readback_verified', cleanup)
                self.assertFalse(cleanup['release_confirmed'], cleanup)
            finally:
                (root/'continue-cleanup-supervisor').write_text('continue', encoding='utf-8')
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})

    async def test_server_lifespan_shutdown_keeps_pending_cancel_custody(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_json(root/'supervisor-fake-x.json',
                        {'down':[1], 'effects':[], 'refused':[]})
            server = create_server(
                {'app':20}, root, session_mode='guarded-x11',
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                guarded_prestarted_cancel_supervisor=True,
                _guarded_cancel_supervisor_target=_fake_prestarted_cancel_worker,
                _guarded_owner_factory=_fake_owner_factory)
            async with server.settings.lifespan(server):
                observed = metadata(await server.call_tool(
                    'interface_guarded_observe', {}))
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(
                    alias='field', source_sequence=observed['source']['sequence'],
                    point=[8,8], region_size=[12,12])))
                (root/'block-owner-io').write_text('block', encoding='utf-8')
                action = metadata(await server.call_tool('interface_guarded_input', dict(
                    alias='field', offset=minted['offset'], interaction='keyboard',
                    observe_after=False, wait_for_result_ms=0,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(action['status'], 'pending', action)
                deadline = time.monotonic() + 3
                while not (root/'owner-io-entered.json').exists() and time.monotonic() < deadline:
                    await asyncio.sleep(0.005)
                self.assertTrue((root/'owner-io-entered.json').exists())
                (root/'block-cleanup-supervisor').write_text('block', encoding='utf-8')
                cancel = metadata(await server.call_tool('interface_guarded_cancel', {
                    'call_id':action['call_id']}))
                self.assertIn(cancel['status'], ('pending', 'cancel_unconfirmed'), cancel)
                operation_id = cancel['operation_id']
                self.assertFalse(cancel['release_confirmed'])
                self.assertFalse(cancel['replay_allowed'])
                started = time.monotonic()
            shutdown_elapsed = time.monotonic() - started
            self.assertLess(shutdown_elapsed, 9.0, shutdown_elapsed)
            result = metadata(await server.call_tool('interface_results', {
                'call_id':action['call_id'], 'include_image':False}))
            cancellation = result['cancellation']
            self.assertEqual(cancellation['operation_id'], operation_id)
            self.assertNotEqual(cancellation['status'], 'pending', cancellation)
            terminal = cancellation.get('result') or {}
            self.assertFalse(terminal.get('release_confirmed', False), terminal)
            self.assertIsNone(terminal.get('task_success'), terminal)
            self.assertFalse(terminal.get('replay_allowed', False), terminal)
            self.assertEqual(_read_json(root/'supervisor-fake-x.json', {})['effects'], [])

    async def test_prestarted_supervisor_keeps_unarchived_terminal_custody_on_write_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server, action = await self._start_prestarted_cancel_case(root)
            from runtime.cli_v1.attempt import _write_json as write_json

            def fail_cancellation_receipt(path, value):
                if Path(path).name == 'cancellation.json':
                    raise OSError('injected cancellation archive failure')
                return write_json(path, value)

            try:
                with patch('runtime.cli_v1.mcp_server._write_json',
                           side_effect=fail_cancellation_receipt):
                    cancel = metadata(await server.call_tool(
                        'interface_guarded_cancel', {'call_id':action['call_id']}))
                    result = await self._wait_for_cancel_terminal(
                        server, action['call_id'])
                cancellation = result['cancellation']
                self.assertEqual(cancellation['operation_id'], cancel['operation_id'])
                self.assertIn('persistence_failure', cancellation)
                self.assertFalse((root/action['call_id']/'cancellation.json').exists())
                self.assertFalse(cancellation['result']['release_confirmed'])
                self.assertIsNone(cancellation['result']['task_success'])
                self.assertFalse(cancellation['result']['replay_allowed'])
                duplicate = metadata(await server.call_tool(
                    'interface_guarded_cancel', {'call_id':action['call_id']}))
                self.assertEqual(duplicate['operation_id'], cancel['operation_id'])
                self.assertEqual(duplicate['cancellation']['operation_id'],
                                 cancel['operation_id'])
                self.assertEqual(len(_read_json(
                    root/'supervisor-fake-x.json', {})['effects']), 1)
                # The cancellation receipt can be terminal while the original
                # action worker is still unwinding from its held Fake X sync.
                # Do not let TemporaryDirectory race the worker's final
                # report.json write on Windows.
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                deadline = time.monotonic() + 5
                action_result = None
                while time.monotonic() < deadline:
                    action_result = metadata(await server.call_tool(
                        'interface_results', {'call_id':action['call_id'],
                                              'include_image':False}))
                    if action_result['status'] != 'pending':
                        break
                    await asyncio.sleep(0.01)
                self.assertIsNotNone(action_result)
                self.assertEqual(action_result['status'], 'runtime_failed',
                                 action_result)
            finally:
                (root/'resume-owner-io').write_text('resume', encoding='utf-8')
                await server.call_tool('interface_close', {})


if __name__ == '__main__':
    unittest.main()
