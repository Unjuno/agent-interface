from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from auditor import audit_payload
from candidate import enumerate_geometry


class GeometryFeasibilityTests(unittest.TestCase):
    def test_freeze_sidecar_sources_and_known_result_are_bound(self):
        root = Path(__file__).parent
        freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
        sidecar = (root / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
        self.assertEqual(hashlib.sha256((root / "FREEZE.json").read_bytes()).hexdigest(), sidecar)
        for relative, expected in freeze["source_sha256"].items():
            self.assertEqual(hashlib.sha256((root / relative).resolve().read_bytes()).hexdigest(), expected, relative)
        baseline = (root / "preformal" / "host_candidate.json").read_bytes()
        self.assertEqual(hashlib.sha256(baseline).hexdigest(), freeze["preformal_candidate_sha256"])

    def test_exact_quadrant_support_is_insufficient(self):
        result = enumerate_geometry()
        self.assertEqual(result["block_counts"], {
            "northwest": 6, "northeast": 6, "southwest": 3, "southeast": 3})
        self.assertEqual(result["decision"], "HOLD_GEOMETRY_NOT_IDENTIFIABLE")

    def test_independent_auditor_reconstructs_raw_enumeration(self):
        result = enumerate_geometry()
        audit = audit_payload(result)
        self.assertEqual(audit["decision"], "PASS_GEOMETRY_AUDIT")
        self.assertEqual(audit["geometry_decision"], "HOLD_GEOMETRY_NOT_IDENTIFIABLE")
        self.assertEqual(audit["independently_reconstructed_sites"], len(result["enumerated_sites"]))

    def test_auditor_detects_corrupted_site_eligibility(self):
        result = enumerate_geometry()
        result["enumerated_sites"][0]["all_training_target_patches_disjoint"] = True
        audit = audit_payload(result)
        self.assertEqual(audit["decision"], "HOLD_AUDIT_INTEGRITY")
        self.assertIn("raw_site_reconstruction_mismatch", audit["errors"])

    def test_auditor_detects_geometry_metadata_mutation(self):
        result = enumerate_geometry()
        result["support_centers"][0] = [19, 15]
        audit = audit_payload(result)
        self.assertEqual(audit["decision"], "HOLD_AUDIT_INTEGRITY")
        self.assertIn("frozen_geometry_metadata_mismatch:support_centers", audit["errors"])


if __name__ == "__main__":
    unittest.main()
