"""Inline construction checks only; formal_input.json is never opened here."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import candidate
import auditor


class IntakeLedgerTests(unittest.TestCase):
    def setUp(self):
        self.raw = b'{"fixture_id":"inline","rows":[]}'
        self.stream = {"fixture_id": "inline", "rows": [
            {"id":"idea-x","kind":"intake","screen":"NOT_TESTED_DUPLICATE","test_started":False,"claim_id":None,"statistical_eligible":False,"p_value":None},
            {"id":"claim-x","kind":"test","screen":None,"test_started":True,"claim_id":"X","statistical_eligible":True,"p_value":0.2,"outcome":"TEST_STARTED_FAIL","abandoned_after_interim":True},
            {"id":"method-x","kind":"deterministic","screen":None,"test_started":True,"claim_id":"M","statistical_eligible":False,"p_value":None,"outcome":"HARD_SAFETY_FAIL","hard_safety":True},
        ]}

    def test_untested_remains_outside_family(self):
        out = candidate.project(self.stream, self.raw)
        self.assertEqual(out["counts"]["screened_out_not_tested"], 1)
        self.assertEqual(out["counts"]["statistical_family_size"], 1)
        self.assertNotIn("idea-x", [r["id"] for r in out["statistical_family"]])

    def test_abandoned_negative_remains_started(self):
        out = candidate.project(self.stream, self.raw)
        self.assertEqual(out["counts"]["started_test_opportunities"], 1)
        self.assertEqual(out["counts"]["started_negative_abandoned"], 1)

    def test_deterministic_safety_has_no_p_value(self):
        out = candidate.project(self.stream, self.raw)
        self.assertNotIn("p_value", out["deterministic"][0])

    def test_independent_replay_matches_candidate(self):
        self.assertEqual(candidate.project(self.stream, self.raw), auditor.reconstruct(self.stream, self.raw))

    def test_five_mutations_are_detectable(self):
        expected = auditor.reconstruct(self.stream, self.raw)
        controls = auditor.corruption_controls(expected)
        self.assertEqual(len(controls), 5)
        self.assertTrue(all(controls.values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
