"""Local guard fence regression; no X server or physical input involved."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime.guarded_x11_v1.bridge import _GuardedBackend
from runtime.backends.x11_v1.backend import X11BackendError


class MotionDeadlineTests(unittest.TestCase):
    def make_backend(self):
        backend = object.__new__(_GuardedBackend)
        backend.owner = SimpleNamespace(
            active=('target', [0, 0]), deadline=100,
            check=Mock(return_value={'point': [20, 30]}),
            _check_cancelled=Mock(), _process_identity_guard=False)
        backend.d = Mock()
        backend.emissions = 0
        return backend

    def test_expiry_after_observation_prevents_motion(self):
        backend = self.make_backend()
        with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns', return_value=100), \
             patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
            with self.assertRaises(X11BackendError):
                backend.pointer_move('target', 'screen_physical_px', 20, 30)
        emit.assert_not_called()
        self.assertEqual(backend.emissions, 0)

    def test_live_lease_allows_guarded_motion(self):
        backend = self.make_backend()
        with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns', return_value=99), \
             patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
            backend.pointer_move('target', 'screen_physical_px', 20, 30)
        emit.assert_called_once()
        self.assertEqual(backend.owner.moved_point, [20, 30])

    def test_cancellation_prevents_motion(self):
        backend = self.make_backend()
        backend.owner._check_cancelled.side_effect = X11BackendError('cancelled')
        with patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
            with self.assertRaisesRegex(X11BackendError, 'cancelled'):
                backend.pointer_move('target', 'screen_physical_px', 20, 30)
        emit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
