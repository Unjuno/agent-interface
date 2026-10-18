"""Fail-first tests for auditor-side raw-image reconstruction."""

import base64
import hashlib
import unittest

try:
    import audit
    import candidate
except ModuleNotFoundError:
    audit = None
    candidate = None
from test_candidate import approach


def pgm(points):
    pixels = bytearray(128 * 128)
    for x, y, value in points:
        pixels[y * 128 + x] = value
    raw = b"P5\n128 128\n255\n" + pixels
    return {"pgm_b64": base64.b64encode(raw).decode("ascii"),
            "sha256": hashlib.sha256(raw).hexdigest()}


class IndependentFrameReconstructionTests(unittest.TestCase):
    def test_auditor_recovers_exact_area_centroid_and_hash_for_disk(self):
        self.assertIsNotNone(audit, "raw-only audit implementation must exist")
        disk = [(x, y, 220) for y in range(19, 24) for x in range(29, 34)
                if (x - 31) ** 2 + (y - 21) ** 2 <= 4]
        disk += [(20, 20, 100), (108, 20, 100), (20, 108, 100), (108, 108, 100)]
        observed = pgm(disk)
        measured = audit.inspect_frame(observed)
        self.assertEqual(measured["sha256"], observed["sha256"])
        self.assertEqual(measured["area"], 13)
        self.assertAlmostEqual(measured["cx"], 31.0)
        self.assertAlmostEqual(measured["cy"], 21.0)

    def test_auditor_rejects_hash_consistent_but_wrong_raw_feature(self):
        self.assertIsNotNone(audit, "raw-only audit implementation must exist")
        disk = [(x, y, 220) for y in range(19, 24) for x in range(29, 34)
                if (x - 31) ** 2 + (y - 21) ** 2 <= 4]
        disk += [(20, 20, 100), (108, 20, 100), (20, 108, 100), (108, 108, 100)]
        observed = pgm(disk)
        measured = audit.inspect_frame(observed)
        altered = dict(measured, area=99)
        self.assertFalse(audit.frame_measurement_matches(measured, altered))

    def test_auditor_refuses_corrupted_frame_digest(self):
        self.assertIsNotNone(audit, "raw-only audit implementation must exist")
        observed = pgm([(31, 21, 220)])
        observed["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "frame_hash_mismatch"):
            audit.inspect_frame(observed)

    def test_independent_raw_reconstruction_matches_candidate_on_held_unit_fixture(self):
        self.assertIsNotNone(audit, "raw-only audit implementation must exist")
        self.assertIsNotNone(candidate, "image-only candidate must exist")
        sequence = approach("synthetic-unit-approach")
        expected = audit._expected(sequence)
        produced = candidate.analyze(sequence)
        for field in ("status", "reason", "gate", "metrics", "yield_latency_s",
                      "pixel_grid", "growth_grid", "ttc_grid", "frames"):
            self.assertEqual(expected[field], produced[field], field)


if __name__ == "__main__":
    unittest.main()
