"""Regression and corruption controls for the independent #3240 raw auditor."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from research.integration.gtk_effect_control_3240_v2.audit_raw import audit


EVIDENCE = (Path(__file__).parents[1] / "gtk_effect_control_3240_v1" /
            "evidence" / "formal01")


class AuditRawTests(unittest.TestCase):
    def test_corrected_native_status_preserves_historical_hold(self):
        result = audit(EVIDENCE)
        self.assertEqual(result["decision"], "HOLD_EVIDENCE_OR_EFFECT_BOUNDARY")
        self.assertEqual(result["errors"], ["untouched_target_pixels_changed"])
        positive = result["rows"][0]
        self.assertEqual(positive["native_status_by_stage"],
                         {"prep": "completed", "action": "completed"})
        self.assertEqual(positive["adapter_status"], "partial")

    def test_native_status_corruption_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "formal01"
            shutil.copytree(EVIDENCE, copied)
            path = copied / "01_application_save" / "adapter-action.json"
            receipt = json.loads(path.read_text())
            receipt["raw_dispatch"]["result"]["status"] = "failed"
            path.write_text(json.dumps(receipt))
            self.assertIn("adapter_native_execution_incomplete:action",
                          audit(copied)["errors"])

    def test_preparation_receipt_is_audited(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "formal01"
            shutil.copytree(EVIDENCE, copied)
            path = copied / "01_application_save" / "adapter-prep.json"
            receipt = json.loads(path.read_text())
            receipt["raw_dispatch"]["result"]["status"] = "failed"
            path.write_text(json.dumps(receipt))
            self.assertIn("adapter_native_execution_incomplete:prep", audit(copied)["errors"])

    def test_target_image_hash_corruption_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "formal01"
            shutil.copytree(EVIDENCE, copied)
            path = copied / "02_render_only_decoy" / "row.json"
            row = json.loads(path.read_text())
            row["target_initial_sha256"] = "0" * 64
            path.write_text(json.dumps(row))
            self.assertIn("raw_image_hash_mismatch:02_render_only_decoy:target_initial_sha256",
                          audit(copied)["errors"])

    def test_measured_untouched_preimage_is_bound_to_raw_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "formal01"
            shutil.copytree(EVIDENCE, copied)
            path = copied / "02_render_only_decoy" / "row.json"
            row = json.loads(path.read_text())
            row["target_pre_sha256"] = row["target_post_sha256"]
            path.write_text(json.dumps(row))
            self.assertIn("raw_image_hash_mismatch:02_render_only_decoy:target_pre_sha256",
                          audit(copied)["errors"])


if __name__ == "__main__":
    unittest.main()
