from __future__ import annotations

import unittest
from runtime.core_v1.platform_probe import probe_platform


class ProbeTests(unittest.TestCase):
    def test_windows(self):
        row = probe_platform(system="Windows", env={})
        self.assertEqual(row["candidate_backend"], "win32")
        self.assertFalse(row["support_claim"])
        self.assertEqual(row["input_authority"], "none")

    def test_macos(self):
        row = probe_platform(system="Darwin", env={})
        self.assertEqual(row["candidate_backend"], "quartz")
        self.assertIn("accessibility", row["permission_hints"])
        self.assertIn("screen-recording", row["permission_hints"])

    def test_linux_x11(self):
        row = probe_platform(system="Linux", env={"DISPLAY": ":7"})
        self.assertEqual(row["candidate_backend"], "x11")
        self.assertEqual(row["session"], ":7")

    def test_linux_wayland_preferred_if_present(self):
        row = probe_platform(system="Linux", env={"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"})
        self.assertEqual(row["candidate_backend"], "wayland")

    def test_linux_without_graphical_session(self):
        row = probe_platform(system="Linux", env={})
        self.assertEqual(row["candidate_backend"], "none")
        self.assertIn("graphical-session-missing", row["permission_hints"])

    def test_unknown_os(self):
        row = probe_platform(system="Plan9", env={})
        self.assertEqual(row["os"], "unknown")
        self.assertEqual(row["candidate_backend"], "unsupported-host")


if __name__ == "__main__":
    unittest.main()
