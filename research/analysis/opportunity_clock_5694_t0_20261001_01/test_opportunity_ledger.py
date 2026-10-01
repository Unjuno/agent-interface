import copy
import unittest

from audit_opportunity_ledger import audit
from opportunity_ledger import build_raw


class OpportunityLedgerTests(unittest.TestCase):
    def test_constructed_ranking_inversion_is_visible(self):
        result = audit(build_raw())
        self.assertEqual(result["result"], "PASS_METHOD_SCOPED")
        self.assertTrue(result["ranking_inversion"]["lower_p95_but_lower_coverage"])

    def test_safe_stop_is_not_counted_as_useful_effect(self):
        s = build_raw()["scenarios"]["safe_stop_control"]["summary"]
        self.assertEqual(s["safe_stop_count"], 1)
        self.assertEqual(s["useful_effect_count"], 2)

    def test_overlap_retains_both_opportunities(self):
        self.assertEqual(build_raw()["scenarios"]["overlap_control"]["summary"]["opportunity_count"], 2)

    def test_unsynchronized_clock_stays_unknown(self):
        s = build_raw()["scenarios"]["unsynchronized_clock_control"]["summary"]
        self.assertEqual(s["unknown_clock_count"], 2)
        self.assertEqual(s["completed_cycle_p95_ms"], None)

    def test_auditor_rejects_denominator_deletion(self):
        raw = copy.deepcopy(build_raw())
        raw["scenarios"]["no_stall_fast"]["opportunities"].pop()
        self.assertNotEqual(audit(raw)["result"], "PASS_METHOD_SCOPED")

    def test_auditor_rejects_fabricated_unsynchronized_timestamp(self):
        raw = copy.deepcopy(build_raw())
        row = raw["scenarios"]["unsynchronized_clock_control"]["opportunities"][0]
        row["decision_start_ms"] = 1
        self.assertNotEqual(audit(raw)["result"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main(verbosity=2)

