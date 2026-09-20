from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

from runtime.selector_v1.selector import BackendUnavailable, open_session, select_backend, validate_targets


class SelectorTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith('linux'), 'actual Linux backend only')
    def test_explicit_display_selects_and_opens_same_x11_without_mutating_environment(self):
        for env in ({}, {'WAYLAND_DISPLAY': 'wayland-0'}, {'DISPLAY': ':88'}):
            with self.subTest(env=env), mock.patch.dict(os.environ, env, clear=True), mock.patch(
                    'runtime.backends.x11_v1.backend.X11Backend') as backend, mock.patch(
                    'runtime.backends.x11_v1.session.X11RuntimeSession') as session:
                result = open_session({'fixture': 123}, display_name=':99')
                backend.assert_called_once_with(':99', {'fixture': 123})
                session.assert_called_once_with(backend.return_value)
                self.assertIs(result, session.return_value)
                self.assertEqual(dict(os.environ), env)

    def test_invalid_explicit_display_fails_before_backend_selection(self):
        for value in ('', ' ', False, 99):
            with self.subTest(value=value), mock.patch(
                    'runtime.selector_v1.selector.select_backend') as select:
                with self.assertRaises(BackendUnavailable):
                    open_session({'fixture': 123}, display_name=value)
                select.assert_not_called()

    def test_linux_x11_selected_only_with_display(self):
        row = select_backend("linux", {"DISPLAY": ":99"})
        self.assertTrue(row.available)
        self.assertEqual(row.backend_id, "x11-v1")
        self.assertEqual(row.target_kind, "x11_window_id")
        self.assertFalse(row.side_effect_authority)

    def test_wayland_only_fails_closed(self):
        row = select_backend("linux", {"WAYLAND_DISPLAY": "wayland-0"})
        self.assertFalse(row.available)
        self.assertEqual(row.reason, "WAYLAND_BACKEND_NOT_PROMOTED")

    def test_linux_without_session_fails_closed(self):
        row = select_backend("linux", {})
        self.assertFalse(row.available)
        self.assertEqual(row.reason, "NO_INTERACTIVE_DISPLAY")

    def test_windows_selection(self):
        row = select_backend("win32", {})
        self.assertEqual((row.available, row.backend_id, row.target_kind), (True, "win32-v1", "hwnd"))
        self.assertFalse(row.side_effect_authority)

    def test_macos_selection(self):
        row = select_backend("darwin", {})
        self.assertEqual((row.available, row.backend_id, row.target_kind), (True, "quartz-v1", "pid"))
        self.assertFalse(row.side_effect_authority)

    def test_unknown_platform_fails_closed(self):
        row = select_backend("plan9", {})
        self.assertFalse(row.available)
        self.assertEqual(row.reason, "UNSUPPORTED_PLATFORM")

    def test_targets_are_explicit_positive_native_ids(self):
        self.assertEqual(validate_targets({"fixture": 123}), {"fixture": 123})
        for bad in ({}, {"": 1}, {"fixture": 0}, {"fixture": -1}, {"fixture": "1"}):
            with self.subTest(bad=bad), self.assertRaises(BackendUnavailable):
                validate_targets(bad)  # type: ignore[arg-type]

    def test_open_session_validates_targets_before_native_import(self):
        with self.assertRaises(BackendUnavailable):
            open_session({})

    def test_selection_is_side_effect_free_on_actual_host(self):
        before = dict(os.environ)
        row = select_backend()
        self.assertEqual(dict(os.environ), before)
        self.assertFalse(row.side_effect_authority)
        if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
            self.assertFalse(row.available)

    def test_foreign_selection_does_not_enable_foreign_instantiation(self):
        self.assertEqual(select_backend("win32", {}).backend_id, "win32-v1")
        actual = select_backend()
        if sys.platform != "win32":
            self.assertNotEqual(actual.platform, "windows")


if __name__ == "__main__":
    unittest.main()
