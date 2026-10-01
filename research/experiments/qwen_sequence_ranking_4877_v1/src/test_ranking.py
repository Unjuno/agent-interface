import math
import unittest


def rank_candidates(candidates, scores):
    return sorted(candidates, key=lambda item: (-scores[item], item))


class RankingTests(unittest.TestCase):
    def test_sequence_sum_can_reverse_first_token_greedy(self):
        # Candidate A wins the first-token decision, while B has larger full path mass.
        candidates = ["A", "B"]
        token_logprobs = {"A": [-0.1, -5.0], "B": [-0.2, -0.2]}
        scores = {k: sum(v) for k, v in token_logprobs.items()}
        self.assertEqual(max(token_logprobs, key=lambda k: token_logprobs[k][0]), "A")
        self.assertEqual(rank_candidates(candidates, scores)[0], "B")

    def test_deterministic_tie_break(self):
        self.assertEqual(rank_candidates(["z", "a"], {"z": -1.0, "a": -1.0}), ["a", "z"])


if __name__ == "__main__":
    unittest.main()

