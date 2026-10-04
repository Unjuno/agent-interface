#!/usr/bin/env python3
"""Frozen audit mutation controls; candidate is never invoked here."""
import copy
import json
import unittest
from pathlib import Path

from audit import audit_data

ROOT = Path(__file__).resolve().parent


class RawAuditMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.result = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))

    def test_unmodified_record_passes(self):
        self.assertEqual(audit_data(self.fixture, self.result), (True, "PASS_METHOD_SCOPED"))

    def test_source_target_relabel_is_rejected(self):
        mutated = copy.deepcopy(self.result)
        mutated["sources"] = ["x2", "x1"]
        self.assertFalse(audit_data(self.fixture, mutated)[0])

    def test_missing_probability_mass_is_rejected(self):
        mutated = copy.deepcopy(self.result)
        mutated["rows"][0]["counts"][0]["count"] -= 1
        self.assertFalse(audit_data(self.fixture, mutated)[0])

    def test_joint_distribution_change_is_rejected(self):
        mutated = copy.deepcopy(self.result)
        mutated["rows"][3]["counts"][0]["y"] = 1
        self.assertFalse(audit_data(self.fixture, mutated)[0])


if __name__ == "__main__":
    unittest.main()
