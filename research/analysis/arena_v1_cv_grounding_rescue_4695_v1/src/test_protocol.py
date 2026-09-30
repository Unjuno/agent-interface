#!/usr/bin/env python3
import unittest

from refine import MAX_ASPECT, MAX_AREA, MIN_AREA, MIN_ASPECT, MIN_FILL, ORANGE, TOLERANCE, matching


class RefinementProtocolTests(unittest.TestCase):
    def test_orange_threshold_accepts_exact(self):
        self.assertTrue(matching(ORANGE))

    def test_orange_threshold_rejects_outside_channel_tolerance(self):
        self.assertFalse(matching((ORANGE[0] + TOLERANCE + 1, ORANGE[1], ORANGE[2])))

    def test_frozen_shape_gates_are_nonempty_and_bounded(self):
        self.assertLess(MIN_AREA, MAX_AREA)
        self.assertLess(MIN_ASPECT, 1.0)
        self.assertGreater(MAX_ASPECT, 1.0)
        self.assertGreater(MIN_FILL, 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
