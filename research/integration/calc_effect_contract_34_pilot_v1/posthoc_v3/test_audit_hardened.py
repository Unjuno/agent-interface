from __future__ import annotations

import base64
import json
import pathlib
import tempfile
import unittest

from audit_hardened import disposition, evidence_errors, read_workbook


class HardenedAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = {
            "allocation": "calc-effect-contract-34-pilot-20260927-01",
            "image": "issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393",
            "source_file": "baseline.xlsx",
            "program_completed": True,
            "cell_before_edit": 0,
            "cell_after_edit_live": 7,
            "document_modified_unsaved": True,
            "save_store_calls": 0,
            "raw_classifications": {"program_terminal_shortcut":"VERIFIED","live_required_effect_shortcut":"VERIFIED","saved_effect_contract":"CONTRADICTED"},
            "persisted_cell_after_independent_reopen": 0,
            "visible_calc_window_ids": ["0x123"],
        }

    def test_well_formed_evidence_has_no_errors(self):
        self.assertEqual(evidence_errors(self.raw, 0, True), [])

    def test_missing_classification_stops(self):
        self.assertIn("shortcut/saved-effect classification missing or inconsistent", evidence_errors(dict(self.raw, raw_classifications=None), 0, True))

    def test_changed_classification_stops(self):
        self.assertIn("shortcut/saved-effect classification missing or inconsistent", evidence_errors(dict(self.raw, raw_classifications={}), 0, True))

    def test_missing_visibility_stops(self):
        self.assertTrue(evidence_errors({k:v for k,v in self.raw.items() if k!="visible_calc_window_ids"}, 0, True))

    def test_null_visibility_stops(self):
        self.assertTrue(evidence_errors(dict(self.raw, visible_calc_window_ids=None), 0, True))

    def test_empty_visibility_stops(self):
        self.assertTrue(evidence_errors(dict(self.raw, visible_calc_window_ids=[]), 0, True))

    def test_wrong_visibility_type_stops(self):
        self.assertTrue(evidence_errors(dict(self.raw, visible_calc_window_ids="0x123"), 0, True))

    def test_malformed_xid_stops(self):
        self.assertTrue(evidence_errors(dict(self.raw, visible_calc_window_ids=["bad"]), 0, True))

    def test_any_validation_error_prevents_pass(self):
        self.assertEqual(disposition(["tampered field"]), "STOP_CONSTRUCTION")

    def test_invalid_pinned_image_stops(self):
        self.assertTrue(evidence_errors(dict(self.raw, image="different"), 0, True))

    def test_incomplete_harness_stops(self):
        self.assertTrue(evidence_errors(dict(self.raw, program_completed=False), 0, True))

    def test_base64_artifact_is_read_without_writing_xlsx(self):
        payload=b"retained-workbook-payload"
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); raw_path=root/"raw.json"
            raw_path.write_text(json.dumps({"source_file":"baseline.xlsx"}),encoding="utf-8")
            (root/"baseline.xlsx.b64").write_bytes(base64.b64encode(payload))
            restored, mode=read_workbook(raw_path,{"source_file":"baseline.xlsx"})
            self.assertEqual(mode,"base64"); self.assertEqual(restored,payload)


if __name__ == "__main__":
    unittest.main()
