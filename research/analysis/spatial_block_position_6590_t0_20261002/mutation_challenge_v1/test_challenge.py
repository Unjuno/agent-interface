from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import candidate
import auditor
from challenge import challenge


ROOT = Path(__file__).resolve().parent.parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class OverlapMutationChallenge(unittest.TestCase):
    def test_single_block_reassignment_is_visible_and_fails_closed(self):
        raw = candidate.generate(FIXTURE)
        clean = auditor.audit(FIXTURE, raw)
        result = challenge(FIXTURE, raw, clean)
        self.assertEqual(result["decision"], "MUTATION_PASS")
        self.assertEqual(result["clean_decision"], "METHOD_PASS")
        self.assertGreaterEqual(result["maximum_reported_position_overlap"], 1)
        self.assertEqual(result["mutated_decision"], "HOLD_AUDIT_INTEGRITY")
        self.assertEqual(result["row_reconstruction_error_count"], 1)


if __name__ == "__main__":
    unittest.main()
