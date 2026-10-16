"""Literal controls: exact visual identity, not schedule-imputed membership."""
import unittest

from policy import decode, capture_slots


class PolicyTests(unittest.TestCase):
    def test_exact_red_cue_is_decoded_from_pixels(self):
        pixels = [0x000001] + [0xFF0000] * 1023
        self.assertEqual(decode(pixels), {"id": 1, "color": 0xFF0000})

    def test_exact_green_cue_is_decoded_from_pixels(self):
        self.assertEqual(decode([8] + [0x00FF00] * 1023), {"id": 8, "color": 0x00FF00})

    def test_dark_frame_does_not_impute_a_cue(self):
        self.assertIsNone(decode([0] * 1024))

    def test_bad_shape_and_unknown_pattern_are_unknown(self):
        for pixels in ([], [1] * 10, [9] + [0xFF0000] * 1023,
                       [True] + [0xFF0000] * 1023,
                       [1] + [0xFF0000] * 1022 + [0],
                       [1] + [0x112233] * 1023):
            with self.subTest(size=len(pixels)):
                self.assertIsNone(decode(pixels))

    def test_equal_budget_rotation_is_not_frequency_increase(self):
        self.assertEqual(capture_slots([0, 0, 0, 0]), [5, 125, 245, 365, 485, 605, 725, 845])
        self.assertEqual(capture_slots([1, 7, 3, 9]), [15, 195, 275, 455, 495, 675, 755, 935])
        self.assertEqual(capture_slots([0, 3, 6, 9]), [5, 155, 305, 455, 485, 635, 785, 935])

    def test_malformed_offset_cycle_is_refused(self):
        for offsets in ([0], [0, 0, 0, True], [0, 0, 0, 12], [0, 0, 0, -1]):
            with self.subTest(offsets=offsets):
                with self.assertRaises(ValueError):
                    capture_slots(offsets)


if __name__ == "__main__":
    unittest.main()
