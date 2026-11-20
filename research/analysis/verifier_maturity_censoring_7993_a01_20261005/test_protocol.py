from __future__ import annotations

import json
import unittest
from fractions import Fraction
from pathlib import Path

import audit
import candidate

ROOT = Path(__file__).parent


class MaturityProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ci = json.loads((ROOT / "candidate_input.json").read_text(encoding="utf-8"))
        cls.oi = json.loads((ROOT / "oracle_input.json").read_text(encoding="utf-8"))
        cls.result = candidate.run(ROOT / "candidate_input.json")
        cls.records = {r["snapshot_id"]: r for r in cls.result["records"]}
        cls.oracles = {o["snapshot_id"]: o for o in cls.oi["snapshots"]}

    def test_complete_case_undercoverage_witness_and_safe_bound(self):
        r = self.records["informative_delay_known_bad@interim"]
        self.assertEqual(r["complete_case"]["risk"], "0")
        self.assertTrue(r["complete_case"]["naive_le_alpha"])
        self.assertEqual(Fraction(self.oracles[r["snapshot_id"]]["full_cohort_risk"]), Fraction(1, 4))
        self.assertEqual(r["all_assigned_bounds"],
                         {"lower": "0", "upper": "1/4", "supports_le_alpha": False})
        self.assertEqual(r["censor_adjusted"]["status"], "UNKNOWN")

    def test_all_sixteen_independent_masks_and_exact_ht_expectation(self):
        group = [o for o in self.oi["snapshots"] if o["enumeration_group"] == "independent_masks_16"]
        self.assertEqual(len(group), 16)
        values = [Fraction(self.records[o["snapshot_id"]]["censor_adjusted"]["point_estimate"])
                  for o in group]
        self.assertEqual(sum(values, Fraction(0)) / 16, Fraction(1, 4))
        self.assertTrue(all(self.records[o["snapshot_id"]]["censor_adjusted"]["status"] == "ELIGIBLE"
                            for o in group))

    def test_zero_support_and_hidden_misspecification_are_not_guarantees(self):
        z = self.records["zero_support_error_stratum@interim"]["censor_adjusted"]
        self.assertEqual(z["status"], "UNKNOWN")
        hidden_id = "informative_delay_hidden_misspecification@interim"
        mask_id = "independent_mask_14@interim"
        self.assertEqual(audit.observed_signature(next(s for s in self.ci["snapshots"] if s["snapshot_id"] == hidden_id)),
                         audit.observed_signature(next(s for s in self.ci["snapshots"] if s["snapshot_id"] == mask_id)))
        self.assertFalse(self.oracles[hidden_id]["mechanism_matches_declared_model"])
        self.assertFalse(self.records[hidden_id]["censor_adjusted"]["is_risk_certificate"])

    def test_delayed_resolution_and_horizon_statuses_remain_distinct(self):
        early = self.records["delayed_eventually_resolved@early"]
        late = self.records["delayed_eventually_resolved@late"]
        self.assertEqual(early["status_counts"]["pending"], 1)
        self.assertEqual((early["all_assigned_bounds"]["lower"], early["all_assigned_bounds"]["upper"]),
                         ("0", "1/4"))
        self.assertEqual((late["all_assigned_bounds"]["lower"], late["all_assigned_bounds"]["upper"]),
                         ("1/4", "1/4"))
        pending = self.records["pending_at_horizon@horizon"]
        safe = self.records["safe_terminal_stop@terminal"]
        lost = self.records["permanent_loss_unknown_cause@horizon"]
        self.assertEqual(pending["status_counts"]["pending"], 1)
        self.assertEqual(safe["status_counts"]["safe_terminal_stop"], 1)
        self.assertEqual(lost["status_counts"]["permanent_loss_unknown_cause"], 1)
        self.assertIsNone(safe["censor_adjusted"]["point_estimate"])
        self.assertIsNone(lost["censor_adjusted"]["point_estimate"])

    def test_raw_only_audit_and_ten_effective_mutations(self):
        self.assertNotIn("import candidate", (ROOT / "audit.py").read_text(encoding="utf-8"))
        self.assertEqual(audit.validate(self.ci, self.oi, self.result), [])
        mutations = audit.mutation_suite(self.ci, self.oi, self.result)
        self.assertEqual(len(mutations), 10)
        self.assertTrue(all(m["rejected"] for m in mutations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
