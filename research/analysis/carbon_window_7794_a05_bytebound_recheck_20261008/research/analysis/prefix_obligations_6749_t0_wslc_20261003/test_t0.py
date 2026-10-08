"""Construction checks only; not the frozen candidate/auditor allocation."""
import copy
import unittest

from audit import audit, mutation_cases, validate
from candidate import build_raw


class PrefixObligationConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = build_raw()

    def test_independent_oracle_accepts_candidate(self):
        self.assertTrue(validate(self.raw))

    def test_stable_negative_keeps_incomplete_mandatory_obligation(self):
        row = next(r for r in self.raw["rows"] if r["disposition"] == "STABLE_FAIL"
                   and r["state"]["check_a"] is None)
        self.assertIn("check_a", row["pending_obligations"])

    def test_only_explicit_complete_can_pass(self):
        for row in self.raw["rows"]:
            if row["disposition"] == "PASS":
                self.assertEqual(row["state"]["optional"], "COMPLETE")
                self.assertEqual(row["state"]["generation"], "CURRENT")
                self.assertEqual((row["state"]["check_a"], row["state"]["check_b"]),
                                 ("PASS", "PASS"))

    def test_timeout_conflict_and_clear_are_not_completion(self):
        for state in ("OPEN", "CLEARED", "CONFLICT", "TIMEOUT"):
            rows = [r for r in self.raw["rows"] if r["state"]["optional"] == state]
            self.assertTrue(rows)
            self.assertFalse(any(r["disposition"] == "PASS" for r in rows))

    def test_accounting_contract_is_disjoint(self):
        self.assertNotIn("stable_fail_prefixes", self.raw["disposition_counts"])
        self.assertEqual(set(self.raw["early_finalization_metrics"]),
                         {"stable_fail_prefixes", "pass_prefixes"})

    def test_all_five_mutations_are_rejected_independently(self):
        for label, changed in mutation_cases(self.raw).items():
            with self.subTest(label=label):
                self.assertFalse(validate(changed))
        self.assertEqual(audit(self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_missing_prefix_is_rejected(self):
        changed = copy.deepcopy(self.raw)
        changed["rows"].pop()
        self.assertFalse(validate(changed))


if __name__ == "__main__":
    unittest.main()
