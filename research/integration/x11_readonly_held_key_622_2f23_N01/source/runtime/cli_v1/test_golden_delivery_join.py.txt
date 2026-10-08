"""Regression tests for composing delivery evidence; no backend is invoked."""
from copy import deepcopy
import unittest
from runtime.cli_v1.golden_v3 import adapt_dispatch_result


class GoldenDeliveryJoinTests(unittest.TestCase):
    def receipt(self, **fields):
        row = {"status": "returned", "result": {"status": "completed", "task_success": True,
                                                "partial_effects": ["retained"]}}
        row.update(fields)
        return row

    def test_inner_ambiguity_cannot_be_hidden_by_outer_confirmation(self):
        for value in ("ambiguous", "uncertain", "unknown", "write_uncertain", "delivery_uncertain"):
            row = self.receipt(delivery="confirmed")
            row["result"]["delivery"] = value
            result = adapt_dispatch_result(row)
            self.assertEqual(result["status"], "refused")
            self.assertFalse(result["task_success"])
            self.assertEqual(result["diagnostic"], "AMBIGUOUS_DELIVERY:" + value)

    def test_outer_null_does_not_erase_inner_evidence(self):
        row = self.receipt(delivery=None)
        row["result"]["delivery"] = "write_uncertain"
        self.assertEqual(adapt_dispatch_result(row)["status"], "refused")

    def test_partial_does_not_override_uncertainty(self):
        row = self.receipt(delivery="confirmed_partial")
        row["result"]["delivery"] = "uncertain"
        self.assertEqual(adapt_dispatch_result(row)["status"], "refused")

    def test_partial_in_either_layer_is_not_full_success(self):
        for outer, inner in (("confirmed", "confirmed_partial"), ("confirmed_partial", "confirmed")):
            row = self.receipt(delivery=outer)
            row["result"]["delivery"] = inner
            self.assertEqual(adapt_dispatch_result(row)["status"], "partial")

    def test_unknown_in_either_layer_is_not_overridden(self):
        for outer, inner in (("confirmed", "future_state"), ("future_state", "confirmed")):
            row = self.receipt(delivery=outer)
            row["result"]["delivery"] = inner
            result = adapt_dispatch_result(row)
            self.assertEqual(result["status"], "refused")
            self.assertEqual(result["diagnostic"], "UNKNOWN_DELIVERY:future_state")

    def test_absent_or_null_preserves_legacy_positive(self):
        for row in (self.receipt(), self.receipt(delivery=None)):
            self.assertEqual(adapt_dispatch_result(row)["status"], "success")

    def test_two_confirmations_preserve_positive(self):
        row = self.receipt(delivery="confirmed")
        row["result"]["delivery"] = "confirmed"
        self.assertEqual(adapt_dispatch_result(row)["status"], "success")

    def test_raw_evidence_is_preserved_and_independent(self):
        row = self.receipt(delivery="confirmed")
        row["result"]["delivery"] = "ambiguous"
        original = deepcopy(row)
        result = adapt_dispatch_result(row)
        self.assertEqual(row, original)
        self.assertEqual(result["raw_dispatch"], original)
        result["raw_dispatch"]["result"]["partial_effects"].append("copy-only")
        self.assertEqual(row, original)
        self.assertEqual(result["partial_effects"], ["retained"])

    def test_unscored_completion_remains_unscored(self):
        row = self.receipt(delivery="confirmed")
        row["result"].pop("task_success")
        result = adapt_dispatch_result(row)
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["task_success"])
        self.assertEqual(result["usage_status"], "unavailable")
        self.assertFalse(result["authority_granted"])

    def test_cleanup_error_still_cannot_succeed(self):
        row = self.receipt(delivery="confirmed", cleanup_error="close failed")
        row["result"]["delivery"] = "confirmed"
        result = adapt_dispatch_result(row)
        self.assertEqual(result["status"], "cleanup_failed")
        self.assertFalse(result["task_success"])

    def test_bad_delivery_types_are_reported_not_raised(self):
        for value in (False, 0, [], {}):
            row = self.receipt(delivery="confirmed")
            row["result"]["delivery"] = value
            result = adapt_dispatch_result(row)
            self.assertEqual(result["status"], "refused")
            self.assertEqual(result["diagnostic"], "UNKNOWN_DELIVERY:INVALID_TYPE:result.delivery")
            self.assertEqual(result["raw_dispatch"], row)

    def test_unknown_lifecycle_remains_refused(self):
        self.assertEqual(adapt_dispatch_result(self.receipt(), lifecycle=["not_known"])["adapter_error"],
                         "UNKNOWN_LIFECYCLE")


if __name__ == "__main__":
    unittest.main()
