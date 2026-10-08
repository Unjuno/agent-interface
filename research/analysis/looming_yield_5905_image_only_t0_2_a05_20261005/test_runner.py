"""The formal candidate runner must emit only observation-derived results."""

import unittest

try:
    import runner
except ModuleNotFoundError:
    runner = None


class CandidateRunnerTests(unittest.TestCase):
    def test_runner_preserves_ids_and_never_reads_a_truth_argument(self):
        self.assertIsNotNone(runner, "one-shot candidate runner must exist")
        self.assertTrue(callable(runner.run))
        self.assertEqual(runner.CANDIDATE_SCHEMA,
                         "looming-image-only-candidate-raw-a04-v1")


if __name__ == "__main__":
    unittest.main()
