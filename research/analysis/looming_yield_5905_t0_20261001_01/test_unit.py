import json
import unittest
from pathlib import Path

from candidate import measure_radius, pgm


HERE = Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    def test_rendered_radius_recovered(self):
        self.assertAlmostEqual(measure_radius(pgm(16.0)), 16.0, delta=0.1)

    def test_fixture_has_eligible_and_boundary_cases(self):
        fixture = json.loads((HERE / "fixture.json").read_text())
        self.assertEqual(sum(c["kind"] == "approach" for c in fixture["cases"]), 4)
        self.assertEqual(sum(c["kind"] == "control" for c in fixture["cases"]), 7)
        self.assertTrue(all("signals" in c for c in fixture["cases"] if c["kind"] == "control"))

    def test_image_payload_is_lossless_pgm(self):
        frame = pgm(9.0)
        header, pixels = frame.split(b"\n255\n", 1)
        self.assertEqual(header, b"P5\n256 256")
        self.assertEqual(len(pixels), 256 * 256)


if __name__ == "__main__":
    unittest.main()
