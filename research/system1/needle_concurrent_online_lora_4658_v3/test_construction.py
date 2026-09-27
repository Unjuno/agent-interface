"""Construction-only tests; no optimizer is constructed and no training runs."""
import unittest
import ast
from pathlib import Path

import torch

import runner
import audit


class ConstructionTests(unittest.TestCase):
    def test_all_frozen_python_sources_parse_without_execution(self):
        for name in ("runner.py", "audit.py", "formal.py", "test_construction.py"):
            ast.parse((Path(__file__).parent / name).read_text(encoding="utf-8"), filename=name)

    def test_schedule_and_seed_contract(self):
        self.assertEqual(runner.SEEDS, (99771, 99883, 99991))
        self.assertEqual((runner.ARRIVALS, runner.STEPS_PER_ARRIVAL, runner.BATCH), (12, 16, 2048))
        self.assertEqual((runner.QUERIES, runner.PERIOD_NS), (120, 16_666_667))
        self.assertEqual(len(set(runner.SEEDS)), 3)

    def test_audit_contract_rejects_wrong_batch_and_order(self):
        self.assertEqual(audit.EXPECTED_SEEDS, (99771, 99883, 99991))
        self.assertEqual((audit.EXPECTED_ARRIVALS, audit.EXPECTED_STEPS,
                          audit.EXPECTED_BATCH, audit.EXPECTED_QUERIES),
                         (12, 16, 2048, 120))
        ordered = [{"arrival": a + 1, "update": a * 16 + u + 1}
                   for a in range(12) for u in range(16)]
        self.assertTrue(audit.valid_training_order(ordered))
        broken = list(ordered)
        broken[0], broken[1] = broken[1], broken[0]
        self.assertFalse(audit.valid_training_order(broken))
        per_arrival_reset = [{"arrival": a + 1, "update": u + 1}
                             for a in range(12) for u in range(16)]
        self.assertFalse(audit.valid_training_order(per_arrival_reset))
        self.assertFalse(audit.valid_cell_identity(99771, "COW", 12, 16, 512, 120))
        self.assertFalse(audit.valid_cell_identity(100000, "COW", 12, 16, 2048, 120))

    def test_snapshot_is_value_copy_and_digest_bound(self):
        a, b = torch.ones((2, 16)), torch.zeros((4, 2))
        frozen = runner.snapshot(a, b, 3)
        claimed = frozen.pop("sha256")
        self.assertEqual(claimed, runner.digest_obj(frozen))
        before = frozen["a"]
        a.add_(5)
        self.assertEqual(frozen["a"], before)

    def test_atomic_publish_returns_complete_immutable_pointer(self):
        cell, lock = {"current": {"version": 0, "payload": ("old-a", "old-b")}}, __import__("threading").Lock()
        old = runner.capture_active(cell, lock)
        new = {"version": 1, "payload": ("new-a", "new-b")}
        runner.atomic_publish(cell, lock, new)
        self.assertIs(runner.capture_active(cell, lock), new)
        self.assertEqual(old["payload"], ("old-a", "old-b"))

    def test_odd_or_changed_shared_generation_is_unstable(self):
        self.assertFalse(runner.generation_is_stable(1, 1))
        self.assertFalse(runner.generation_is_stable(2, 4))
        self.assertTrue(runner.generation_is_stable(4, 4))
        self.assertFalse(audit.stable_generation(1, 1))
        self.assertFalse(audit.stable_generation(2, 4))

    def test_unknown_or_changed_active_version_is_rejected(self):
        available = {"0": {"a": [], "b": []}}
        self.assertTrue(audit.available_version(0, 0, available))
        self.assertFalse(audit.available_version(1, 1, available))
        self.assertFalse(audit.available_version(0, 1, available))

    def test_fixed_forward_is_finite_and_bounded(self):
        base = {"w1": torch.zeros((16, 8)).tolist(), "b1": torch.zeros(16).tolist(),
                "w2": torch.zeros((4, 16)).tolist(), "b2": torch.zeros(4).tolist()}
        logits = runner.predict(base, torch.zeros((2, 16)), torch.zeros((4, 2)), torch.zeros((1, 8)))
        self.assertEqual(tuple(logits.shape), (1, 4))
        self.assertTrue(torch.isfinite(logits).all().item())

    def test_independent_oracle_preserves_all_four_logits(self):
        base = {"w1": torch.zeros((16, 8)).tolist(), "b1": torch.zeros(16).tolist(),
                "w2": torch.zeros((4, 16)).tolist(), "b2": [0.1, 0.2, 0.3, 0.4]}
        adapter = {"a": torch.zeros((2, 16)).tolist(), "b": torch.zeros((4, 2)).tolist()}
        query = [0.0] * 8
        runner_logits = runner.predict(base, torch.zeros((2, 16)), torch.zeros((4, 2)), torch.tensor([query]))[0]
        oracle_logits = audit.oracle(base, adapter, query)
        self.assertEqual(tuple(oracle_logits.shape), (4,))
        self.assertTrue(audit.valid_logits(oracle_logits))
        self.assertTrue(torch.equal(runner_logits, oracle_logits))
        self.assertFalse(audit.valid_logits(torch.tensor(oracle_logits[0].item())))


if __name__ == "__main__":
    unittest.main()
