import copy
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs" / "a02"
AUDITOR_PATH = ROOT / "auditor.py"
SPEC = (
    importlib.util.spec_from_file_location("a04_auditor", AUDITOR_PATH)
    if AUDITOR_PATH.is_file()
    else None
)
AUDITOR = None
if SPEC is not None and SPEC.loader is not None:
    AUDITOR = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(AUDITOR)


class ReceiptShapeSpecificAuditTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(AUDITOR, "A04 independent auditor is not implemented yet")
        self.evidence = AUDITOR.load_saved_evidence(INPUTS)

    def test_reconstructs_a02_failure_and_rejects_four_mutations(self):
        report = AUDITOR.audit_saved_evidence(INPUTS)
        self.assertEqual(report["status"], "PASS_AUDIT_ONLY_SCOPED")
        self.assertEqual(report["a02_decision"], "FAIL_AUDITOR_CONTRACT")
        self.assertEqual(report["mutation_controls_rejected"], 4)

    def test_candidate_cleanup_reads_top_level_absence_receipt(self):
        AUDITOR.validate_candidate_cleanup(self.evidence)

    def test_auditor_cleanup_reads_nested_exact_cid_absence_receipt(self):
        AUDITOR.validate_auditor_cleanup(self.evidence)

    def test_rejects_candidate_container_reported_present(self):
        changed = copy.deepcopy(self.evidence)
        changed["candidate_cleanup"]["absence_verified"] = False
        with self.assertRaisesRegex(ValueError, "candidate cleanup"):
            AUDITOR.validate_candidate_cleanup(changed)

    def test_rejects_auditor_container_reported_present_in_nested_receipt(self):
        changed = copy.deepcopy(self.evidence)
        exact = changed["auditor_cleanup"]["targeted_inspect_checks"][1]
        exact["absence_verified"] = False
        with self.assertRaisesRegex(ValueError, "auditor cleanup"):
            AUDITOR.validate_auditor_cleanup(changed)

    def test_rejects_input_changed_after_a04_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "a02"
            shutil.copytree(INPUTS, copy)
            fixture = copy / "fixture.txt"
            fixture.write_bytes(fixture.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "hash"):
                AUDITOR.load_saved_evidence(copy)

    def test_validates_frozen_a02_blobs_and_a04_sources(self):
        report = AUDITOR.verify_a04_freeze(ROOT)
        self.assertEqual(report["a02_inputs_checked"], 17)
        self.assertEqual(report["a04_sources_checked"], 4)

    def test_rejects_a02_input_with_wrong_git_blob_oid(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "a04"
            shutil.copytree(ROOT, copy)
            freeze_path = copy / "FREEZE.json"
            freeze = AUDITOR.json.loads(freeze_path.read_text(encoding="utf-8"))
            freeze["a02_git_blob_oids"]["fixture.txt"] = "0" * 40
            freeze_path.write_text(AUDITOR.json.dumps(freeze), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Git blob identity mismatch"):
                AUDITOR.verify_a04_freeze(copy)


if __name__ == "__main__":
    unittest.main()
