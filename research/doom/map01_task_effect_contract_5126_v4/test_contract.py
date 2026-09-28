import copy
import json
import tempfile
import unittest
from pathlib import Path
from audit import audit, ALLOCATION, PINNED_SHA
from run import make_rows


class V4AuditIntegrityTests(unittest.TestCase):
    def document(self):
        digest, rows = make_rows()
        return {"schema": "map01-task-effect-contract-result-v5", "allocation": ALLOCATION,
                "issue": 5126, "input_corpus_sha256": digest, "input_authority": False,
                "live_calls": 0, "cases": rows}

    def check(self, doc):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "result.json"
            p.write_text(json.dumps(doc))
            return audit(p)

    def test_positive(self):
        self.assertEqual(self.check(self.document())["status"], "PASS_PINNED_CORPUS_AND_EFFECT_LINEAGE")

    def test_stale_digest_cannot_hide_substituted_raw_case(self):
        doc = self.document()
        doc["cases"][0]["raw"]["session_id"] = "substituted"
        result = self.check(doc)
        self.assertIn("corpus_rows_mismatch", result["errors"])

    def test_candidate_and_oracle_same_corrupt_effect_id_rejected(self):
        doc = self.document()
        for key in ("candidate", "oracle"):
            doc["cases"][0][key]["effect_id"] = "forged"
        result = self.check(doc)
        self.assertIn("candidate_effect_identity:valid_positive", result["errors"])
        self.assertIn("oracle_effect_identity:valid_positive", result["errors"])


if __name__ == "__main__":
    unittest.main()
