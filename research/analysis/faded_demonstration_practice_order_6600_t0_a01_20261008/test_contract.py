"""Behavioral contract for fixed-dose practice-order ledger T0."""

import copy
import unittest

from audit import audit_document
from candidate import build_raw


SOURCE = {
    "format": "practice-order-6600-source-v1",
    "allocation": "FADED-PRACTICE-ORDER-6600-T0-A01-20261008",
    "variants": ["A", "B", "C"],
    "task_ids": ["A1", "A2", "B1", "B2", "C1", "C2"],
    "blocked_order": ["A1", "A2", "B1", "B2", "C1", "C2"],
    "mixed_order": ["A1", "B1", "C1", "A2", "B2", "C2"],
    "assessment_history": {
        "baseline_screen": "neutral_non-task; same in both arms",
        "intervening_task_test": "none",
        "first_delayed_assessment": "D1",
    },
    "tasks": {
        "A1": {"variant_id": "A", "demonstrated_fact_ids": ["fact-A"], "support_offer_id": "support-A1", "hint_profile": "H1", "stop_available": True, "skip_available": True},
        "A2": {"variant_id": "A", "demonstrated_fact_ids": ["fact-A"], "support_offer_id": "support-A2", "hint_profile": "H1", "stop_available": True, "skip_available": True},
        "B1": {"variant_id": "B", "demonstrated_fact_ids": ["fact-B"], "support_offer_id": "support-B1", "hint_profile": "H1", "stop_available": True, "skip_available": True},
        "B2": {"variant_id": "B", "demonstrated_fact_ids": ["fact-B"], "support_offer_id": "support-B2", "hint_profile": "H1", "stop_available": True, "skip_available": True},
        "C1": {"variant_id": "C", "demonstrated_fact_ids": ["fact-C"], "support_offer_id": "support-C1", "hint_profile": "H1", "stop_available": True, "skip_available": True},
        "C2": {"variant_id": "C", "demonstrated_fact_ids": ["fact-C"], "support_offer_id": "support-C2", "hint_profile": "H1", "stop_available": True, "skip_available": True},
    },
}
ORACLE = {
    "format": "practice-order-6600-oracle-v1",
    "effects": {"A1": "exact", "A2": "exact", "B1": "exact", "B2": "exact", "C1": "exact", "C2": "exact"},
    "forbidden_effects": {"A1": 0, "A2": 0, "B1": 0, "B2": 0, "C1": 0, "C2": 0},
}
SOURCE_BYTES = (
    __import__("json").dumps(SOURCE, sort_keys=True, separators=(",", ":")).encode()
)


class PracticeOrderContractTests(unittest.TestCase):
    def raw(self):
        return build_raw(SOURCE, SOURCE_BYTES)

    def test_blocked_and_mixed_orders_keep_the_same_six_task_dose(self):
        raw = self.raw()
        self.assertEqual(raw["arms"]["blocked"], ["A1", "A2", "B1", "B2", "C1", "C2"])
        self.assertEqual(raw["arms"]["mixed"], ["A1", "B1", "C1", "A2", "B2", "C2"])
        self.assertCountEqual(raw["arms"]["blocked"], raw["arms"]["mixed"])

    def test_independent_auditor_accepts_equal_dose_and_records_no_task_success_claim(self):
        raw = self.raw()
        self.assertEqual(raw["source_sha256"], __import__("hashlib").sha256(SOURCE_BYTES).hexdigest())
        result = audit_document(SOURCE, ORACLE, raw, SOURCE_BYTES)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["task_slots_per_arm"], 6)
        self.assertEqual(result["effect_truth_by_arm"], {"blocked": {"exact": 6}, "mixed": {"exact": 6}})
        self.assertFalse(result["task_success_claim"])

    def test_auditor_binds_exact_source_file_bytes(self):
        source_bytes = b'{ "allocation": "ledger", "format": "source" }\n'
        raw = self.raw()
        raw["source_sha256"] = __import__("hashlib").sha256(SOURCE_BYTES).hexdigest()
        result = audit_document(SOURCE, ORACLE, raw, source_bytes)
        self.assertIn("source_binding", result["errors"])

    def test_auditor_rejects_variant_swap_even_when_task_count_is_unchanged(self):
        raw = self.raw()
        raw["rows"]["mixed"][1]["variant_id"] = "C"
        self.assertEqual(audit_document(SOURCE, ORACLE, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_extra_practice(self):
        raw = self.raw()
        raw["rows"]["mixed"].append(copy.deepcopy(raw["rows"]["mixed"][0]))
        self.assertEqual(audit_document(SOURCE, ORACLE, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_unequal_support_or_hint_opportunities(self):
        raw = self.raw()
        raw["rows"]["mixed"][0]["hint_profile"] = "H2"
        self.assertEqual(audit_document(SOURCE, ORACLE, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_missing_opt_out(self):
        raw = self.raw()
        raw["rows"]["blocked"][2]["skip_available"] = False
        self.assertEqual(audit_document(SOURCE, ORACLE, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_assessment_history_drift(self):
        raw = self.raw()
        raw["assessment_history"]["intervening_task_test"] = "related_task_practice"
        self.assertEqual(audit_document(SOURCE, ORACLE, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_missing_task_and_wrong_effect_truth(self):
        raw = self.raw()
        raw["rows"]["blocked"].pop()
        self.assertEqual(audit_document(SOURCE, ORACLE, raw)["status"], "FAIL_METHOD")

        changed_oracle = copy.deepcopy(ORACLE)
        changed_oracle["effects"]["B1"] = "wrong"
        self.assertEqual(audit_document(SOURCE, changed_oracle, self.raw())["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
