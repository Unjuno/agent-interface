#!/usr/bin/env python3
"""Regression coverage for A04 summary-field consistency."""
import sys
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))
from audit_v2 import audit


class SummaryFieldAuditTests(unittest.TestCase):
    def test_pristine_parent_result_passes(self):
        report = audit(PKG / "RESULT.json")
        self.assertTrue(report["pass"], report)
        self.assertTrue(all(report["checks"].values()), report)

    def test_each_top_level_summary_corruption_fails_only_its_own_check(self):
        cases = {
            "unique": ("unique", 0),
            "ambiguous": ("ambiguous", 0),
            "unmatched": ("unmatched", 39),
        }
        for case_name, (field, expected_value) in cases.items():
            with self.subTest(field=field):
                report = audit(PKG / "corruptions" / case_name / "RESULT.json")
                self.assertFalse(report["pass"], report)
                self.assertIs(report["checks"][f"{field}_summary_matches"], False)
                self.assertTrue(all(value for key, value in report["checks"].items()
                                    if key != f"{field}_summary_matches"), report)
                self.assertEqual(report["recomputed"][field],
                                 {"unique": 6, "ambiguous": 33, "unmatched": 0}[field])
                self.assertEqual(
                    (PKG / "corruptions" / case_name / "RESULT.json").read_text(
                        encoding="utf-8").find(f'\"{field}\": {expected_value}') >= 0,
                    True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
