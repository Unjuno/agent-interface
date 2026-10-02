"""Construction-only checks; run before freezing and before the formal invocation."""
from __future__ import annotations

import json
import unittest

import auditor
import candidate
import fixture


class ConditionalParallaxConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.visible, cls.truth = fixture.build()
        cls.output = candidate.run(cls.visible)

    def test_nine_pairs_and_truth_is_sidecar_only(self) -> None:
        self.assertEqual(len(self.visible["pairs"]), 9)
        self.assertEqual(len(self.truth["pairs"]), 9)
        self.assertNotIn("contact_time_ms", json.dumps(self.visible))
        self.assertEqual([len(p["members"][0]["frames"]) for p in self.visible["pairs"]], [8] * 9)

    def test_all_pairs_match_during_passive_interval(self) -> None:
        for pair in self.visible["pairs"]:
            left, right = pair["members"]
            self.assertEqual([x["pgm_b64"] for x in left["frames"][:5]], [x["pgm_b64"] for x in right["frames"][:5]])

    def test_active_overlay_pairs_are_observation_distinguishable(self) -> None:
        rows = self.output["results"][:3]
        self.assertEqual([r["classification"] for r in rows], ["DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS"] * 3)
        self.assertTrue(all(r["max_relative_separation_px"] >= 2.0 for r in rows))

    def test_sham_and_world_matched_pairs_yield_unknown(self) -> None:
        rows = self.output["results"]
        self.assertEqual([r["classification"] for r in rows[3:]], ["UNKNOWN"] * 6)
        for pair in self.visible["pairs"][3:]:
            a, b = pair["members"]
            self.assertEqual([x["pgm_b64"] for x in a["frames"]], [x["pgm_b64"] for x in b["frames"]])

    def test_no_authority_or_contact_claim(self) -> None:
        self.assertTrue(all(r["authority"] is False and r["contact_claim"] is False for r in self.output["results"]))

    def test_independent_audit_and_all_four_corruptions(self) -> None:
        result = auditor.run(self.visible, self.truth, self.output)
        self.assertEqual(result["base_errors"], [])
        self.assertEqual(result["mutation_controls_rejected"], {
            "altered_probe_receipt": True,
            "swapped_truth_label": True,
            "sham_mislabeled_as_movement": True,
            "one_frame_mismatch": True,
        })


if __name__ == "__main__":
    unittest.main()
