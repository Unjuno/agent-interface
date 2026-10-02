import unittest

import candidate


class SequenceCoverageConstructionTests(unittest.TestCase):
    def test_direct_pair_suite_is_feasible_and_covers_its_denominator(self):
        legal = candidate.legal_words()
        suite = candidate.ordered_pair_suite(legal)
        self.assertEqual(candidate.feasible_adjacent_pairs(legal), candidate.feasible_adjacent_pairs(suite))
        self.assertTrue(all(not any(trace[j:j + 3] == ("OBS", "REV", "ACT") for j in range(len(trace) - 2)) for trace in suite))
        self.assertLess(len(suite), len(legal))

    def test_pair_mutant_discriminates_order_from_presence(self):
        static = candidate.presence_suite()
        pairs = candidate.ordered_pair_suite(candidate.legal_words())
        self.assertFalse(candidate.detects(static, "pair_stale_lease")[0])
        self.assertTrue(candidate.detects(pairs, "pair_stale_lease")[0])

    def test_triple_control_is_beyond_pair_suite(self):
        pairs = candidate.ordered_pair_suite(candidate.legal_words())
        triples = [word for word in candidate.all_words(3) if len(word) == 3 and candidate.simulate(word)["legal"]]
        self.assertFalse(candidate.detects(pairs, "triple_stale_permit")[0])
        self.assertTrue(candidate.detects(triples, "triple_stale_permit")[0])

    def test_impossible_release_and_ping_control(self):
        self.assertFalse(candidate.simulate(("REL",))["legal"])
        self.assertFalse(candidate.simulate(("REV", "REL"))["legal"])
        for trace in candidate.legal_words():
            if "PING" in trace:
                no_ping = tuple(event for event in trace if event != "PING")
                a, b = candidate.simulate(trace), candidate.simulate(no_ping)
                self.assertEqual(a["final_state"], b["final_state"])


if __name__ == "__main__":
    unittest.main()
