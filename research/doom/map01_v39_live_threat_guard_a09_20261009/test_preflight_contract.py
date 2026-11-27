"""Local checks for A09 source-root and dependency fail-closed preflights."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_live import guest_source_mapping, qualified_guest_runtime


class PreflightContractTests(unittest.TestCase):
    def test_host_checkout_maps_to_its_exact_guest_source_path(self):
        mapping = guest_source_mapping()
        self.assertEqual(mapping["relative_repo"], "results-local/doom/a09-source")
        self.assertEqual(mapping["guest_source_root"],
                         "/mnt/source/results-local/doom/a09-source")
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


if __name__ == "__main__":
    unittest.main()
