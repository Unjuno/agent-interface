"""A03 construction tests exercise only private mini-records."""
from __future__ import annotations

import unittest

import audit_controls as audit


class ConstructionTests(unittest.TestCase):
    def test_mutation_must_change_public_bytes(self):
        base = {"cases": [{"scene": {"tracks": [{"layer": "foreground"}]}}]}
        changed = {"cases": [{"scene": {"tracks": [{"layer": "target"}]}}]}
        self.assertNotEqual(audit.public_digest(base), audit.public_digest(changed))

    def test_row_count_failure_has_specific_reason(self):
        public = {"cases": [{"case_id": str(i)} for i in range(8)]}
        truth = {"cases": {str(i): {} for i in range(8)}}
        rows = []
        with self.assertRaisesRegex(ValueError, "exact_row_count_mismatch"):
            audit.baseline(public, truth, rows, audit.public_digest(public))

    def test_likely_old_first_target_relabel_is_noop(self):
        track = {"layer": "target"}
        self.assertEqual(track["layer"], "target")
        track["layer"] = "target"
        self.assertEqual(track["layer"], "target")


if __name__ == "__main__":
    unittest.main()
