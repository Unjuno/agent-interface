import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditor import audit, load_parent, load_parent_bytes


class LineageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_parent()

    def test_parent_candidate_passes_corrected_lineage_audit(self):
        self.assertEqual(audit(self.result)["status"], "PASS_AUDIT_LINEAGE_SCOPED")

    def test_wrong_failure_id_rejected(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "cause_a" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["snapshot"]["failure_id"] = "other-failure"
        self.assertIn("snapshot failure ID mismatch", " ".join(audit(mutant)["errors"]))

    def test_wrong_receipt_id_rejected(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "cause_b" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["snapshot"]["receipt_id"] = "other-receipt"
        self.assertIn("snapshot receipt ID mismatch", " ".join(audit(mutant)["errors"]))

    def test_forged_captured_signal_rejected(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "cause_a" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["snapshot"]["signal"] = "invented"
        self.assertIn("captured signal differs", " ".join(audit(mutant)["errors"]))

    def test_diagnosis_not_bound_to_capture_rejected(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "cause_a" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["snapshot"]["signal"] = "invented"
        row["diagnosis_signal"] = "transient_focus_loss"
        self.assertIn("promoted diagnosis is not bound", " ".join(audit(mutant)["errors"]))

    def test_minimal_capture_extra_private_field_rejected(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "null_cause" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["snapshot"]["private_payload"] = "secret"
        self.assertIn("minimal capture contains unexpected fields", " ".join(audit(mutant)["errors"]))

    def test_null_cause_never_promoted(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "null_cause" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["diagnosis_signal"] = "fabricated"
        self.assertIn("diagnosis unsupported", " ".join(audit(mutant)["errors"]))

    def test_safety_gate_rejects_capture(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "hazard_held" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["snapshot"] = {"failure_id": "f", "source_id": row["source_id"], "receipt_id": "r", "signal": None, "authority": False}
        self.assertIn("safety/privacy gate", " ".join(audit(mutant)["errors"]))

    def test_changed_parent_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            data = (Path(__file__).resolve().parent.parent / "candidate_result.json").read_bytes() + b"x"
            load_parent_bytes(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
