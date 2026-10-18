import base64
import hashlib
import importlib.util
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if importlib.util.find_spec("candidate") is None:
    analyze = None
else:
    from candidate import analyze


def frame(radius, t_s, track_id="track-a", center=(64, 64), marker_scale=1.0):
    pixels = bytearray(128 * 128)
    cx, cy = center
    for y in range(128):
        for x in range(128):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                pixels[y * 128 + x] = 220
    for mx, my in ((28, 28), (100, 28), (28, 100), (100, 100)):
        px = round(64 + (mx - 64) * marker_scale)
        py = round(64 + (my - 64) * marker_scale)
        pixels[py * 128 + px] = 100
    pgm = b"P5\n128 128\n255\n" + bytes(pixels)
    return {"t_s": t_s, "track_id": track_id,
            "pgm_b64": base64.b64encode(pgm).decode("ascii"),
            "sha256": hashlib.sha256(pgm).hexdigest()}


def approach(sequence_id="approach", radii=(7, 8, 9, 10, 11),
              centers=((64, 64),) * 5, tracks=("track-a",) * 5,
              marker_scales=(1.0,) * 5, times=(0.0, .1, .2, .3, .4)):
    return {"sequence_id": sequence_id, "frames": [
        frame(r, t, track, center, scale)
        for r, t, track, center, scale in zip(
            radii, times, tracks, centers, marker_scales)]}


class ImageOnlyCandidateTests(unittest.TestCase):
    def test_analytic_raster_disks_pass_shape_gate_without_grid_perimeter(self):
        self.assertTrue(callable(analyze), "image-only analyzer must exist")
        result = analyze(approach())
        self.assertEqual(result["status"], "TRACKABLE")
        self.assertGreaterEqual(result["gate"]["shape_fill_min"], 0.50)
        self.assertLessEqual(result["gate"]["axis_ratio_max"], 1.50)
        self.assertGreater(result["metrics"]["secant_ttc_s"], .20)

    def test_identical_frames_with_same_clock_and_track_have_same_decision(self):
        self.assertTrue(callable(analyze), "image-only analyzer must exist")
        first = analyze(approach("true-approach-label"))
        twin = analyze(approach("nonapproach-twin-label"))
        for key in ("status", "reason", "gate", "metrics", "pixel_grid",
                    "growth_grid", "ttc_grid", "yield_latency_s"):
            self.assertEqual(first[key], twin[key], key)

    def test_track_identity_change_abstains_for_all_comparators(self):
        self.assertTrue(callable(analyze), "image-only analyzer must exist")
        sequence = approach(tracks=("track-a", "track-a", "track-b",
                                    "track-b", "track-b"))
        result = analyze(sequence)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "track_identity_changed")
        self.assertFalse(any(result["pixel_grid"].values()))
        self.assertFalse(any(result["growth_grid"].values()))
        self.assertFalse(any(result["ttc_grid"].values()))

    def test_global_zoom_abstains_instead_of_counting_as_target_approach(self):
        self.assertTrue(callable(analyze), "image-only analyzer must exist")
        sequence = approach(marker_scales=(1.0, 1.02, 1.04, 1.07, 1.10))
        result = analyze(sequence)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "global_scale_changed")
        self.assertFalse(any(result["ttc_grid"].values()))

    def test_timestamp_regression_is_unknown_and_never_yields(self):
        self.assertTrue(callable(analyze), "image-only analyzer must exist")
        sequence = approach(times=(0.0, .1, .2, .15, .4))
        result = analyze(sequence)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "invalid_capture_clock")
        self.assertFalse(any(result["ttc_grid"].values()))

    def test_hash_mismatch_is_rejected_not_scored(self):
        self.assertTrue(callable(analyze), "image-only analyzer must exist")
        sequence = approach()
        sequence["frames"][0]["pgm_b64"] = sequence["frames"][1]["pgm_b64"]
        with self.assertRaises(ValueError):
            analyze(sequence)


if __name__ == "__main__":
    unittest.main()
