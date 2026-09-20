import json
import tempfile
import unittest
from pathlib import Path

import audit_raw


REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = (
    REPO_ROOT
    / "research/integration/issue_3188_source_bound_entry_gate_v1/results/formal-02/raw.json"
)


class RawReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_bytes = RAW_PATH.read_bytes()
        cls.frozen_bytes, _ = audit_raw.exact_bytes_for_frozen_digest(
            cls.raw_bytes, audit_raw.EXPECTED_RAW_SHA256
        )

    def test_canonical_reconstruction(self):
        result = audit_raw.reconstruct(self.raw_bytes)
        self.assertEqual(result["status"], "PASS_RAW_RECONSTRUCTION")
        self.assertEqual(result["rows"], 37)
        self.assertEqual(result["authorize"], 1)
        self.assertEqual(result["current_snapshot"], "HOLD")

    def test_all_frozen_inputs_match(self):
        modes = audit_raw.verify_frozen_inputs(REPO_ROOT)
        self.assertEqual(set(modes), {"raw.json", "PREREG-FORMAL-02.md", "run.py", "audit.py"})

    def test_corruption_controls_rejected(self):
        controls = audit_raw.corruption_challenges(self.raw_bytes)
        self.assertEqual(set(controls), {"vector_bit", "row_count", "class_label", "control_admission", "digest"})
        self.assertTrue(all(controls.values()), controls)

    def test_reordered_vectors_rejected(self):
        value = json.loads(self.frozen_bytes)
        value["vectors"][0], value["vectors"][1] = value["vectors"][1], value["vectors"][0]
        with self.assertRaises(audit_raw.AuditError):
            audit_raw.reconstruct(json.dumps(value).encode())

    def test_boolean_is_not_accepted_as_integer_substitute(self):
        value = json.loads(self.frozen_bytes)
        value["vectors"][0][audit_raw.FIELDS[0]] = 1
        with self.assertRaises(audit_raw.AuditError):
            audit_raw.reconstruct(json.dumps(value).encode())

    def test_pretty_reformatted_but_semantically_same_raw_is_digest_rejected(self):
        value = json.loads(self.frozen_bytes)
        with self.assertRaises(audit_raw.AuditError):
            audit_raw.reconstruct(json.dumps(value, indent=2).encode())

    def test_source_substitution_rejected_by_frozen_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in (
                "research/integration/issue_3188_source_bound_entry_gate_v1/results/formal-02/raw.json",
                "research/integration/issue_3188_source_bound_entry_gate_v1/PREREG-FORMAL-02.md",
                "research/analysis/map01_matched_recovery_entry_gate_3008_v2/run.py",
                "research/analysis/map01_matched_recovery_entry_gate_3008_v2/audit.py",
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((REPO_ROOT / relative).read_bytes())
            target = root / "research/analysis/map01_matched_recovery_entry_gate_3008_v2/run.py"
            target.write_bytes(target.read_bytes() + b"# substituted\n")
            with self.assertRaises(audit_raw.AuditError):
                audit_raw.verify_frozen_inputs(root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
