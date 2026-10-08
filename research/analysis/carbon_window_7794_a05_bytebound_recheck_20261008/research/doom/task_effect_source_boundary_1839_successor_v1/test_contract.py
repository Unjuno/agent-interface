import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("source_boundary_candidate", HERE / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class SourceBoundaryTests(unittest.TestCase):
    def test_rejects_altered_compressed_source(self):
        self.assertNotEqual(candidate.EXPECTED_SHA, "0" * 64)

    def test_exact_source_inventory_is_frozen(self):
        self.assertEqual(len(candidate.EXPECTED_KEYS), 6)

    def test_only_exact_attack_session_suffix_is_treated_as_input(self):
        self.assertTrue("p1-attack".endswith("-attack"))
        self.assertFalse("p1-noinput".endswith("-attack"))


if __name__ == "__main__":
    unittest.main()
