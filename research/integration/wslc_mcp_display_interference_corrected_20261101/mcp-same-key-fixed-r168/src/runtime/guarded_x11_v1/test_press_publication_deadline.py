"""Expiry while publishing prearmed custody must not send a new press."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
from runtime.guarded_x11_v1.bridge import _GuardedBackend


class PressPublicationDeadlineTests(unittest.TestCase):
    def test_expiry_during_publication_refuses_both_press_types(self):
        for kind in ('button', 'key'):
            with self.subTest(kind=kind):
                clock = [99]
                b = object.__new__(_GuardedBackend)
                b.d = Mock()
                b.held_keycodes = {}
                b.held_buttons = set()
                b.emissions = 0
                owner = SimpleNamespace(active=('fixture', [0, 0]), deadline=100,
                                        _check_cancelled=Mock(), _process_identity_guard=False)
                owner._prearm_button_press = lambda button: b.held_buttons.add(button)
                owner._prearm_key_press = lambda key, code: b.held_keycodes.update({key: code})
                b.owner = owner
                b._keycode = Mock(return_value=38)
                b._input_obligation_publisher = lambda keys, buttons: clock.__setitem__(0, 100)
                with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns', side_effect=lambda: clock[0]), \
                     patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
                    with self.assertRaises(X11BackendError):
                        if kind == 'button': X11Backend.pointer_button(b, 'left', True)
                        else: X11Backend.key_state(b, 'A', True)
                emit.assert_not_called()
                self.assertEqual(b.emissions, 0)
                self.assertTrue(b.held_buttons or b.held_keycodes)

    def test_cancel_during_publication_refuses_press(self):
        b = object.__new__(_GuardedBackend)
        b.d = Mock(); b.emissions = 0; b.held_buttons = set()
        b.held_keycodes = {}
        cancel = [False]
        def check():
            if cancel[0]: raise X11BackendError('cancelled')
        b.owner = SimpleNamespace(active=('fixture', [0, 0]), deadline=100,
                                  _check_cancelled=check, _process_identity_guard=False,
                                  _prearm_button_press=lambda button: b.held_buttons.add(button))
        b._input_obligation_publisher = lambda keys, buttons: cancel.__setitem__(0, True)
        with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns', return_value=99), \
             patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
            with self.assertRaisesRegex(X11BackendError, 'cancelled'):
                X11Backend.pointer_button(b, 'left', True)
        emit.assert_not_called()
        self.assertEqual(b.held_buttons, {'left'})


if __name__ == '__main__': unittest.main()
