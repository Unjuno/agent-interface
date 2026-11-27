import unittest
from unittest.mock import Mock, patch
from Xlib import X
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError

class ReleaseDeadlineTests(unittest.TestCase):
    def test_expiry_between_keys_stops_additional_release_requests(self):
        backend=object.__new__(X11Backend)
        backend.held_keycodes={'a':38,'b':56}
        backend.held_buttons=set()
        backend.emissions=0
        backend.d=Mock()
        with (patch('runtime.backends.x11_v1.backend.time.monotonic_ns',side_effect=[90,110]),
              patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit):
            with self.assertRaises(X11BackendError):
                backend.release_all(deadline_monotonic_ns=100)
        emit.assert_called_once_with(backend.d,X.KeyRelease,38)
        backend.d.sync.assert_not_called()
        self.assertEqual(backend.held_keycodes,{'a':38,'b':56})

if __name__=='__main__':unittest.main()
