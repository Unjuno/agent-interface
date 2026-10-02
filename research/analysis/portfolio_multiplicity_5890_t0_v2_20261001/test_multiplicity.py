import copy
import unittest

from audit import validate
from runner import build_raw, online_reject


class MultiplicityLedgerTests(unittest.TestCase):
    def test_schedule_is_complete_and_fixed(self):
        raw = build_raw()
        self.assertEqual(len(raw["rows"]), 416)
        self.assertEqual(len({r["completion_order"] for r in raw["rows"]}), 416)
        self.assertEqual(validate(raw)[0], [])

    def test_alpha_spending_is_bounded(self):
        total = sum(0.05/(i*(i+1)) for i in range(1,193))
        self.assertLess(total, 0.05)
        self.assertFalse(online_reject(50_001, 1))

    def test_ineligible_claims_cannot_promote(self):
        raw = build_raw()
        for row in raw["rows"]:
            if row["claim_type"] not in {"STAT_NULL", "STAT_ALT"}:
                self.assertFalse(row["online_promoted"])
        safety = [r for r in raw["rows"] if r["claim_type"] == "HARD_SAFETY_FAIL"]
        self.assertTrue(all(r["p_micro"] == 1 and not r["online_promoted"] for r in safety))

    def test_auditor_rejects_omission_and_method_p(self):
        raw = build_raw()
        missing = copy.deepcopy(raw); missing["rows"].pop(6)
        self.assertTrue(validate(missing)[0])
        methodp = copy.deepcopy(raw); methodp["rows"][2]["p_micro"] = 1
        self.assertTrue(validate(methodp)[0])

    def test_seeded_null_and_alternative_have_distinct_truth(self):
        raw = build_raw()
        self.assertTrue(all(r["true_null"] is True for r in raw["rows"] if r["claim_type"] == "STAT_NULL"))
        self.assertTrue(all(r["true_null"] is False for r in raw["rows"] if r["claim_type"] == "STAT_ALT"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

