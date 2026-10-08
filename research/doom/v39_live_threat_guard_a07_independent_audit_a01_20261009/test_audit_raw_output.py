from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


AUDITOR_PATH = Path(__file__).with_name("audit_raw.py")
SPEC = importlib.util.spec_from_file_location("audit_raw", AUDITOR_PATH)
audit_raw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_raw)


class OutputSafetyTests(unittest.TestCase):
    def test_output_inside_raw_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            raw_root = Path(temp) / "raw"
            raw_root.mkdir()
            output = raw_root / "episode" / "runtime" / "events.jsonl"

            with self.assertRaisesRegex(ValueError, "outside the raw allocation"):
                audit_raw.validate_output_path(raw_root, output)

    def test_output_symlink_into_raw_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw_root = root / "raw"
            raw_root.mkdir()
            alias = root / "raw-alias"
            alias.symlink_to(raw_root, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "outside the raw allocation"):
                audit_raw.validate_output_path(raw_root, alias / "RESULT.json")

    def test_atomic_write_does_not_modify_raw_hardlink_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw_file = root / "raw-events.jsonl"
            output = root / "RESULT.json"
            raw_file.write_text("immutable raw bytes\n")
            os.link(raw_file, output)

            audit_raw.write_result_atomically(output, {"status": "PASS"})

            self.assertEqual(raw_file.read_text(), "immutable raw bytes\n")
            self.assertEqual(json.loads(output.read_text()), {"status": "PASS"})
            self.assertNotEqual(raw_file.stat().st_ino, output.stat().st_ino)


if __name__ == "__main__":
    unittest.main(verbosity=2)
