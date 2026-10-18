"""Process identity through real handles/public dispatch; all X I/O is fake."""
import copy
import struct
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PIL import Image
from Xlib import X
from runtime.backends.x11_v1.backend import X11BackendError
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.guarded_x11_v1.bridge import NativeHandleBridge, _GuardedBackend, CaptureBindingChanged
from runtime.guarded_x11_v1.handles import TargetHandleStore


class ProcessBridgeTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000
        self.generation = 'a' * 64
        self.reader_error = False
        self.flip = False
        self.fail_after_press = False
        self.expire_in_reader = False
        self.emissions, self.down = [], set()
        b = self.bridge = object.__new__(NativeHandleBridge)
        b._process_identity_guard = True
        b._cancel_lock = threading.Lock()
        b._cancel_ticket = None
        b._active_process_identity = None
        b.target, b.scope = 'app', 'identity:test'
        b.binding_revision, b.sequence = 0, 0
        b.active = b.deadline = b.moved_point = b._input_guard = None
        b.checks, b.additional_checks, b.history = [], [], {}
        b.review_required = False
        b._save = Mock()
        b.store = TargetHandleStore(b.scope)
        backend = b.backend = object.__new__(_GuardedBackend)
        backend.owner = b
        backend.targets = {'app': SimpleNamespace(id=20)}
        backend.d = SimpleNamespace(sync=lambda: None, query_keymap=self.keymap,
            get_input_focus=lambda: SimpleNamespace(focus=SimpleNamespace(id=20)),
            screen=lambda: SimpleNamespace(width_in_pixels=32, height_in_pixels=32))
        backend.root = SimpleNamespace(query_pointer=lambda: SimpleNamespace(mask=0))
        backend.geometry = lambda _target: dict(x=0, y=0, width=32, height=32)
        backend.preflight = lambda _program: None
        backend.focus = lambda _target: None
        backend._activation_supported = lambda: False
        backend._refresh_keyboard_mapping = lambda: False
        backend._keycode = {'CTRL': 1, 'a': 2}.__getitem__
        backend.held_keycodes, backend.held_buttons, backend.emissions = {}, set(), 0
        b.session = X11RuntimeSession(backend)
        self.image = Image.new('RGB', (32, 32))
        for y in range(32):
            for x in range(32):
                self.image.putpixel((x, y), ((x * 31) % 256, (y * 29) % 256, (x * y) % 256))
        b.observe = self.observe

        for target, effect in [('time.monotonic_ns', lambda: self.now),
                ('runtime.guarded_x11_v1.bridge.read_linux_x11_process_identity', self.read),
                ('runtime.backends.x11_v1.backend.xtest.fake_input', self.emit)]:
            p = patch(target, side_effect=effect, create=True)
            p.start(); self.addCleanup(p.stop)
        source = self.observe()
        b.store.mint('field', 'window_content', [2, 2, 12, 12], source, self.image, self.now)

    def test_cancel_ack_and_prearmed_input_obligation_are_serialized(self):
        cancelled = threading.Event()
        cancelled.set()
        self.bridge._cancel_ticket = ('cancel-token', cancelled)

        with self.assertRaises(X11BackendError):
            self.bridge.backend._track_key_press('CTRL', 1)
        with self.assertRaises(X11BackendError):
            self.bridge.backend._track_button_press('left')

        self.assertEqual(self.bridge.backend.held_keycodes, {})
        self.assertEqual(self.bridge.backend.held_buttons, set())
        self.assertEqual(self.emissions, [])

    def read(self, _connection, _xid):
        if self.reader_error:
            raise RuntimeError('identity unavailable')
        if self.expire_in_reader and self.bridge._active_process_identity is not None:
            self.now = self.bridge.deadline
        return self.generation

    def observe(self):
        b = self.bridge
        binding = b._binding()
        b.sequence += 1
        row = dict(sequence=b.sequence, capture_ns=self.now, binding_revision=0, pointer_binding=binding)
        b.history[b.sequence] = (row, self.image.copy())
        return row

    def keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bitmap

    def emit(self, _display, kind, code):
        self.emissions.append((kind, code))
        if kind == X.KeyPress:
            self.down.add(code)
            if self.flip and code == 1:
                self.generation = 'b' * 64
            if self.fail_after_press and code == 1:
                self.reader_error = True
        elif kind == X.KeyRelease:
            self.down.discard(code)

    def invoke(self):
        return self.bridge.keyboard('field', [1, 1],
            tail=[{'op': 'key_chord', 'keys': ['CTRL', 'a']}], expires_at_ns=11_000_000)

    def test_observation_binding_contains_only_identity_digest(self):
        self.assertEqual(self.bridge.history[1][0]['pointer_binding']['process_generation'], 'a' * 64)

    def test_stable_identity_reaches_real_public_session_and_release(self):
        result = self.invoke()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual([c for k, c in self.emissions if k == X.KeyPress], [1, 2])
        self.assertTrue(result['execution']['releases'][-1]['verified'])
        self.assertEqual(self.down, set())

    def test_changed_process_same_xid_and_pixels_refuses_old_alias(self):
        self.generation = 'b' * 64
        result = self.invoke()
        self.assertEqual(result['status'], 'refused')
        self.assertEqual(self.emissions, [])

    def test_change_after_modifier_releases_prefix_and_blocks_next_press(self):
        self.flip = True
        result = self.invoke()
        self.assertEqual(result['status'], 'execution_failed')
        self.assertEqual(self.emissions, [(X.KeyPress, 1), (X.KeyRelease, 1)])
        self.assertTrue(result['execution']['releases'][-1]['verified'])
        self.assertTrue(self.bridge.review_required)
        self.assertEqual(self.down, set())
        self.assertEqual(self.invoke()['status'], 'refused')

    def test_unavailable_reader_refuses_without_input(self):
        self.reader_error = True
        self.assertEqual(self.invoke()['status'], 'refused')
        self.assertEqual(self.emissions, [])
        self.assertTrue(self.bridge.review_required)

    def test_reader_failure_after_modifier_still_releases_prefix(self):
        self.fail_after_press = True
        result = self.invoke()
        self.assertEqual(result['status'], 'execution_failed')
        self.assertEqual(self.emissions, [(X.KeyPress, 1), (X.KeyRelease, 1)])
        self.assertTrue(result['execution']['releases'][-1]['verified'])

    def test_malformed_digest_cannot_become_input_evidence(self):
        self.generation = True
        self.assertEqual(self.invoke()['status'], 'refused')
        self.assertEqual(self.emissions, [])

    def test_changed_identity_refuses_button_press_but_not_release(self):
        b = self.bridge
        b.active, b.deadline, b._active_process_identity = ('field', [1, 1]), 11_000_000, 'a' * 64
        b.check = Mock(return_value={'point': [3, 3]})
        b.moved_point = [3, 3]
        b.backend.root.query_pointer = lambda: SimpleNamespace(mask=0, root_x=3, root_y=3)
        self.generation = 'b' * 64
        with self.assertRaisesRegex(X11BackendError, 'process identity'):
            b.backend.pointer_button('left', True)
        self.assertEqual(self.emissions, [])
        b.backend.held_buttons = {'left'}
        self.reader_error = True
        b.backend.pointer_button('left', False)
        self.assertEqual(self.emissions, [(X.ButtonRelease, 1)])

    def test_legacy_mode_does_not_silently_gain_process_check(self):
        b = self.bridge
        b._process_identity_guard = False
        b.store = TargetHandleStore(b.scope)
        source = self.observe()
        self.assertNotIn('process_generation', source['pointer_binding'])
        b.store.mint('field', 'window_content', [2, 2, 12, 12], source, self.image, self.now)
        self.reader_error = True
        self.assertEqual(self.invoke()['status'], 'completed')

    def test_identity_query_consuming_deadline_cannot_press(self):
        self.expire_in_reader = True
        result = self.invoke()
        self.assertEqual(result['status'], 'execution_failed')
        self.assertEqual(self.emissions, [])

    def test_release_bypasses_identity_even_after_expiry(self):
        self.bridge.backend.held_keycodes = {'CTRL': 1}
        self.down.add(1)
        self.now = 20_000_000
        self.reader_error = True
        self.bridge.backend.key_state('CTRL', False)
        self.assertEqual(self.down, set())

    def test_generation_change_during_real_observe_rejects_capture(self):
        def capture(*args, **kwargs):
            self.generation = 'b' * 64
            return {'status': 'returned', 'observation_id': 'fake', 'observation': {}}
        sequence = self.bridge.sequence
        with patch('runtime.guarded_x11_v1.bridge.observe_in_session', side_effect=capture):
            with self.assertRaises(CaptureBindingChanged):
                NativeHandleBridge.observe(self.bridge)
        self.assertEqual(self.bridge.sequence, sequence)
        self.assertTrue(self.bridge.review_required)

    def test_identity_evidence_cannot_be_dropped_at_resolution(self):
        source = copy.deepcopy(self.bridge.history[1][0])
        source['pointer_binding'].pop('process_generation', None)
        result = self.bridge.store.resolve_point('field', [1, 1], source, self.image, self.now)
        self.assertFalse(result['eligible'])

    def test_invalid_mode_fails_before_backend_creation(self):
        with tempfile.TemporaryDirectory() as temp, patch('runtime.guarded_x11_v1.bridge._GuardedBackend') as backend:
            for value in (1, 'yes', None):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    NativeHandleBridge(None, {}, 'app', Path(temp) / 'out', process_identity=value)
            backend.assert_not_called()

    def test_explicit_constructor_selects_identity_binding(self):
        self.bridge.backend.configure_capture_artifacts = Mock()
        with tempfile.TemporaryDirectory() as temp, patch(
                'runtime.guarded_x11_v1.bridge._GuardedBackend', return_value=self.bridge.backend):
            bridge = NativeHandleBridge(None, {'app': 20}, 'app', Path(temp) / 'out', process_identity=True)
            self.assertTrue(bridge._process_identity_guard)
            self.assertEqual(bridge._binding()['process_generation'], 'a' * 64)


class ReaderTests(unittest.TestCase):
    def connection(self):
        return SimpleNamespace(has_extension=lambda name: name == 'X-Resource',
            res_query_version=Mock(return_value=SimpleNamespace(server_major=1, server_minor=2)),
            res_query_client_ids=Mock(return_value=SimpleNamespace(ids=[
                SimpleNamespace(spec=SimpleNamespace(client=20, mask=2), value=[42])])) )

    def test_xres_process_digest_changes_with_start_time_and_caches_only_version(self):
        from runtime.guarded_x11_v1.process_identity import read_linux_x11_process_identity
        connection = SimpleNamespace(has_extension=lambda name: name == 'X-Resource',
            res_query_version=Mock(return_value=SimpleNamespace(server_major=1, server_minor=2)),
            res_query_client_ids=Mock(return_value=SimpleNamespace(ids=[
                SimpleNamespace(spec=SimpleNamespace(client=20, mask=2), value=[42])])) )
        stat = lambda ticks: '42 (name with ) inside) ' + ' '.join(['S'] + ['0'] * 18 + [str(ticks)])
        with patch('runtime.guarded_x11_v1.process_identity.Path.read_text', side_effect=[stat(123), stat(124)]):
            first = read_linux_x11_process_identity(connection, 20)
            second = read_linux_x11_process_identity(connection, 20)
        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, second)
        self.assertEqual(connection.res_query_version.call_count, 1)
        self.assertEqual(connection.res_query_client_ids.call_count, 2)

    def test_missing_extension_has_no_pid_property_fallback(self):
        from runtime.guarded_x11_v1.process_identity import read_linux_x11_process_identity
        connection = SimpleNamespace(has_extension=lambda _: False)
        with self.assertRaises(RuntimeError):
            read_linux_x11_process_identity(connection, 20)

    def test_real_xlib_protocol_reply_shape_reaches_reader(self):
        from Xlib.ext import res
        from runtime.guarded_x11_v1.process_identity import read_linux_x11_process_identity
        xid, client_base = 0x400001, 0x400000
        request = res.QueryClientIds._request.to_binary(opcode=200, specs=[{'client': xid, 'mask': 2}])
        self.assertEqual(len(request), 16)
        parsed, rest = res.ClientIdValue.parse_binary(struct.pack('=IIII', client_base, 2, 4, 42), None)
        self.assertEqual(rest, b'')
        connection = self.connection()
        connection.res_query_client_ids.return_value.ids = [parsed]
        stat = '42 (name) ' + ' '.join(['S'] + ['0'] * 18 + ['123'])
        with patch('runtime.guarded_x11_v1.process_identity.Path.read_text', return_value=stat):
            self.assertEqual(len(read_linux_x11_process_identity(connection, xid)), 64)
        connection.res_query_client_ids.assert_called_once_with([{'client': xid, 'mask': 2}])

    def test_invalid_protocol_and_process_evidence_refuses(self):
        from runtime.guarded_x11_v1.process_identity import read_linux_x11_process_identity
        valid = '42 (name) ' + ' '.join(['S'] + ['0'] * 18 + ['123'])
        for fault in ('old_version', 'boolean_version', 'no_pid', 'duplicate_pid',
                      'wrong_mask', 'boolean_mask', 'boolean_client', 'zero_client', 'overflow_client',
                      'extra_record', 'boolean_pid', 'zero_pid', 'wrong_proc_pid', 'zombie', 'missing_start', 'negative_start'):
            with self.subTest(fault=fault):
                connection = self.connection()
                stat = valid
                if fault == 'old_version': connection.res_query_version.return_value.server_minor = 1
                elif fault == 'boolean_version': connection.res_query_version.return_value.server_major = True
                elif fault == 'no_pid': connection.res_query_client_ids.return_value.ids = []
                elif fault == 'duplicate_pid': connection.res_query_client_ids.return_value.ids *= 2
                elif fault == 'wrong_mask': connection.res_query_client_ids.return_value.ids[0].spec.mask = 1
                elif fault == 'boolean_mask': connection.res_query_client_ids.return_value.ids[0].spec.mask = True
                elif fault == 'boolean_client': connection.res_query_client_ids.return_value.ids[0].spec.client = True
                elif fault == 'zero_client': connection.res_query_client_ids.return_value.ids[0].spec.client = 0
                elif fault == 'overflow_client': connection.res_query_client_ids.return_value.ids[0].spec.client = 2**32
                elif fault == 'extra_record': connection.res_query_client_ids.return_value.ids.append(
                    SimpleNamespace(spec=SimpleNamespace(client=30, mask=1), value=[]))
                elif fault == 'boolean_pid': connection.res_query_client_ids.return_value.ids[0].value = [True]
                elif fault == 'zero_pid': connection.res_query_client_ids.return_value.ids[0].value = [0]
                elif fault == 'wrong_proc_pid': stat = valid.replace('42 (', '43 (')
                elif fault == 'zombie': stat = valid.replace(') S ', ') Z ')
                elif fault == 'missing_start': stat = '42 (name) S'
                elif fault == 'negative_start': stat = valid[:-3] + '-1'
                with patch('runtime.guarded_x11_v1.process_identity.Path.read_text', return_value=stat):
                    with self.assertRaises(RuntimeError):
                        read_linux_x11_process_identity(connection, 20)


if __name__ == '__main__':
    unittest.main()
