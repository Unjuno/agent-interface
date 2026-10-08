import json
from pathlib import Path
import tempfile
import unittest

from recovery import recover

def receipt(sequence, check, value=True, generation=1):
    return dict(sequence=sequence, check=check, value=value, generation=generation, scope="synthetic-claim")

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "receipts.jsonl"

    def write(self, rows, torn=b""):
        self.path.write_bytes(b"".join((json.dumps(row) + "\n").encode() for row in rows) + torn)

    def test_complete_current_prefix_survives_restart(self):
        self.write([receipt(1, "identity"), receipt(2, "freshness"), receipt(3, "effect")])
        result = recover(self.path)
        self.assertEqual(result["disposition"], "COMPLETE_VERDICT")
        self.assertEqual(result["missing"], [])

    def test_decisive_current_identity_negative_can_reject(self):
        self.write([receipt(1, "identity", False)])
        self.assertEqual(recover(self.path)["disposition"], "COUNTEREXAMPLE")

    def test_partial_positive_reports_missing_effect(self):
        self.write([receipt(1, "identity"), receipt(2, "freshness")])
        result = recover(self.path)
        self.assertEqual(result["disposition"], "PARTIAL_UNKNOWN")
        self.assertEqual(result["completed"], ["identity", "freshness"])
        self.assertEqual(result["missing"], ["effect"])

    def test_torn_tail_never_completes_missing_effect(self):
        self.write([receipt(1, "identity"), receipt(2, "freshness")], b'{"sequence":3')
        result = recover(self.path)
        self.assertEqual(result["disposition"], "PARTIAL_UNKNOWN")
        self.assertEqual(result["completed"], ["identity", "freshness"])

    def test_generation_replacement_discards_reuse(self):
        self.write([receipt(1, "identity")])
        self.assertEqual(recover(self.path, generation=2)["completed"], [])

    def test_duplicate_receipt_refuses_the_entire_stream(self):
        self.write([receipt(1, "identity"), receipt(2, "identity")])
        self.assertEqual(recover(self.path)["completed"], [])

    def test_boolean_sequence_is_not_an_integer_identity(self):
        self.write([receipt(True, "identity")])
        self.assertEqual(recover(self.path)["completed"], [])

    def test_corrupt_complete_record_is_not_a_torn_tail(self):
        self.path.write_bytes(b'{"sequence":1\n')
        self.assertEqual(recover(self.path)["completed"], [])

if __name__ == "__main__":
    unittest.main()
