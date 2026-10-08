import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidate import run
from independent_audit import audit


class PresnapshotT0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_baseline_audits_with_planted_distinction(self):
        self.assertEqual(audit(self.result)["status"], "PASS_METHOD_SCOPED")

    def test_safety_release_precedes_and_skips_capture(self):
        row = next(r for r in self.result["rows"] if r["scenario"] == "hazard_held" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        self.assertEqual(row["events"][0], "safe_release_or_stop")
        self.assertIsNone(row["snapshot"])
        self.assertEqual(row["disposition"], "SNAPSHOT_SKIPPED_SAFETY")

    def test_minimal_capture_preserves_cause_signal_immediate_does_not(self):
        rows = {(r["scenario"], r["policy"]): r for r in self.result["rows"] if r["seed"] == 0}
        self.assertIsNone(rows[("cause_a", "IMMEDIATE_RECOVER")]["diagnosis_signal"])
        self.assertEqual(rows[("cause_a", "PRE_RECOVERY_MINIMAL_CAPTURE")]["diagnosis_signal"], "transient_focus_loss")

    def test_null_cause_does_not_generate_diagnosis(self):
        row = next(r for r in self.result["rows"] if r["seed"] == 0 and r["scenario"] == "null_cause" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        self.assertIsNone(row["diagnosis_signal"])

    def test_stale_source_missing_receipt_and_observer_perturbation_hold(self):
        for scenario in ("stale_source", "lost_receipt", "observer_perturbation"):
            row = next(r for r in self.result["rows"] if r["seed"] == 0 and r["scenario"] == scenario and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
            self.assertIsNone(row["snapshot"])
            self.assertTrue(row["recovery_completed"])

    def test_overcollection_is_detected_as_negative_control(self):
        row = next(r for r in self.result["rows"] if r["seed"] == 0 and r["scenario"] == "cause_a" and r["policy"] == "CAPTURE_EVERYTHING")
        self.assertEqual(row["disposition"], "CAPTURED_OVERBROAD")
        self.assertIn("private_payload", row["snapshot"])
        self.assertEqual(row["capture_cost"], 9)
        self.assertTrue(row["deadline_missed"])

    def test_minimal_capture_fits_synthetic_budget(self):
        row = next(r for r in self.result["rows"] if r["seed"] == 0 and r["scenario"] == "cause_a" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        self.assertEqual((row["capture_cost"], row["slack_budget"], row["deadline_missed"]), (1, 2, False))

    def test_auditor_rejects_capture_before_safety_gate(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "hazard_held" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["snapshot"] = {"source_id": row["source_id"], "failure_id": "f", "authority": False}
        row["disposition"] = "CAPTURED_MINIMAL"
        self.assertEqual(audit(mutant)["status"], "FAIL_METHOD")

    def test_auditor_rejects_forged_diagnosis(self):
        mutant = copy.deepcopy(self.result)
        row = next(r for r in mutant["rows"] if r["scenario"] == "null_cause" and r["policy"] == "PRE_RECOVERY_MINIMAL_CAPTURE")
        row["diagnosis_signal"] = "forged"
        self.assertEqual(audit(mutant)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
