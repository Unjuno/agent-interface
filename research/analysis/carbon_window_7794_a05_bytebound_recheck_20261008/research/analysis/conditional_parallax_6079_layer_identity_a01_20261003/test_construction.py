"""Construction checks use synthetic mini-cases, not the formal 8-case fixture."""
from __future__ import annotations

import unittest

import audit
import candidate


def mini_case(*, target_left: int = 8, target_right: int = 0,
              background_left: int = 2, background_right: int = 0) -> dict:
    def layer(name: str, ids: tuple[str, str], displacement: int) -> list[dict]:
        return [
            {"track_id": track_id, "layer": name, "membership": "verified",
             "source_id": "mini-source", "frame_ids": ["m0", "m1"],
             "xy": [[x, 0], [x + displacement, 0]]}
            for track_id, x in zip(ids, ((0, 10) if name == "target" else (20, 30)), strict=True)
        ]
    return {
        "case_id": "construction-mini",
        "source_id": "mini-source", "frame_ids": ["m0", "m1"],
        "probe": {"status": "verified", "source_id": "mini-source",
                  "frame_ids": ["m0", "m1"], "intent_epoch": "e1"},
        "scenes": [
            {"scene_id": "left", "tracks": layer("target", ("t1", "t2"), target_left)
             + layer("background", ("b1", "b2"), background_left)},
            {"scene_id": "right", "tracks": layer("target", ("t1", "t2"), target_right)
             + layer("background", ("b1", "b2"), background_right)},
        ],
    }


class ConstructionTests(unittest.TestCase):
    def test_two_layer_positive_uses_relative_motion(self):
        row = candidate.estimate(mini_case())
        self.assertEqual(row["status"], "DISTINGUISHED")
        self.assertEqual(row["layer_relative_sq"], {"n": 36, "d": 1})

    def test_same_layer_motion_has_no_relative_discriminator(self):
        row = candidate.estimate(mini_case(target_left=8, target_right=4,
                                           background_left=2, background_right=0))
        self.assertEqual(row["status"], "UNKNOWN")

    def test_unverified_probe_fails_closed(self):
        case = mini_case()
        case["probe"]["status"] = "unknown"
        self.assertEqual(candidate.estimate(case)["status"], "UNKNOWN")

    def test_duplicate_track_identity_fails_closed(self):
        case = mini_case()
        case["scenes"][0]["tracks"][1]["track_id"] = case["scenes"][0]["tracks"][0]["track_id"]
        self.assertEqual(audit.derive(case)["status"], "UNKNOWN")

    def test_auditor_and_candidate_agree_on_mini_case(self):
        case = mini_case()
        self.assertEqual(candidate.estimate(case), audit.derive(case))
        self.assertEqual(audit.derive(case)["status"], "DISTINGUISHED")


if __name__ == "__main__":
    unittest.main()
