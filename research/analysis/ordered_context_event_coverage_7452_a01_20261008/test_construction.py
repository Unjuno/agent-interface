import itertools
import unittest

import candidate


class ConstructionTests(unittest.TestCase):
    def test_counts_and_reset_partition(self):
        suites = candidate.build()
        self.assertEqual({k: len(v) for k, v in suites.items()},
                         {"context_only": 4, "order_only": 1, "mixed_occ": 4, "exhaustive": 128})
        self.assertEqual({k: sum(len(e["rows"]) for e in v) for k, v in suites.items()},
                         {"context_only": 4, "order_only": 8, "mixed_occ": 32, "exhaustive": 256})
        self.assertTrue(all(e["reset_before"] for suite in suites.values() for e in suite))
        self.assertTrue(all({(r["focus_generation"], r["surface_mode"], r["evidence_fresh"]) for r in e["rows"]}.__len__() == 1
                            for suite in suites.values() for e in suite))

    def test_order_pairs_are_episode_local(self):
        suites = candidate.build()
        for e in suites["mixed_occ"]:
            found = {(a["event"], b["event"]) for i, a in enumerate(e["rows"]) for b in e["rows"][i+1:]}
            self.assertEqual(found, set(itertools.product(candidate.EVENTS, repeat=2)))
        self.assertEqual(len(suites["mixed_occ"]), 4)  # no cross-reset event pair is needed


if __name__ == "__main__":
    unittest.main()
