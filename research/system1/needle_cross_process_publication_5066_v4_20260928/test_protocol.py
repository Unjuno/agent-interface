import unittest
from pathlib import Path

from model import OLD_GENERATION, load_seed, package_for_sequence, parsed_package


class PackageConstructionTests(unittest.TestCase):
    def test_seed_identity_and_digest(self):
        raw, seed = load_seed(Path(__file__).parent)
        self.assertEqual(seed["generation"], OLD_GENERATION)
        self.assertEqual(len(raw), 15279)

    def test_successor_changes_only_frozen_metadata(self):
        _, seed = load_seed(Path(__file__).parent)
        candidate = package_for_sequence(seed, 1)
        valid, generation = parsed_package(candidate)
        self.assertTrue(valid)
        self.assertEqual(generation, OLD_GENERATION + 1)
        import json
        parsed = json.loads(candidate)
        self.assertEqual(parsed["tensors"], seed["tensors"])
        self.assertEqual(parsed["graph"], seed["graph"])
        self.assertEqual(parsed["provenance"]["publication_sequence"], 1)

    def test_sequences_are_distinct_and_monotonic(self):
        _, seed = load_seed(Path(__file__).parent)
        packages = [package_for_sequence(seed, i) for i in (1, 2, 4096)]
        self.assertEqual(len(set(packages)), 3)
        self.assertEqual([parsed_package(x)[1] for x in packages],
                         [OLD_GENERATION + i for i in (1, 2, 4096)])

    def test_bad_sequence_refuses(self):
        _, seed = load_seed(Path(__file__).parent)
        for invalid in (0, -1, True, 1.0):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                package_for_sequence(seed, invalid)


if __name__ == "__main__":
    unittest.main()
