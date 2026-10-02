"""Construction-only tests for mutation routing; parent candidate is never imported."""
from __future__ import annotations

import base64
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import auditor


class IntegrityAdjudicationConstructionTests(unittest.TestCase):
    def test_truth_label_mutation_is_checked_in_truth_slot(self):
        visible = {"pairs": [{"pair_id": "p", "probe_receipt": {"actual_dx": 0.0}}]}
        truth = {"pairs": [{"pair_id": "p", "family": "sham", "member_truth": ["approach_contact", "screen_overlay_no_contact"]}]}
        self.assertFalse(auditor.reject_truth_label_corruption(visible, truth))
        truth["pairs"][0]["member_truth"].reverse()
        self.assertTrue(auditor.reject_truth_label_corruption(visible, truth))

    def test_sham_motion_label_mutation_is_bound_to_visible_receipt(self):
        visible = {"pairs": [{"pair_id": "p", "probe_receipt": {"actual_dx": 0.0}}]}
        truth = {"pairs": [{"pair_id": "p", "expected_actual_dx": 0.0}]}
        self.assertFalse(auditor.reject_visible_truth_mismatch(visible, truth))
        truth["pairs"][0]["expected_actual_dx"] = 0.85
        self.assertTrue(auditor.reject_visible_truth_mismatch(visible, truth))

    def test_pixel_mutation_is_bound_to_original_truth_hash(self):
        raw = b"P5\n1 1\n255\n" + bytes([240])
        truth = {"pairs": [{"pair_id": "p", "frame_sha256": [[hashlib.sha256(raw).hexdigest()]]}]}
        visible = {"pairs": [{"pair_id": "p", "members": [{"frames": [{"pgm_b64": base64.b64encode(raw).decode()}]}]}]}
        self.assertTrue(auditor._truth_frame_hashes_hold(visible, truth))
        auditor._flip_pixel(visible["pairs"][0]["members"][0]["frames"][0])
        self.assertFalse(auditor._truth_frame_hashes_hold(visible, truth))

    def test_adjudicator_never_imports_parent_candidate_or_auditor(self):
        source = (ROOT / "auditor.py").read_text()
        self.assertNotRegex(source, r"^\s*(?:import|from)\s+(?:candidate|auditor)\b")
        self.assertNotIn("candidate.run(", source)


if __name__ == "__main__":
    unittest.main()
