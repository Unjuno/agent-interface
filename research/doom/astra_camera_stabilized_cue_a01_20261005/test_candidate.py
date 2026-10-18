"""Construction checks for translation estimation; no video input is used."""
import unittest

import numpy as np

import candidate


def shift_image(image, dx, dy):
    h, w = image.shape
    out = np.zeros_like(image)
    py, px, cy, cx = candidate.overlap_slices(h, w, dy, dx)
    out[cy, cx] = image[py, px]
    return out


class RegistrationTests(unittest.TestCase):
    def test_recovers_known_translation(self):
        rng = np.random.default_rng(5905)
        prior = rng.integers(0, 256, size=(96, 128), dtype=np.uint8)
        current = shift_image(prior, 4, -3)
        dx, dy, score = candidate.estimate_shift(prior, current)
        self.assertEqual((dx, dy), (4, -3))
        self.assertEqual(score, 0.0)

    def test_identical_images_choose_zero_translation(self):
        rng = np.random.default_rng(59)
        image = rng.integers(0, 256, size=(96, 128), dtype=np.uint8)
        self.assertEqual(candidate.estimate_shift(image, image)[:2], (0, 0))

    def test_translation_preserves_prior_mask_inside_overlap(self):
        mask = np.zeros((12, 16), dtype=bool)
        mask[4, 5] = True
        moved = candidate.translated_previous(mask, 3, -2)
        self.assertEqual(np.argwhere(moved).tolist(), [[2, 8]])


if __name__ == "__main__":
    unittest.main()
