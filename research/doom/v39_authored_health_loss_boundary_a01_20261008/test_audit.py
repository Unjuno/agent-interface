import copy
import hashlib
import json
import unittest
from pathlib import Path

from .audit import validate


class AuthoredHealthBoundaryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((Path(__file__).parent / "RESULT.json").read_text(encoding="utf-8"))

    def test_candidate_result_matches_independent_full_sweep(self):
        self.assertTrue(validate(self.result))
        self.assertEqual(self.result["rows"][12]["triage_value_84"]["status"], "HARD_INVALIDATED")
        self.assertEqual(self.result["rows"][16]["triage_value_84"]["status"], "SOFT_CHANGED")
        self.assertEqual(self.result["rows"][20]["triage_value_84"]["status"], "SOFT_CHANGED")

    def test_mutated_result_claims_are_rejected(self):
        mutations = [
            lambda r: r.update(main_commit="0" * 40),
            lambda r: r["rows"][12].update(hard_minimum=80),
            lambda r: r["rows"][16]["triage_value_84"].update(status="HARD_INVALIDATED"),
            lambda r: r["rows"][16]["exact_floor"].update(requires_new_decision=True),
            lambda r: r["rows"].append(copy.deepcopy(r["rows"][-1])),
            lambda r: r.update(pending_model=1),
            lambda r: r.update(synthetic_typed_health_source=100.0),
            lambda r: r.update(maximum_health_loss_values=[0.0, 20.0]),
            lambda r: r["rows"][1].update(maximum_health_loss=True),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                altered = copy.deepcopy(self.result)
                mutate(altered)
                with self.assertRaises(ValueError):
                    validate(altered)

    def test_corrected_audit_binds_exact_result_bytes_and_preserves_original(self):
        root = Path(__file__).parent
        result_bytes = (root / "RESULT.json").read_bytes()
        audit = json.loads((root / "AUDIT.json").read_text(encoding="utf-8"))
        original = json.loads((root / "AUDIT_A01.json").read_text(encoding="utf-8"))

        self.assertEqual(audit["schema"],
                         "issue59-authored-health-loss-boundary-audit-v2")
        self.assertEqual(audit["result_hash_encoding"],
                         "exact committed RESULT.json bytes")
        self.assertEqual(audit["result_sha256"], hashlib.sha256(result_bytes).hexdigest())
        self.assertEqual(audit["supersedes"], "AUDIT_A01.json")
        self.assertEqual(original["result_sha256"], hashlib.sha256(
            result_bytes.replace(b"\r\n", b"\n")).hexdigest())


    def test_manifest_matches_exact_package_bytes(self):
        root = Path(__file__).parent
        manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "issue59-authored-health-loss-boundary-manifest-v3")
        expected = {"AUDIT.json", "AUDIT_A01.json", "MANIFEST_A01.json", "README.md", "RESULT.json",
                    "RUN_COMMAND.txt", "audit.py", "candidate.py", "test_audit.py", "FREEZE.json"}
        entries = manifest["files"]
        self.assertEqual({row["path"] for row in entries}, expected)
        for row in entries:
            data = (root / row["path"]).read_bytes()
            with self.subTest(path=row["path"]):
                self.assertEqual(len(data), row["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])
if __name__ == "__main__":
    unittest.main(verbosity=2)
