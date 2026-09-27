import tempfile
import unittest
from pathlib import Path

import audit


class StopEvidenceAuditTests(unittest.TestCase):
    def test_preserved_stop_is_hash_bound_and_zero_step(self):
        result = audit.audit()
        self.assertEqual(result["status"], "PASS_STOP_EVIDENCE_INTEGRITY")
        self.assertEqual(result["formal_training_steps"], 0)
        self.assertFalse(result["raw_result_present"])

    def test_trace_must_contain_deterministic_operator_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in audit.FILES + ("EVIDENCE_SHA256SUMS.txt",):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((audit.ROOT / rel).read_bytes())
            target = root / "evidence/CONSTRUCTION.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((audit.ROOT / "evidence/CONSTRUCTION.json").read_bytes())
            target = root / "SHA256SUMS.txt"
            target.write_bytes((audit.ROOT / "SHA256SUMS.txt").read_bytes())
            trace = root / "evidence/traceback.txt"
            trace.write_text("unrelated error\n", encoding="utf-8")
            result = audit.audit(root)
            self.assertIn("canonical CUDA failure evidence missing", result["errors"])

    def test_declared_artifact_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in audit.FILES + ("SHA256SUMS.txt", "EVIDENCE_SHA256SUMS.txt"):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((audit.ROOT / rel).read_bytes())
            target = root / "evidence/CONSTRUCTION.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((audit.ROOT / "evidence/CONSTRUCTION.json").read_bytes())
            target = root / "evidence/stdout.txt"
            target.write_text("preserve", encoding="utf-8")
            with (root / "environment.json").open("a", encoding="utf-8") as stream:
                stream.write(" ")
            result = audit.audit(root)
            self.assertTrue(any("file digest mismatch: environment.json" == e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
