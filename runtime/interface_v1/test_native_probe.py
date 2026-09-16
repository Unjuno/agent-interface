from __future__ import annotations

import platform
import unittest

from runtime.interface_v1.doctor import report
from runtime.interface_v1.native_probe import (
    SCHEMA,
    probe_linux,
    probe_macos,
    probe_native,
    probe_windows,
)


class DeterministicProbeTests(unittest.TestCase):
    def test_foreign_windows_probe_is_inapplicable(self):
        row = probe_windows(system="Linux")
        self.assertFalse(row["applicable"])
        self.assertFalse(row["support_claim"])
        self.assertEqual(row["input_authority"], "none")

    def test_foreign_macos_probe_is_inapplicable(self):
        row = probe_macos(system="Linux")
        self.assertFalse(row["applicable"])
        self.assertEqual(row["candidate_backend"], "quartz")

    def test_linux_x11_discovery_is_not_support(self):
        row = probe_linux(system="Linux", env={"DISPLAY": ":77"})
        self.assertEqual(row["candidate_backend"], "x11")
        self.assertTrue(row["native_api"]["x11_candidate_integrated"])
        self.assertFalse(row["support_claim"])
        self.assertEqual(row["input_authority"], "none")

    def test_linux_wayland_discovery_is_not_support(self):
        row = probe_linux(system="Linux", env={"WAYLAND_DISPLAY": "wayland-0"})
        self.assertEqual(row["candidate_backend"], "wayland")
        self.assertTrue(row["native_api"]["wayland_candidate_only"])
        self.assertFalse(row["support_claim"])

    def test_doctor_never_grants_authority(self):
        for system in ("Linux", "Windows", "Darwin", "Plan9"):
            with self.subTest(system=system):
                row = report(system=system, env={})
                self.assertFalse(row["support_claim"])
                self.assertFalse(row["ready_for_side_effects"])
                self.assertEqual(row["native_probe"]["input_authority"], "none")


class CurrentHostProbeTests(unittest.TestCase):
    def test_actual_host_probe_is_typed_and_side_effect_free(self):
        row = probe_native()
        self.assertEqual(row["schema"], SCHEMA)
        self.assertFalse(row["support_claim"])
        self.assertEqual(row["input_authority"], "none")
        self.assertEqual(row["capture_authority"], "none")
        self.assertIn("native_api", row)
        self.assertIn("permissions", row)
        self.assertIn("observations", row)
        self.assertEqual(row["applicable"], platform.system() in {"Linux", "Windows", "Darwin"})


if __name__ == "__main__":
    unittest.main()
