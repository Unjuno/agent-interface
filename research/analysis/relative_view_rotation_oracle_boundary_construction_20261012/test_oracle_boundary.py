"""Construction-only regressions for the #8636 ViewState oracle boundary.

Run with A04_SOURCE_DIR set to an extracted copy of frozen source commit
2f15e4f9a68cea4b9e47940b8f9b468ba5dd07cf. This module never runs the formal
candidate loop or auditor main entry point.
"""
from __future__ import annotations

import os
import sys
import unittest

SOURCE_DIR = os.environ.get("A04_SOURCE_DIR")
if SOURCE_DIR:
    sys.path.insert(0, SOURCE_DIR)
    import auditor
    import runner
else:
    auditor = None
    runner = None


def pixels(ppm: bytes) -> bytes:
    return ppm.split(bytes([10]) + b"255" + bytes([10]), 1)[1]


@unittest.skipUnless(SOURCE_DIR, "run through verify_construction.py against the frozen source")
class OracleBoundaryConstructionTests(unittest.TestCase):
    def test_oracle_action_does_not_depend_on_near_singular_image(self):
        seed = 30090
        yaw, pitch, focal, fault = runner.scenario(seed, "feature_loss")
        self.assertEqual(fault, "near_singular")
        image, _ = runner.render(yaw, pitch, focal, fault)
        meta = {
            "width": 96,
            "height": 96,
            "target_generation": seed,
            "viewport_generation": seed,
        }

        points, features, action = runner.control_step(
            "viewstate_oracle", yaw, pitch, 0, image, None, meta
        )

        self.assertIsNone(points)
        self.assertIsNone(features)
        self.assertEqual(action, auditor.expected_oracle_action(yaw, pitch, 0))
        self.assertTrue(all(abs(value) <= 0.08 for value in action))

    def test_image_controller_still_yields_on_near_singular_image(self):
        seed = 30090
        yaw, pitch, focal, fault = runner.scenario(seed, "feature_loss")
        image, _ = runner.render(yaw, pitch, focal, fault)
        meta = {
            "width": 96,
            "height": 96,
            "target_generation": seed,
            "viewport_generation": seed,
        }

        with self.assertRaisesRegex(ValueError, "landmark missing or ambiguous"):
            runner.control_step("raw_pixels", yaw, pitch, 0, image, None, meta)

    def test_auditor_skips_image_detection_for_oracle_action(self):
        seed = 30090
        yaw, pitch, focal, fault = runner.scenario(seed, "feature_loss")
        image, _ = runner.render(yaw, pitch, focal, fault)
        raw_pixels = pixels(image)

        with self.assertRaisesRegex(ValueError, "missing or ambiguous landmark"):
            auditor.centers(96, 96, raw_pixels)

        self.assertIsNone(
            auditor.audit_image_points("viewstate_oracle", 96, 96, raw_pixels, "ACTION")
        )

    def test_auditor_still_requires_image_arm_yield_on_invalid_pixels(self):
        seed = 30090
        yaw, pitch, focal, fault = runner.scenario(seed, "feature_loss")
        image, _ = runner.render(yaw, pitch, focal, fault)
        raw_pixels = pixels(image)

        self.assertIsNone(
            auditor.audit_image_points("raw_pixels", 96, 96, raw_pixels, "YIELD")
        )
        with self.assertRaisesRegex(ValueError, "missing or ambiguous landmark"):
            auditor.audit_image_points("raw_pixels", 96, 96, raw_pixels, "ACTION")


if __name__ == "__main__":
    unittest.main()
