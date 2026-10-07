from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import auditor


class AuditConstructionTests(unittest.TestCase):
    def test_gate_accepts_only_exact_clean_reconstruction(self):
        self.assertEqual(auditor.gate_status(400, [], []), "PASS")
        self.assertEqual(auditor.gate_status(399, [], []), "FAIL")
        self.assertEqual(auditor.gate_status(400, ["row mismatch"], []), "FAIL")

    def test_a01_inverted_mutation_count_cannot_pass(self):
        self.assertEqual(auditor.gate_status(400, [], [f"control-{n}" for n in range(6)]), "FAIL")
        self.assertEqual(auditor.gate_status(400, [], []), "PASS")

    def test_expected_cells_are_fully_crossed_and_safety_is_vetoed(self):
        cells = [auditor._expected(seed, mode, rule)
                 for seed in (0, 17, 99) for mode in auditor.MODES for rule in auditor.RULES]
        self.assertEqual(len(cells), 12)
        self.assertTrue(all(row["query_count"] == 5 for row in cells))
        self.assertTrue(all(row["safety_veto_count"] == 1 for row in cells))
        self.assertTrue(all(row["candidate_locked_before_fresh"] for row in cells))

    def test_independent_reconstruction_and_six_mutation_controls(self):
        rows = [auditor._expected(seed, mode, rule)
                for seed in range(100) for mode in auditor.MODES for rule in auditor.RULES]
        self.assertEqual(auditor.reconstruct(rows), [])
        self.assertEqual(auditor.undetected_mutations(rows), [])


if __name__ == "__main__":
    unittest.main()
