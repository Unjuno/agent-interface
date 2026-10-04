"""Mutation tests for the independent audit's freeze enforcement."""
import json
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


if __name__ == "__main__":
    unittest.main()
