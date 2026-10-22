"""Standard MCP composition over one explicitly owned guarded-X11 process."""
import asyncio
import hashlib
import threading
from unittest.mock import Mock, patch
import json
import multiprocessing
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from PIL import Image

from Xlib import X

from runtime.cli_v1.mcp_server import create_server, main
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.backends.x11_v1.backend import X11Backend
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata


def _blocked_release_worker(_send_connection):
    while True:
        time.sleep(0.01)


def _delayed_release_worker(send_connection):
    time.sleep(0.35)
    send_connection.send({
        'status':'released',
        'release':{'verified':True, 'keys_down':[], 'buttons_down':[]},
    })


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
                              heartbeat_count=None):
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

    def read(self, operation, _xid):
        if operation == 'focus':
            return True
        if operation == 'process_identity':
            marker = self.root/'fake-process-generation'
            return marker.read_text(encoding='utf-8') if marker.exists() else 'a'*64
        raise ValueError(operation)

    def close(self):
        return None


def _fake_owner_factory(targets, directory, display_name, options):
    """Rebuild only the transport fake inside the spawned owner process."""
    cleanup = _Cleanup()
    fake = FakeX(cleanup)
    fake.backend.d.get_display_name = lambda:'fake-display'
    fake.backend.d.display = SimpleNamespace(
        info=SimpleNamespace(resource_id_base=0x1200000))
    root = Path(directory)
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
    return owner


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
            await server.call_tool('interface_close',{})

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

    def test_close_after_cancel_retirement_retries_unconfirmed_release_once(self):
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
        owner._cleanup_after_owner_retirement.assert_called_once_with(
            owner._retirement)
        self.assertEqual(first, second)
        self.assertEqual(first['owner_client_disconnect']['status'], 'disconnected')
        self.assertEqual(first['owner_release_attempt']['status'], 'readback_verified')
        self.assertTrue(first['release_attempted'])
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
                    '--guarded-query-worker','--guarded-owned-process']
            with patch('sys.argv', argv), patch(
                    'runtime.cli_v1.mcp_server.create_server') as create:
                main()
            create.assert_called_once_with({'app':20}, output, display_name=None,
                session_mode='guarded-x11', guarded_process_identity=True,
                guarded_query_worker=True, guarded_owned_process=True)
            create.return_value.run.assert_called_once_with(transport='stdio')

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
                self.assertTrue(closed['verified'], closed)
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
                guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            try:
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertEqual(observed['source']['pointer_binding']['process_generation'],'a'*64)
                self.assertTrue(observed['session']['compiled_scope'])
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
                guarded_owned_process=True,
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

                fence_result = {'status':'disconnected', 'worker_retired':True,
                                'elapsed_ms':2.5}
                release_result = {'status':'readback_verified',
                                   'release':{'verified':True, 'keys_down':[],
                                              'buttons_down':[], 'monotonic_ns':12}}
                with (patch('runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                            return_value=fence_result),
                      patch('runtime.cli_v1.owned_guarded_session.OwnedGuardedSessionOwner._release_retired_owner_inputs',
                            return_value=release_result) as release_inputs):
                    cancel = metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))
                self.assertTrue(cancel['owner_process_retired'], cancel)
                self.assertEqual(cancel.get('owner_client_disconnect'), fence_result)
                self.assertEqual(cancel.get('owner_input_obligations'),
                                 {'keys':{'CTRL':1}, 'buttons':[]})
                self.assertEqual(cancel.get('owner_input_obligations_source'),
                                 'retired_child_shared_state')
                self.assertEqual(cancel.get('owner_input_obligations_live_read'), {
                    'status':'snapshot',
                    'obligations':{'keys':{'CTRL':1}, 'buttons':[]},
                })
                self.assertEqual(cancel.get('owner_release_attempt'), release_result)
                release_inputs.assert_called_once_with({'keys':{'CTRL':1}, 'buttons':[]})
                self.assertFalse(cancel['release_confirmed'])
                self.assertEqual(cancel['cleanup_status'], 'UNKNOWN')
                self.assertTrue(cancel['late_server_request_possible'])

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
                    self.assertEqual(kwargs['terminate_grace_s'], 0.1)
                    self.assertEqual(kwargs['accepted_statuses'], ('released', 'unknown'))
                    return supervise_xres_worker(
                        _blocked_release_worker, (), timeout_s=kwargs['timeout_s'],
                        terminate_grace_s=kwargs['terminate_grace_s'],
                        accepted_statuses=kwargs['accepted_statuses'])

                started = time.monotonic()
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
                    self.assertLess(elapsed, 0.45, cancel)
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
                self.assertTrue(cancel['owner_process_retired'], cancel)
                self.assertFalse(cancel['release_confirmed'])
                self.assertIsNone(cancel['task_success'])
                self.assertFalse(cancel['replay_allowed'])
                result = await self._wait_for_cancel_terminal(
                    server, action['call_id'])
                cleanup = result['cancellation']['result']
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'readback_verified', cleanup)
                self.assertFalse(cleanup['release_confirmed'])
                self.assertIsNone(cleanup['task_success'])
                self.assertFalse(cleanup['replay_allowed'])
                state = _read_json(root/'supervisor-fake-x.json', {})
                self.assertEqual(state['down'], [])
                self.assertEqual(len(state['effects']), 1)
                _retain_prestarted_trial('healthy-release', result, state,
                                         response_seconds=time.monotonic() - started)
                operation = _read_json(root/'cleanup-supervisor-entered.json', {})
                self.assertEqual(operation['operation_id'], cancel['operation_id'])
                self.assertEqual(operation['session_id'],
                                 result['cancellation']['owner_generation']['session_id'])
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
                    server, action['call_id'])
                cleanup = result['cancellation']['result']
                self.assertEqual(cleanup['owner_release_attempt']['status'],
                                 'unknown')
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


if __name__ == '__main__':
    unittest.main()
