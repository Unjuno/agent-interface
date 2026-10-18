import gzip
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent


class RetainedV1EvidenceTests(unittest.TestCase):
    def test_failed_audit_is_not_promoted(self):
        result = json.loads((ROOT / "audit.json").read_text())
        self.assertEqual(result["status"], "METHOD_FAIL_OR_INCONCLUSIVE")
        self.assertEqual(result["groups"], 504)
        self.assertEqual(len(result["errors"]), 217)
        self.assertEqual(len(result["reversal_cells"]), 16)
        self.assertEqual(result["control_reversal_counts"]["no_imitation"], 8)
        self.assertEqual(result["control_reversal_counts"]["partitioned"], 8)

    def test_compressed_raw_is_lossless_and_hash_bound(self):
        with gzip.open(ROOT / "candidate-raw.json.gz", "rb") as stream:
            digest = hashlib.sha256(stream.read()).hexdigest()
        self.assertEqual(digest, "e45f5b74b68fe17c1a4f456dacc59fa8895d3d80f9320736495ff39a71be1098")


if __name__ == "__main__":
    unittest.main()
