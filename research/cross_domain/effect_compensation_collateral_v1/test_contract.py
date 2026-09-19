import tempfile
import unittest
from pathlib import Path

from experiment import (
    COMPENSATED,
    INCOMPLETE,
    VERIFIED,
    full_invariant_label,
    primary_only_label,
    run_case,
)


class ClassifierTests(unittest.TestCase):
    def test_correct(self):
        h=[{"seq":1,"kind":"effect","primary":"target","collateral":"preserve"}]
        self.assertEqual(primary_only_label(("target","preserve"),h), VERIFIED)
        self.assertEqual(full_invariant_label(("target","preserve"),h), VERIFIED)

    def test_clean_compensation(self):
        h=[{"seq":1,"kind":"effect","primary":"wrong","collateral":"preserve"},{"seq":2,"kind":"compensation","primary":"old","collateral":"preserve"}]
        self.assertEqual(primary_only_label(("old","preserve"),h), COMPENSATED)
        self.assertEqual(full_invariant_label(("old","preserve"),h), COMPENSATED)

    def test_collateral_damage_discriminates(self):
        h=[{"seq":1,"kind":"effect","primary":"wrong","collateral":"preserve"},{"seq":2,"kind":"compensation","primary":"old","collateral":"damaged"}]
        self.assertEqual(primary_only_label(("old","damaged"),h), COMPENSATED)
        self.assertEqual(full_invariant_label(("old","damaged"),h), INCOMPLETE)


class DurableFixtureTests(unittest.TestCase):
    def test_three_scenarios_persist_expected_state_and_history(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cases=[
                {"id":"t-correct","scenario":"correct"},
                {"id":"t-clean","scenario":"wrong_compensated_clean"},
                {"id":"t-damaged","scenario":"wrong_compensated_collateral"},
            ]
            rows=[run_case(root,c) for c in cases]
            self.assertEqual(rows[0]["state"],{"primary":"target","collateral":"preserve"})
            self.assertEqual(len(rows[0]["history"]),1)
            self.assertEqual(rows[1]["state"],{"primary":"old","collateral":"preserve"})
            self.assertEqual(len(rows[1]["history"]),2)
            self.assertEqual(rows[2]["state"],{"primary":"old","collateral":"damaged"})
            self.assertEqual(len(rows[2]["history"]),2)
            self.assertFalse(rows[2]["primary_truthful"])
            self.assertTrue(rows[2]["full_truthful"])


if __name__ == "__main__":
    unittest.main()
