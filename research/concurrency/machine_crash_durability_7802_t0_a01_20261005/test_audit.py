import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import audit
import candidate


class MachineCrashModelTests(unittest.TestCase):
    def test_candidate_matches_independent_audit(self):
        expected = {
            "effect_then_receipt_separate_domains": ["NO_EFFECT_CONFIRMED", "UNKNOWN_RECONCILE", "EFFECT_AND_RECEIPT_CONFIRMED"],
            "receipt_then_effect_separate_domains": ["NO_EFFECT_CONFIRMED", "UNKNOWN_RECONCILE", "EFFECT_AND_RECEIPT_CONFIRMED"],
            "effect_and_receipt_single_atomic_transaction": ["NO_EFFECT_CONFIRMED", "EFFECT_AND_RECEIPT_CONFIRMED"],
            "effect_commit_then_ack_before_receipt": ["NO_EFFECT_CONFIRMED", "UNKNOWN_RECONCILE", "EFFECT_AND_RECEIPT_CONFIRMED"],
            "corrupt_or_untrusted_record": ["NO_EFFECT_CONFIRMED", "UNKNOWN_RECONCILE", "CORRUPT_OR_UNTRUSTED", "EFFECT_AND_RECEIPT_CONFIRMED"],
        }
        actual = {name: [row["classification"] for row in candidate.enumerate_protocol(name)] for name in expected}
        self.assertEqual(actual, expected)

    def test_auditor_rejects_false_no_effect_and_retry_authority(self):
        data = {"schema": "machine-crash-durability-7802-candidate-v1",
                "rows": {name: candidate.enumerate_protocol(name) for name in (
                    "effect_then_receipt_separate_domains", "receipt_then_effect_separate_domains",
                    "effect_and_receipt_single_atomic_transaction", "effect_commit_then_ack_before_receipt",
                    "corrupt_or_untrusted_record")}}
        row = data["rows"]["effect_then_receipt_separate_domains"][1]
        row["classification"] = "NO_EFFECT_CONFIRMED"
        row["retry_authorized"] = True
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "mutant.json"
            path.write_text(json.dumps(data))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = audit.main(path)
        report = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("effect_then_receipt_separate_domains:row-1", report["errors"])


if __name__ == "__main__":
    unittest.main()
