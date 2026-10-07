import json
import unittest
from pathlib import Path
from boundary_audit import audit
from mutations import cases


class BoundaryTests(unittest.TestCase):
    def test_retained_control_and_corruption_matrix(self):
        raw = json.loads((Path(__file__).parent / "retained" / "raw.json").read_text())
        for name, item, invalid in cases(raw):
            with self.subTest(case=name):
                self.assertEqual(bool(audit(item)), invalid)


if __name__ == "__main__":
    unittest.main()
