"""Mutation controls for the strict retained-output auditor; no candidate replay."""
from pathlib import Path
import unittest

from audit_v2 import audit_text


RAW = Path(__file__).with_name("RAW_STDOUT.txt").read_text(encoding="utf-8")


class StrictAuditTests(unittest.TestCase):
    def test_original_six_case_matrix_passes(self):
        self.assertEqual(audit_text(RAW), {
            "case_count": 6,
            "status": "PASS_RAW_POSITION_MATRIX",
        })

    def test_missing_accepted_then_raise_suffix_fails(self):
        target = "accept_before_raise=True fail_position=0 observed=[(0, True, 'accepted_then_raise'), (1, False, 'delivered'), (2, False, 'delivered')]"
        self.assertIn(target, RAW)
        self.assert_fails(RAW.replace(target, target.replace(", (2, False, 'delivered')", "")))

    def test_missing_confirmed_prefix_fails(self):
        target = "accept_before_raise=True fail_position=2 observed=[(0, True, 'delivered'), (1, True, 'delivered'), (2, True, 'accepted_then_raise')]"
        self.assertIn(target, RAW)
        self.assert_fails(RAW.replace(target, target.replace("(0, True, 'delivered'), ", "")))

    def test_duplicate_case_fails(self):
        first_case = RAW.splitlines()[1]
        self.assert_fails(RAW + first_case + "\n")

    def test_wrong_completeness_in_suffix_fails(self):
        self.assert_fails(RAW.replace(
            "(1, False, 'delivered'), (2, False, 'delivered')",
            "(1, True, 'delivered'), (2, False, 'delivered')",
            1,
        ))

    def assert_fails(self, text):
        with self.assertRaises(ValueError):
            audit_text(text)


if __name__ == "__main__":
    unittest.main()
