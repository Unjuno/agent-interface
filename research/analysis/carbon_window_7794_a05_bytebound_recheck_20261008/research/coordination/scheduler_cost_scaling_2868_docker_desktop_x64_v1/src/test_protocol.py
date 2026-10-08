import unittest

from generate_schedule import BLOCKS, POLICIES, SIZES, make_schedule
from worker import select


class ProtocolTests(unittest.TestCase):
    def test_schedule_dimensions_and_ties(self):
        schedule = make_schedule()
        self.assertEqual(schedule["sizes"], list(SIZES))
        self.assertEqual(schedule["blocks_per_size"], BLOCKS)
        for size in SIZES:
            data = schedule["sizes_data"][str(size)]
            self.assertEqual(len(data["candidates"]), size)
            self.assertEqual(len(data["blocks"]), BLOCKS)
            self.assertEqual({c["enqueue_seq"] for c in data["candidates"]}, set(range(size)))
            self.assertTrue(all(c["ready"] and c["expires"] is None for c in data["candidates"]))
            self.assertLess(len({(c["priority"], c["deadline"]) for c in data["candidates"]}), size)
            for block in data["blocks"]:
                self.assertEqual(set(block["policy_order"]), set(POLICIES))

    def test_three_policies_match_tuple_oracle(self):
        candidates = [
            {"priority": 1, "deadline": 2, "enqueue_seq": 0, "op_id": "z"},
            {"priority": 1, "deadline": 1, "enqueue_seq": 1, "op_id": "y"},
            {"priority": 3, "deadline": 8, "enqueue_seq": 2, "op_id": "x"},
            {"priority": 1, "deadline": 1, "enqueue_seq": 3, "op_id": "w"},
        ]
        expected = ["x", "y", "w", "z"]
        for policy in POLICIES:
            with self.subTest(policy=policy):
                self.assertEqual(select(policy, candidates), expected)


if __name__ == "__main__":
    unittest.main()
