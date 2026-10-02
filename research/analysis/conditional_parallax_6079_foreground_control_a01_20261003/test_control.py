"""Construction checks; formal candidate is invoked only after freeze."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "conditional_parallax_6079_t0_v1_20261003"))
sys.path.insert(0, str(ROOT))
import auditor
import candidate
import probe


class ForegroundControlConstructionTest(unittest.TestCase):
    def test_control_preserves_target_and_passive_pairs_but_adds_landmark_pixels(self):
        source = probe.run()
        parent = __import__("json").loads((probe.PARENT / "candidate_input.json").read_text())
        original = parent["pairs"][3]
        tested = source["pairs"][0]
        self.assertEqual([f["pgm_b64"] for f in tested["members"][0]["frames"][:5]], [f["pgm_b64"] for f in tested["members"][1]["frames"][:5]])
        self.assertEqual(tested["probe_receipt"]["actual_dx"], 0.85)
        for idx in range(5, 8):
            self.assertEqual(auditor.pixels(tested["members"][1]["frames"][idx])[2].count(240), auditor.pixels(original["members"][1]["frames"][idx])[2].count(240))
        self.assertEqual(candidate.run(source)["results"][0]["classification"], "DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS")


if __name__ == "__main__":
    unittest.main()
