"""Construction-only contract tests; no base or adapter optimizer updates."""
import os
import unittest
from unittest.mock import patch

import torch

import audit
import runner


class ConstructionTests(unittest.TestCase):
    def test_seed_schedule_is_fresh_and_unique(self):
        self.assertEqual(runner.SEEDS, (734211, 734311, 734411))
        self.assertEqual(len(set(runner.SEEDS)), 3)
        retired = {734011, 734012, 68117, 68229, 68341, 66117, 66229, 66341,
                   6811701, 6812701, 6813701, 6825731, 6826731, 6827731}
        self.assertFalse(set(runner.SEEDS) & retired)

    def test_support_is_balanced_deterministic_and_stream_disjoint(self):
        x, y = runner.balanced_support(734211)
        x2, y2 = runner.balanced_support(734211)
        heldout = runner.data(256, 734211, 404)
        self.assertTrue(torch.equal(x, x2))
        self.assertTrue(torch.equal(y, y2))
        self.assertEqual(y.bincount(minlength=2).tolist(), [8, 8])
        self.assertEqual(x[:, 0].long().bincount(minlength=2).tolist(), [8, 8])
        self.assertEqual(heldout[:, 0].long().bincount(minlength=2).tolist(), [128, 128])
        support_rows = {tuple(row) for row in x.tolist()}
        heldout_rows = {tuple(row) for row in heldout.tolist()}
        self.assertFalse(support_rows & heldout_rows)
        self.assertTrue(torch.equal(y, runner.labels_b(x)))
        self.assertTrue(torch.equal(runner.labels_a(x) + y, torch.ones(16, dtype=torch.long)))

    def test_zero_adapter_delta_preserves_base_logits_exactly(self):
        torch.manual_seed(734211)
        core = runner.Core()
        adapter = runner.Adapter()
        with torch.no_grad():
            adapter.right.zero_()
        x = runner.data(32, 734211, 303)
        with torch.no_grad():
            self.assertTrue(torch.equal(core(x), adapter(core, x)))

    def test_arm_schedules_consume_each_feedback_once(self):
        single = [runner.update_batch("SINGLE", i) for i in range(16)]
        micro = [runner.update_batch("MICROBATCH2", i) for i in range(16)]
        self.assertEqual(single, [[i] for i in range(16)])
        self.assertEqual([b for b in micro if b], [[0, 1], [2, 3], [4, 5], [6, 7],
                                                  [8, 9], [10, 11], [12, 13], [14, 15]])
        self.assertEqual(sorted(i for b in micro for i in b), list(range(16)))
        self.assertEqual(sum(runner.steps_per_arrival("SINGLE", i) for i in range(16)), 128)
        self.assertEqual(sum(runner.steps_per_arrival("MICROBATCH2", i) for i in range(16)), 128)
        self.assertEqual([runner.steps_per_arrival("MICROBATCH2", i) for i in range(4)], [0, 16, 0, 16])

    def test_invalid_role_and_scope_yield_without_proposal(self):
        before = {"adapter": "frozen-digest"}
        outputs = [runner.route("UNKNOWN", "synthetic-role-v1"),
                   runner.route("B", "stale-scope")]
        self.assertTrue(all(x == {"status": "YIELD", "selected_role": None, "proposal": None}
                            for x in outputs))
        self.assertEqual(before, {"adapter": "frozen-digest"})

    def test_missing_environment_stops_before_any_seed_run(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(runner, "run_seed", side_effect=AssertionError("training attempted")) as run:
            with self.assertRaises(SystemExit) as raised:
                runner.main()
            self.assertEqual(str(raised.exception), "STOP_INVALID_TRAINING_ENV")
            run.assert_not_called()

    def test_invalid_seed_schedule_stops_before_any_seed_run(self):
        with patch.dict(os.environ, {"NEEDLE_OUTPUT": "/unused", "NEEDLE_SEEDS": "1,2,3"}), \
             patch.object(runner, "run_seed", side_effect=AssertionError("training attempted")) as run:
            with self.assertRaises(SystemExit) as raised:
                runner.main()
            self.assertEqual(str(raised.exception), "STOP_SEED_ALLOCATION_MISMATCH")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
