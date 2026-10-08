from __future__ import annotations

import base64
import pathlib
import tempfile
import unittest

from audit_hardened import (
    ALLOCATION,
    DOCUMENT_TITLE,
    IMAGE,
    VCL_TITLE,
    audit_values,
    read_xlsx,
)


class PosthocAuditTests(unittest.TestCase):
    def setUp(self):
        self.source_hash = "source-sha"
        doc_state = "IsViewable"
        root = f'''xwininfo: Window id: 0x50d (the root window) (has no name)

  Root window id: 0x50d (the root window) (has no name)
     2 children:
     0x101 "{DOCUMENT_TITLE}": ("libreoffice" "libreoffice-calc") 1280x800+0+0
     0x102 "{VCL_TITLE}": ("libreoffice" "LibreOffice 7.4") 1280x800+0+0
'''
        def attrs(wid, title, state):
            return {
                "window_id": wid,
                "exit": 0,
                "stdout": f'\nxwininfo: Window id: {wid} "{title}"\n\n  Map State: {state}\n',
            }
        self.raw = {
            "schema": "calc-effect-contract-document-window-raw-v1",
            "allocation": ALLOCATION,
            "image": IMAGE,
            "source_file": "document-window-probe.xlsx",
            "harness_completed": True,
            "cell_before_edit": 0,
            "cell_after_edit_live": 7,
            "document_modified_unsaved": True,
            "save_store_calls": 0,
            "persisted_cell_after_independent_reopen": 0,
            "source_sha256_before": self.source_hash,
            "source_sha256_after": self.source_hash,
            "root_tree": {"exit": 0, "stdout": root},
            "root_child_ids": ["0x101", "0x102"],
            "child_window_attributes": [attrs("0x101", DOCUMENT_TITLE, doc_state), attrs("0x102", VCL_TITLE, "IsUnMapped")],
        }
        self.frozen = {
            "schema": "calc-effect-contract-document-window-audit-v1",
            "raw_sha256": "raw-sha",
            "source_sha256_independent": self.source_hash,
            "independently_reopened_A1": 0,
        }

    def evaluate(self, raw=None, frozen=None, disk=0, source_hash=None, raw_hash="raw-sha", frozen_hash="frozen-sha"):
        return audit_values(raw or self.raw, frozen or self.frozen, disk,
                            self.source_hash if source_hash is None else source_hash,
                            raw_hash, frozen_hash)

    def test_valid_retained_evidence_passes_scoped_gate(self):
        result = self.evaluate()
        self.assertEqual(result["disposition"], "PASS_DOCUMENT_WINDOW_VISIBLE_CONSTRUCTION_ONLY")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["frozen_audit_sha256"], "frozen-sha")

    def test_unmapped_document_is_contradiction(self):
        raw = {**self.raw, "child_window_attributes": list(self.raw["child_window_attributes"])}
        raw["child_window_attributes"][0] = {**raw["child_window_attributes"][0], "stdout": raw["child_window_attributes"][0]["stdout"].replace("IsViewable", "IsUnMapped")}
        self.assertEqual(self.evaluate(raw=raw)["disposition"], "CONTRADICTED_DOCUMENT_WINDOW_VISIBILITY")

    def test_unviewable_document_is_contradiction(self):
        raw = {**self.raw, "child_window_attributes": list(self.raw["child_window_attributes"])}
        raw["child_window_attributes"][0] = {**raw["child_window_attributes"][0], "stdout": raw["child_window_attributes"][0]["stdout"].replace("IsViewable", "IsUnviewable")}
        self.assertEqual(self.evaluate(raw=raw)["disposition"], "CONTRADICTED_DOCUMENT_WINDOW_VISIBILITY")

    def test_wrong_image_stops(self):
        self.assertEqual(self.evaluate(raw={**self.raw, "image": "other"})["disposition"], "STOP_CONSTRUCTION")

    def test_wrong_allocation_stops(self):
        self.assertEqual(self.evaluate(raw={**self.raw, "allocation": "other"})["disposition"], "STOP_CONSTRUCTION")

    def test_incomplete_harness_stops(self):
        self.assertEqual(self.evaluate(raw={**self.raw, "harness_completed": False})["disposition"], "STOP_CONSTRUCTION")

    def test_missing_child_query_stops(self):
        raw = {**self.raw, "child_window_attributes": self.raw["child_window_attributes"][:1]}
        self.assertEqual(self.evaluate(raw=raw)["disposition"], "STOP_CONSTRUCTION")

    def test_b64_only_workbook_is_read_losslessly(self):
        workbook = b"synthetic-retained-xlsx-bytes"
        with tempfile.TemporaryDirectory() as temp:
            raw_path = pathlib.Path(temp)/"raw.json"
            (pathlib.Path(temp)/"document-window-probe.xlsx.b64").write_bytes(base64.b64encode(workbook))
            data, mode = read_xlsx(raw_path, {"source_file": "document-window-probe.xlsx"})
        self.assertEqual(mode, "base64")
        self.assertEqual(data, workbook)

    def test_malformed_tree_output_stops_without_exception(self):
        raw = {**self.raw, "root_tree": {"exit": 0, "stdout": None}}
        self.assertEqual(self.evaluate(raw=raw)["disposition"], "STOP_CONSTRUCTION")

    def test_unknown_map_state_stops(self):
        raw = {**self.raw, "child_window_attributes": list(self.raw["child_window_attributes"])}
        raw["child_window_attributes"][0] = {**raw["child_window_attributes"][0], "stdout": raw["child_window_attributes"][0]["stdout"].replace("IsViewable", "IsUnknown")}
        self.assertEqual(self.evaluate(raw=raw)["disposition"], "STOP_CONSTRUCTION")

    def test_wrong_saved_value_stops(self):
        self.assertEqual(self.evaluate(disk=1)["disposition"], "STOP_CONSTRUCTION")

    def test_raw_hash_mismatch_stops(self):
        self.assertEqual(self.evaluate(raw_hash="wrong")["disposition"], "STOP_CONSTRUCTION")

    def test_frozen_audit_must_bind_same_raw(self):
        self.assertEqual(self.evaluate(frozen={**self.frozen, "raw_sha256": "other"})["disposition"], "STOP_CONSTRUCTION")


if __name__ == "__main__":
    unittest.main()
