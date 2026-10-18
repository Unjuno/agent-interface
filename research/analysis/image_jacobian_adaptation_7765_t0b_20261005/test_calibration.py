import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent


class CalibrationProtocolTests(unittest.TestCase):
    def test_training_and_heldout_seed_ranges_are_disjoint(self):
        p = json.loads((ROOT / "CALIBRATION_PROTOCOL.json").read_text())
        a, b = p["training_seeds"], p["heldout_test_seeds"]
        self.assertTrue(set(range(a[0], a[1] + 1)).isdisjoint(range(b[0], b[1] + 1)))
        self.assertTrue(p["no_reuse"] and p["no_retry"])


if __name__ == "__main__": unittest.main()
