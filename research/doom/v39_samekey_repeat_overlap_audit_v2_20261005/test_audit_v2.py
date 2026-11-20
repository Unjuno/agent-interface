"""Corruption controls for the versioned raw-only overlap auditor."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from .audit_v2 import assess_overlap

RAW = json.loads((Path(__file__).resolve().parent / "INPUT_RAW.json").read_text(encoding="utf-8"))


class OverlapAuditTests(unittest.TestCase):
    def test_retained_overlap_passes_as_non_bijective_hold(self):
        result = assess_overlap(copy.deepcopy(RAW))
        self.assertEqual(result, {
            "errors": [], "disposition": "HOLD_NON_BIJECTIVE",
            "admissions": 2, "release_rows": 1,
        })

    def test_both_admissions_after_release_are_rejected(self):
        raw = copy.deepcopy(RAW)
        case = raw["cases"][1]
        receipt = next(e for e in case["events"] if e.get("event") == "input_release_transition")["owner_thread_keyup_receipt"]
        later = receipt["owner_keyrelease_started_ns"] + 1
        for admission in (e for e in case["events"] if e.get("event") == "input_admission"):
            admission["input_ack_ns"] = later
            later += 1
        result = assess_overlap(raw)
        self.assertIn("overlap_admission_0_ack_before_release", result["errors"])
        self.assertIn("overlap_admission_1_ack_before_release", result["errors"])
        self.assertEqual(result["disposition"], "FAIL_AUDIT")

    def test_foreign_admission_context_is_rejected(self):
        raw = copy.deepcopy(RAW)
        admission = [e for e in raw["cases"][1]["events"] if e.get("event") == "input_admission"][1]
        admission.update(id="foreign", step=999, intent_token="foreign-token",
                         owner_id="foreign-owner")
        result = assess_overlap(raw)
        self.assertIn("overlap_admission_1_id", result["errors"])
        self.assertIn("overlap_admission_1_step", result["errors"])
        self.assertIn("overlap_admission_1_intent_token", result["errors"])
        self.assertIn("overlap_admission_owner_context", result["errors"])
        self.assertEqual(result["disposition"], "FAIL_AUDIT")

    def test_foreign_release_receipt_context_is_rejected(self):
        raw = copy.deepcopy(RAW)
        release = next(e for e in raw["cases"][1]["events"] if e.get("event") == "input_release_transition")
        release["owner_thread_keyup_receipt"]["owner_id"] = "foreign-owner"
        result = assess_overlap(raw)
        self.assertIn("overlap_release_receipt_owner_id", result["errors"])
        self.assertEqual(result["disposition"], "FAIL_AUDIT")

    def test_malformed_event_row_fails_closed(self):
        raw = copy.deepcopy(RAW)
        raw["cases"][1]["events"].append(None)
        result = assess_overlap(raw)
        self.assertEqual(result["errors"], ["overlap_event_rows"])
        self.assertEqual(result["disposition"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
