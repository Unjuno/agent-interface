"""Standard MCP composition over one explicitly owned guarded-X11 process."""
import asyncio
import hashlib
import threading
from unittest.mock import Mock, patch
import json
import multiprocessing
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from Xlib import X

from runtime.cli_v1.mcp_server import create_server, main
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.backends.x11_v1.backend import X11Backend
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata


def _blocked_release_worker(_send_connection):
    while True:
        time.sleep(0.01)


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
    def sync():
        if (root/'block-owner-io').exists():
            (root/'owner-io-entered.json').write_text(
                json.dumps(sorted(fake.down)), encoding='utf-8')
            while not (root/'resume-owner-io').exists():
                time.sleep(0.005)
    fake.backend.d.sync = sync
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

                with patch('runtime.cli_v1.owned_guarded_session._STARTUP_TIMEOUT_S', 0):
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

                    with patch('runtime.cli_v1.owned_guarded_session._STARTUP_TIMEOUT_S', 0):
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
                    self.assertEqual(kwargs['timeout_s'], 0.25)
                    self.assertEqual(kwargs['terminate_grace_s'], 0.1)
                    self.assertEqual(kwargs['accepted_statuses'], ('released', 'unknown'))
                    return supervise_xres_worker(
                        _blocked_release_worker, (), timeout_s=0.08,
                        terminate_grace_s=0.08,
                        accepted_statuses=kwargs['accepted_statuses'])

                started = time.monotonic()
                with (patch('runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised',
                            return_value=fence),
                      patch('runtime.cli_v1.owned_guarded_session.supervise_xres_worker',
                            side_effect=supervise_blocked_release)):
                    cancel = metadata(await server.call_tool('interface_guarded_cancel',
                        {'call_id':pending['call_id']}))
                elapsed = time.monotonic() - started

                self.assertLess(elapsed, 3.0, cancel)
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


if __name__ == '__main__':
    unittest.main()
