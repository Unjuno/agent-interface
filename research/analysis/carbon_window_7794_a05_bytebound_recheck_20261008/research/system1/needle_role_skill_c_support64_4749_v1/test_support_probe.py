"""Zero-training construction-contract tests."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import support_probe


class ConstructionTests(unittest.TestCase):
    def test_missing_environment_stops_before_upstream_import_or_training(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                support_probe.main()
        self.assertEqual(str(ctx.exception), "STOP_MISSING_NEEDLE_ENV")

    def test_seed_specific_empty_output_required(self):
        with patch.dict(os.environ, {"NEEDLE_SEED": "7865001", "NEEDLE_OUTPUT": "/not-empty"}, clear=True):
            with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "iterdir", return_value=iter([Path("x")])), patch.object(support_probe, "load_upstream", side_effect=AssertionError("must stop first")):
                with self.assertRaises(SystemExit) as ctx:
                    support_probe.main()
        self.assertEqual(str(ctx.exception), "STOP_CONSTRUCTION_ALLOCATION_OR_OUTPUT")

    def test_invalid_seed_stops_before_upstream_import(self):
        with patch.dict(os.environ, {"NEEDLE_SEED": "7865101", "NEEDLE_OUTPUT": "/empty"}, clear=True):
            with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "iterdir", return_value=iter([])), patch.object(support_probe, "load_upstream", side_effect=AssertionError("must stop first")):
                with self.assertRaises(SystemExit) as ctx:
                    support_probe.main()
        self.assertEqual(str(ctx.exception), "STOP_CONSTRUCTION_ALLOCATION_OR_OUTPUT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
