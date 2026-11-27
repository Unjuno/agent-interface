"""Local checks for A12 source-root, dependency, and resource preflights."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_live import (
    MIN_MEMORY_AVAILABLE_BYTES, MIN_TMP_AVAILABLE_BYTES,
    guest_source_mapping, memory_available_bytes, qualified_guest_runtime,
    tmp_available_bytes,
)


class PreflightContractTests(unittest.TestCase):
    def test_host_checkout_maps_to_its_exact_guest_source_path(self):
        mapping = guest_source_mapping()
        self.assertEqual(mapping["relative_repo"], "results-local/doom/a12-source")
        self.assertEqual(mapping["guest_source_root"],
                         "/mnt/source/results-local/doom/a12-source")
        self.assertEqual(Path(mapping["host_repo_root"]),
                         Path(mapping["host_mount_root"]) / mapping["relative_repo"])

    def test_checkout_outside_declared_mount_is_rejected(self):
        with self.assertRaises(ValueError):
            guest_source_mapping("/tmp/unmounted-repo")

    def test_all_startup_dependencies_must_match_the_frozen_versions(self):
        runtime = {"python": "3.12.3", "vizdoom": "1.3.0", "pillow": "12.3.0",
                   "python_xlib": "0.33", "openpyxl": "3.1.5"}
        self.assertTrue(qualified_guest_runtime(runtime))
        for key in runtime:
            changed = dict(runtime)
            changed[key] = "unexpected"
            with self.subTest(key=key):
                self.assertFalse(qualified_guest_runtime(changed))

    def test_resource_preflight_parses_current_available_capacity(self):
        memory = ("Mem: 16808173568 1090265088 15564144640 293253120 "
                  "710672384 15717908480\nSwap: 0 0 0\n")
        disk = ("Filesystem 1-blocks Used Available Capacity Mounted on\n"
                "tmpfs 13446541312 268685312 13177856000 2% /tmp\n")
        self.assertGreaterEqual(memory_available_bytes(memory),
                                MIN_MEMORY_AVAILABLE_BYTES)
        self.assertGreaterEqual(tmp_available_bytes(disk),
                                MIN_TMP_AVAILABLE_BYTES)

    def test_resource_preflight_rejects_unparseable_capacity(self):
        with self.assertRaises(ValueError):
            memory_available_bytes("Mem: unavailable\n")
        with self.assertRaises(ValueError):
            tmp_available_bytes("Filesystem no /tmp row\n")


if __name__ == "__main__":
    unittest.main()
