"""Mutation tests for the independent audit's freeze enforcement."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import audit_v3

HERE = Path(__file__).resolve().parent


class AuditPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (HERE / "raw.json").read_bytes()
        cls.source = (HERE / "audit_v3.py").read_bytes()
        cls.freeze = json.loads((HERE / "AUDIT_V3_FREEZE.json").read_text(encoding="utf-8"))

    def test_canonical_bytes_and_source_match_freeze(self):
        checks, expected = audit_v3.validate_pins(self.raw, self.source, self.freeze)
        self.assertTrue(all(checks.values()))
        self.assertEqual(expected, {"SPACE", "W"})

    def test_changed_raw_bytes_fail_frozen_digest(self):
        checks, _ = audit_v3.validate_pins(self.raw + b" ", self.source, self.freeze)
        self.assertFalse(checks["raw_matches_frozen_digest"])

    def test_changed_audit_source_fails_frozen_digest(self):
        checks, _ = audit_v3.validate_pins(self.raw, self.source + b" ", self.freeze)
        self.assertFalse(checks["audit_matches_frozen_digest"])

    def test_duplicate_or_invalid_inventory_fails_closed(self):
        for inventory in (["SPACE", "SPACE"], ["SPACE", 1], []):
            with self.subTest(inventory=inventory):
                freeze = dict(self.freeze, expected_keys=inventory)
                checks, expected = audit_v3.validate_pins(self.raw, self.source, freeze)
                self.assertFalse(checks["frozen_expected_inventory_is_valid"])
                self.assertEqual(expected, set())

    def test_report_writer_uses_canonical_crlf_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            audit_v3.write_report(output, {"status": "PASS"})
            data = output.read_bytes()
        self.assertIn(b"\r\n", data)
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    def test_archived_v2_source_matches_its_historical_freeze(self):
        freeze = json.loads((HERE / "AUDIT_V2_FREEZE.json").read_text(encoding="utf-8"))
        archived = (HERE / "audit_v2_historical.py").read_bytes()
        self.assertEqual(audit_v3.sha256(archived), freeze["audit_v2_sha256"])
        self.assertEqual(audit_v3.sha256((HERE / "audit_v2.py").read_bytes()),
                         freeze["retired_entrypoint_sha256"])

    def test_retired_v2_entrypoint_cannot_report_pass(self):
        result = subprocess.run([sys.executable, str(HERE / "audit_v2.py")],
                                capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("superseded", result.stderr)


if __name__ == "__main__":
    unittest.main()
