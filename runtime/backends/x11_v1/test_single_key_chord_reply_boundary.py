"""Actual backend methods, inert X requests; no display or physical input."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from Xlib import X
from runtime.backends.x11_v1.backend import X11Backend


class SingleKeyChordReplyBoundaryTests(unittest.TestCase):
    def backend(self, *, failure=None):
        backend = object.__new__(X11Backend)
        backend.held_keycodes = {}
        backend.held_buttons = set()
        backend.emissions = 0
        backend._keycode = lambda key: 38
        trace, obligations = [], []
        backend._input_obligation_publisher = lambda keys, buttons: obligations.append(dict(keys))
        backend._before_input_press = lambda: trace.append('authority')
        def sync():
            trace.append('sync')
            if failure == 'sync':
                raise OSError('reply unavailable')
        backend.d = SimpleNamespace(sync=sync)
        def emit(connection, kind, code):
            self.assertIs(connection, backend.d)
            trace.append(('down' if kind == X.KeyPress else 'up', code))
            if failure == ('down' if kind == X.KeyPress else 'up'):
                raise OSError('send acceptance unknown')
        self.enterContext(patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit))
        self.enterContext(patch('runtime.backends.x11_v1.backend.display.Display',
            side_effect=AssertionError('native display forbidden')))
        return backend, trace, obligations

    def test_single_key_queues_release_before_first_reply_wait(self):
        backend, trace, obligations = self.backend(failure='sync')
        with self.assertRaisesRegex(OSError, 'reply unavailable'):
            backend.key_chord(['a'])
        self.assertEqual(trace, ['authority', ('down', 38), ('up', 38), 'sync'])
        self.assertEqual(backend.held_keycodes, {'a':38})
        self.assertEqual(obligations, [{'a':38}])
        self.assertEqual(backend.emissions, 2)

    def test_success_confirms_release_after_one_reply(self):
        backend, trace, obligations = self.backend()
        backend.key_chord(['a'])
        self.assertEqual(trace, ['authority', ('down', 38), ('up', 38), 'sync'])
        self.assertEqual(backend.held_keycodes, {})
        self.assertEqual(obligations, [{'a':38}, {}])
        self.assertEqual(backend.emissions, 2)

    def test_each_uncertain_send_keeps_original_key_obligation(self):
        for failure in ('down', 'up'):
            with self.subTest(failure=failure):
                with self.subTest():
                    backend, trace, obligations = self.backend(failure=failure)
                    with self.assertRaisesRegex(OSError, 'send acceptance unknown'):
                        backend.key_chord(['a'])
                    self.assertEqual(backend.held_keycodes, {'a':38})
                    self.assertEqual(obligations, [{'a':38}])
                    self.assertNotIn('sync', trace)
                    self.assertFalse(backend._tap_defer_sync)

    def test_authority_rejection_precedes_obligation_and_any_input(self):
        backend, trace, obligations = self.backend()
        def refuse():
            raise PermissionError('authority expired')
        backend._before_input_press = refuse
        with self.assertRaises(PermissionError):
            backend.key_chord(['a'])
        self.assertEqual(trace, [])
        self.assertEqual(obligations, [])
        self.assertEqual(backend.held_keycodes, {})

    def test_subclass_key_state_interception_is_preserved(self):
        backend, trace, obligations = self.backend()
        calls = []
        class Intercepted(X11Backend):
            def key_state(self, key, down):
                calls.append((key, down))
                return super().key_state(key, down)
        backend.__class__ = Intercepted
        backend.key_chord(['a'])
        self.assertEqual(calls, [('a', True), ('a', False)])
        self.assertEqual(trace, ['authority', ('down', 38), ('up', 38), 'sync'])

    def test_guarded_focus_loss_still_refuses_tap_before_input(self):
        from runtime.guarded_x11_v1.bridge import _GuardedBackend
        import time
        backend, trace, obligations = self.backend()
        backend.__class__ = _GuardedBackend
        backend.owner = SimpleNamespace(active=('fixture', 1),
            deadline=time.monotonic_ns()+1_000_000_000, _focus_within_target=lambda:False)
        with self.assertRaisesRegex(RuntimeError, 'focused window is outside'):
            backend.key_chord(['a'])
        self.assertEqual(trace, [])
        self.assertEqual(obligations, [])
        self.assertFalse(backend._tap_defer_sync)

    def test_explicit_key_down_preserves_separate_hold_semantics(self):
        backend, trace, obligations = self.backend()
        backend.key_state('a', True)
        self.assertEqual(trace, ['authority', ('down', 38), 'sync'])
        self.assertEqual(backend.held_keycodes, {'a':38})


if __name__ == '__main__':
    unittest.main()
