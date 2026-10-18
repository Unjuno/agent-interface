import unittest

from repair import constrained_oracle


class ConstrainedOracleTests(unittest.TestCase):
    def test_no_interruptions_need_no_checkpoint(self):
        self.assertEqual(
            constrained_oracle({"task_units": 2, "legal": [1, 1]}, [0, 0], 3, 1), 0
        )

    def test_one_interruption_costs_one_replayed_unit(self):
        self.assertEqual(
            constrained_oracle({"task_units": 2, "legal": [1, 1, 1]}, [1, 0, 0], 3, 1), 1
        )

    def test_two_interruptions_replay_twice(self):
        self.assertEqual(
            constrained_oracle({"task_units": 2, "legal": [1, 1, 1, 1]}, [1, 1, 0, 0], 3, 1), 2
        )

    def test_checkpoint_requires_legal_boundary(self):
        self.assertEqual(
            constrained_oracle({"task_units": 2, "legal": [0, 1, 1]}, [1, 0, 0], 3, 2), 2
        )


if __name__ == "__main__":
    unittest.main()
