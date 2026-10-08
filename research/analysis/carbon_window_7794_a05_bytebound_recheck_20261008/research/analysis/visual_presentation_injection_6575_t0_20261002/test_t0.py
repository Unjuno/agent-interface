import json
import hashlib
import tempfile
import unittest
from pathlib import Path

import audit
import candidate
import make_fixtures


class PresentationT0Tests(unittest.TestCase):
    def setUp(self):
        prepared = json.loads(json.dumps(candidate.FREEZE))
        prepared["status"] = "AUTHORIZED"
        prepared["resource_assignment_record"] = "construction-test-only; no resource assignment"
        for rel in prepared["source_sha256"]:
            prepared["source_sha256"][rel] = hashlib.sha256((candidate.ROOT / rel).read_bytes()).hexdigest()
        candidate.FREEZE = prepared
        audit.FREEZE = prepared

    @classmethod
    def setUpClass(cls):
        make_fixtures.main()

    def test_candidate_and_independent_auditor_accept_frozen_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            candidate.main(out)
            result = audit.audit(out)
            self.assertTrue(result["passed"], result)
            self.assertEqual(result["decision"], "PASS_METHOD_SCOPED")
            self.assertEqual(result["rows"], 18)

    def test_auditor_rejects_mutated_crop_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            candidate.main(out)
            doc_path = out / "candidate.json"
            doc = json.loads(doc_path.read_text())
            payload = out / doc["rows"][1]["views"][0]["file"]
            raw = bytearray(payload.read_bytes()); raw[-1] ^= 1; payload.write_bytes(raw)
            self.assertFalse(audit.audit(out)["passed"])

    def test_auditor_rejects_omitted_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            candidate.main(out)
            path = out / "candidate.json"
            doc = json.loads(path.read_text()); doc["rows"].pop()
            path.write_text(json.dumps(doc))
            self.assertFalse(audit.audit(out)["passed"])


if __name__ == "__main__":
    unittest.main()
