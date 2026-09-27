from __future__ import annotations

import unittest

from lifetime_experiment import lifetime_classify, make_receipt
from typed_validator_881 import EXACT_MATCH, INVALID, MISMATCH, classify


IDENTITY = {
    "backend": {"state": "KNOWN", "value": "x11"},
    "top_level_client_id": {"state": "KNOWN", "value": 2097152},
    "transient_for": {"state": "KNOWN_NULL"},
}


class LifetimeExperimentTests(unittest.TestCase):
    def test_exact_merged_validator_same_generation(self):
        receipt = make_receipt(IDENTITY, "g1")
        self.assertEqual(classify(receipt, IDENTITY)["classification"], EXACT_MATCH)

    def test_lifetime_bound_accepts_same_generation(self):
        receipt = make_receipt(IDENTITY, "g1")
        ledger = {receipt["receipt_id"]: "g1"}
        got = lifetime_classify(receipt, IDENTITY, "g1", ledger)
        self.assertEqual(got["classification"], "ACCEPT")

    def test_lifetime_bound_rejects_cross_generation(self):
        receipt = make_receipt(IDENTITY, "g1")
        ledger = {receipt["receipt_id"]: "g1"}
        got = lifetime_classify(receipt, IDENTITY, "g2", ledger)
        self.assertEqual(got["reason"], "server_instance_mismatch")

    def test_forged_token_fails_closed(self):
        receipt = make_receipt(IDENTITY, "g1")
        ledger = {receipt["receipt_id"]: "g1"}
        receipt["server_instance_id"] = "g2"
        got = lifetime_classify(receipt, IDENTITY, "g2", ledger)
        self.assertEqual(got["reason"], "receipt_token_forged_or_changed")

    def test_missing_token_fails_closed(self):
        receipt = make_receipt(IDENTITY, "g1")
        ledger = {receipt["receipt_id"]: "g1"}
        del receipt["server_instance_id"]
        self.assertEqual(lifetime_classify(receipt, IDENTITY, "g1", ledger)["classification"], "REJECT")

    def test_authority_escalation_is_invalid(self):
        receipt = make_receipt(IDENTITY, "g1")
        receipt["authority"] = "task-input"
        self.assertEqual(classify(receipt, IDENTITY)["classification"], INVALID)

    def test_changed_backend_and_client_mismatch(self):
        receipt = make_receipt(IDENTITY, "g1")
        receipt["identity"] = {**IDENTITY, "backend": {"state": "KNOWN", "value": "win32"}}
        self.assertEqual(classify(receipt, IDENTITY)["classification"], MISMATCH)
        receipt["identity"] = {**IDENTITY,
                               "top_level_client_id": {"state": "KNOWN", "value": 7}}
        self.assertEqual(classify(receipt, IDENTITY)["classification"], MISMATCH)

    def test_known_transient_mismatch(self):
        receipt = make_receipt(IDENTITY, "g1")
        receipt["identity"] = {**IDENTITY, "transient_for": {"state": "KNOWN", "value": 123}}
        self.assertEqual(classify(receipt, IDENTITY)["classification"], MISMATCH)


if __name__ == "__main__":
    unittest.main()
