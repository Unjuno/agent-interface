import unittest
from unittest.mock import Mock, patch

from runtime.backends.win32_v1.backend import Win32Backend, Win32BackendError


class Win32FocusDiagnosticTests(unittest.TestCase):
    def test_focus_failure_retains_set_result_and_observed_foreground(self):
        backend = object.__new__(Win32Backend)
        backend.targets = {"fixture": 42}
        backend.user32 = Mock()
        backend.user32.SetForegroundWindow.return_value = False
        backend.user32.GetForegroundWindow.return_value = 99
        backend.user32.GetAncestor.return_value = 100
        backend.focused_target = None

        with patch("runtime.backends.win32_v1.backend.time.monotonic",
                   side_effect=[0.0, 0.5, 1.1]), patch(
                       "runtime.backends.win32_v1.backend.time.sleep"):
            with self.assertRaises(Win32BackendError) as raised:
                backend.focus("fixture")

        self.assertIn("SetForegroundWindow=False", str(raised.exception))
        self.assertIn("observed_foreground_hwnd=99", str(raised.exception))
        backend.user32.SetForegroundWindow.assert_called_once_with(42)
        self.assertIsNone(backend.focused_target)

    def test_focus_accepts_foreground_child_owned_by_target_window(self):
        backend = object.__new__(Win32Backend)
        backend.targets = {"fixture": 42}
        backend.user32 = Mock()
        backend.user32.SetForegroundWindow.return_value = False
        backend.user32.GetForegroundWindow.return_value = 99
        backend.user32.GetAncestor.return_value = 42
        backend.focused_target = None

        with patch("runtime.backends.win32_v1.backend.time.monotonic",
                   side_effect=[0.0, 0.0, 1.1]), patch(
                       "runtime.backends.win32_v1.backend.time.sleep"):
            backend.focus("fixture")

        self.assertEqual(backend.focused_target, "fixture")
        backend.user32.GetAncestor.assert_called_with(99, 2)


if __name__ == "__main__":
    unittest.main()
