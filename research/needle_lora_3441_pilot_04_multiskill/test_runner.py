"""Construction tests only; these do not run the formal GPU allocation."""
import unittest

import torch

import runner


class MultiSkillConstructionTests(unittest.TestCase):
    def test_three_skills_encode_distinct_expected_bit_mappings(self):
        x = torch.tensor([
            [1.0, 1.0, 0, 0, 0, 0, 0, 0],
            [-1.0, 1.0, 0, 0, 0, 0, 0, 0],
            [1.0, -1.0, 0, 0, 0, 0, 0, 0],
            [-1.0, -1.0, 0, 0, 0, 0, 0, 0],
        ])
        self.assertEqual(runner.labels(x, "skill_a").tolist(), [3, 1, 2, 0])
        self.assertEqual(runner.labels(x, "skill_b").tolist(), [1, 3, 0, 2])
        self.assertEqual(runner.labels(x, "skill_c").tolist(), [2, 0, 3, 1])

    def test_rank_two_adapter_has_only_forty_trainable_parameters(self):
        base = runner.BasePolicy()
        adapter = runner.RankTwoAdapter(base)
        self.assertEqual(sum(p.numel() for p in adapter.parameters() if p.requires_grad), 40)
        self.assertTrue(all(not p.requires_grad for p in base.parameters()))

    def test_skill_receipts_route_only_to_their_named_model(self):
        base = runner.BasePolicy()
        adapters = {"adapter-b": runner.RankTwoAdapter(base),
                    "adapter-c": runner.RankTwoAdapter(base)}
        cases = (
            ("skill_a", {"epoch": 7, "adapter_id": "base", "adapter_version": 0}, base),
            ("skill_b", {"epoch": 7, "adapter_id": "adapter-b", "adapter_version": 1}, adapters["adapter-b"]),
            ("skill_c", {"epoch": 7, "adapter_id": "adapter-c", "adapter_version": 1}, adapters["adapter-c"]),
        )
        for skill, receipt, expected in cases:
            with self.subTest(skill=skill):
                decision, model = runner.route(skill, receipt, base, adapters)
                self.assertEqual(decision, "PROPOSE")
                self.assertIs(model, expected)

    def test_invalid_skill_epoch_and_adapter_metadata_yield(self):
        base = runner.BasePolicy()
        adapters = {"adapter-b": runner.RankTwoAdapter(base),
                    "adapter-c": runner.RankTwoAdapter(base)}
        cases = (
            ("unknown", {"epoch": 7, "adapter_id": "adapter-b", "adapter_version": 1}),
            ("skill_b", {"epoch": 6, "adapter_id": "adapter-b", "adapter_version": 1}),
            ("skill_b", {"epoch": 7, "adapter_id": "adapter-c", "adapter_version": 1}),
            ("skill_b", {"epoch": 7, "adapter_version": 1}),
            ("skill_b", {"epoch": 7, "adapter_id": "adapter-b"}),
            ("skill_b", {"epoch": True, "adapter_id": "adapter-b", "adapter_version": 1}),
        )
        for skill, receipt in cases:
            with self.subTest(skill=skill, receipt=receipt):
                decision, model = runner.route(skill, receipt, base, adapters)
                self.assertEqual(decision, "YIELD")
                self.assertIsNone(model)

    def test_tensor_state_comparison_is_exact_and_detects_one_bit_change(self):
        left = {"a": torch.tensor([1.0, 2.0]), "b": torch.tensor([3])}
        right = {key: value.clone() for key, value in left.items()}
        self.assertTrue(runner.tensor_state_equal(left, right))
        right["a"][0] = torch.nextafter(right["a"][0], torch.tensor(float("inf")))
        self.assertFalse(runner.tensor_state_equal(left, right))


if __name__ == "__main__":
    unittest.main()
