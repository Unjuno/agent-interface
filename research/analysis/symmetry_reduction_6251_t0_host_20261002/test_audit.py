"""Independent checker tests; audit.py must not import candidate.py."""
from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import audit
import candidate


class IndependentAuditTests(unittest.TestCase):
    def test_independent_reconstruction_accepts_candidate_result(self):
        result = candidate.run()

        self.assertEqual(audit.audit_result(result), [])

    def test_independent_reconstruction_rejects_state_count_tampering(self):
        result = candidate.run()
        result["symmetric"]["full_state_count"] += 1

        self.assertTrue(any("full_state_count" in error for error in audit.audit_result(result)))

    def test_independent_reconstruction_rejects_corrupted_counterexample_trace(self):
        result = candidate.run()
        result["symmetric"]["counterexample_witnesses"][0]["trace"].clear()

        self.assertTrue(any("witness" in error for error in audit.audit_result(result)))


if __name__ == "__main__":
    unittest.main()
