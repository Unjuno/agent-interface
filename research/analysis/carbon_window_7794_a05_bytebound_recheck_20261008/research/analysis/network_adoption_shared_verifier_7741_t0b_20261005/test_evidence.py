import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent


class RetainedStopTests(unittest.TestCase):
    def test_candidate_stdout_is_empty_and_science_is_unadjudicated(self):
        self.assertEqual((ROOT / "candidate-raw.json").stat().st_size, 0)
        stop = (ROOT / "STOP.md").read_text()
        self.assertIn("STOP_CANDIDATE_RUNTIME", stop)
        self.assertIn("no scientific result", stop)
        self.assertIn("source hash", stop)


if __name__ == "__main__":
    unittest.main()
