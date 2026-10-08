import unittest

from candidate import classify


class LifecycleTests(unittest.TestCase):
    def test_output_without_receipt_is_not_completed(self):
        self.assertEqual(classify({"frozen": True, "candidate_receipt": None, "auditor_receipt": None, "raw_present": True}), "STOP_OUTPUT_WITHOUT_INVOCATION_RECEIPT")

    def test_zero_invocations_and_no_output_is_pre_run(self):
        self.assertEqual(classify({"frozen": True, "candidate_receipt": None, "auditor_receipt": None, "raw_present": False}), "PRE_RUN")

    def test_candidate_only_is_not_audited_completion(self):
        row = {"frozen": True, "raw_present": True, "raw_sha256": "a", "candidate_receipt": {"exit": 0, "raw_sha256": "a"}, "auditor_receipt": None}
        self.assertEqual(classify(row), "CANDIDATE_ONLY")

    def test_hash_disagreement_holds(self):
        row = {"frozen": True, "raw_present": True, "raw_sha256": "a", "candidate_receipt": {"exit": 0, "raw_sha256": "a"}, "auditor_receipt": {"candidate_raw_sha256": "b", "exit": 0, "errors": []}}
        self.assertEqual(classify(row), "HOLD_AUDIT_INPUT_HASH_MISMATCH")


if __name__ == "__main__":
    unittest.main()
