from __future__ import annotations

import base64
import json
import pathlib
import tempfile
import unittest

from audit_hardened import classify, read_workbook, visibility_state


class HardenedAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = {
            "allocation": "calc-effect-contract-34-window-gate-20260927-01",
            "image": "issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393",
            "harness_completed": True,
            "cell_after_edit_live": 7,
            "source_sha256_before": "same",
            "source_sha256_after": "same",
        }

    def test_confirmed_unmapped_is_contradiction(self):
        self.assertEqual(classify(self.raw, "IsUnMapped", 0, True, []), "CONTRADICTED_WINDOW_VISIBILITY")

    def test_confirmed_unviewable_is_contradiction(self):
        self.assertEqual(classify(self.raw, "IsUnviewable", 0, True, []), "CONTRADICTED_WINDOW_VISIBILITY")

    def test_missing_state_is_stop(self):
        self.assertEqual(classify(self.raw, "UNKNOWN", 0, True, []), "STOP_CONSTRUCTION")

    def test_viewable_expected_state_passes_scoped_gate(self):
        self.assertEqual(classify(self.raw, "IsViewable", 0, True, []), "PASS_WINDOW_GATED_CONSTRUCTION_ONLY")

    def test_validation_error_prevents_pass(self):
        self.assertEqual(classify(self.raw, "IsViewable", 0, True, ["tampered evidence"]), "STOP_CONSTRUCTION")

    def test_wrong_image_prevents_classification(self):
        raw = dict(self.raw, image="other-image")
        self.assertEqual(classify(raw, "IsUnMapped", 0, True, []), "STOP_CONSTRUCTION")

    def test_incomplete_harness_prevents_classification(self):
        raw = dict(self.raw, harness_completed=False)
        self.assertEqual(classify(raw, "IsViewable", 0, True, []), "STOP_CONSTRUCTION")

    def test_effect_mismatch_is_contradiction(self):
        self.assertEqual(classify(self.raw, "IsViewable", 1, True, []), "CONTRADICTED_EFFECT_STATE")

    def test_reads_base64_only_publication_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            raw_path = root / "raw.json"
            raw_path.write_text(json.dumps({"source_file": "baseline.xlsx"}), encoding="utf-8")
            payload = b"retained-xlsx-payload"
            (root / "baseline.xlsx.b64").write_bytes(base64.b64encode(payload))
            data, mode = read_workbook(raw_path, {"source_file": "baseline.xlsx"})
            self.assertEqual(mode, "base64")
            self.assertEqual(data, payload)

    def test_visibility_parser_distinguishes_unmapped(self):
        tree = '{"exit":0,"stdout":"0x123 \\"VCL ImplGetDefaultWindow\\": ()\\n"}'
        attrs = '{"exit":0,"stdout":"Window id: 0x123 \\"VCL ImplGetDefaultWindow\\"\\nMap State: IsUnMapped\\n"}'
        raw = {"xwininfo_root_tree": tree, "vcl_window_id": "0x123", "xwininfo_window_attributes": attrs}
        self.assertEqual(visibility_state(raw), "IsUnMapped")


if __name__ == "__main__":
    unittest.main()
