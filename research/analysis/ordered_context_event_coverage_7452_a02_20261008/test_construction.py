import itertools
import unittest

import candidate


class EqualDenominatorTests(unittest.TestCase):
    def test_same_64_obligations_and_comparable_work(self):
        suites = candidate.build()
        self.assertEqual(len(suites["mixed_occ"]), 4)
        self.assertEqual(sum(len(e["rows"]) for e in suites["mixed_occ"]), 32)
        self.assertEqual(len(suites["exhaustive"]), 64)
        self.assertEqual(sum(len(e["rows"]) for e in suites["exhaustive"]), 128)
        expected = set(itertools.product(candidate.CONTEXTS, candidate.EVENTS, candidate.EVENTS))
        mixed = set()
        exhaustive = set()
        for ep in suites["mixed_occ"]:
            ctx = (ep["rows"][0]["focus_generation"], ep["rows"][0]["surface_mode"])
            mixed.update((ctx, a["event"], b["event"]) for i, a in enumerate(ep["rows"]) for b in ep["rows"][i+1:])
        for ep in suites["exhaustive"]:
            a, b = ep["rows"]
            exhaustive.add(((a["focus_generation"], a["surface_mode"]), a["event"], b["event"]))
        self.assertEqual(mixed, expected)
        self.assertEqual(exhaustive, expected)


if __name__ == "__main__":
    unittest.main()
