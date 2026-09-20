import tempfile
import unittest
from pathlib import Path

from proxy import render


class ProxySurfaceTests(unittest.TestCase):
    def test_image_is_deterministic_and_state_bound_by_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b, c = (Path(tmp) / n for n in ("a.ppm", "b.ppm", "c.ppm"))
            render(0, 1, a); render(0, 1, b); render(1, 2, c)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertNotEqual(a.read_bytes(), c.read_bytes())
            self.assertTrue(a.read_bytes().startswith(b"P6\n320 120\n255\n"))


if __name__ == "__main__":
    unittest.main()
