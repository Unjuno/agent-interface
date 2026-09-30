import unittest

from .design import ALL_ROWS, EXHAUSTIVE, OFAT, PAIRWISE, THREE_WAY, coverage


class DesignTests(unittest.TestCase):
    def test_factorial_fixture_has_sixteen_assignments(self):
        self.assertEqual(len(ALL_ROWS), 16)
        self.assertEqual(len(set(ALL_ROWS)), 16)

    def test_ofat_is_baseline_and_single_flips(self):
        self.assertEqual(len(OFAT), 5)
        self.assertTrue(all(sum(row) <= 1 for row in OFAT))

    def test_pairwise_covers_all_binary_pairs_with_reduction(self):
        pairs = set().union(*(coverage(row, 2) for row in PAIRWISE))
        self.assertEqual(len(pairs), 24)
        self.assertLess(len(PAIRWISE), len(EXHAUSTIVE))

    def test_three_way_covers_all_binary_triples_with_reduction(self):
        triples = set().union(*(coverage(row, 3) for row in THREE_WAY))
        self.assertEqual(len(triples), 32)
        self.assertLess(len(THREE_WAY), len(EXHAUSTIVE))

    def test_pair_oracle_is_missed_by_ofat_and_found_by_pairwise(self):
        hazard = lambda row: row[0] == 1 and row[1] == 1
        self.assertFalse(any(map(hazard, OFAT)))
        self.assertTrue(any(map(hazard, PAIRWISE)))

    def test_triple_oracle_is_found_by_three_way(self):
        hazard = lambda row: row[0] == 1 and row[2] == 1 and row[3] == 1
        self.assertTrue(any(map(hazard, THREE_WAY)))

    def test_designs_are_deterministic_and_unique(self):
        self.assertEqual(PAIRWISE, tuple(PAIRWISE))
        self.assertEqual(len(set(PAIRWISE)), len(PAIRWISE))
        self.assertEqual(len(set(THREE_WAY)), len(THREE_WAY))


if __name__ == "__main__":
    unittest.main()
