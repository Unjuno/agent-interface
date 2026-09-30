"""Zero-optimizer-update construction checks for the frozen rehearsal study."""
import os
import unittest
from unittest.mock import patch

import torch
import torch.nn.functional as F

import audit
import runner


class RehearsalConstruction(unittest.TestCase):
    def test_fresh_seed_block_and_data_roles(self):
        self.assertEqual(runner.SEEDS, (735211, 735311, 735411))
        self.assertEqual(len(set(runner.SEEDS)), 3)
        a = runner.sample(16, 735211, 202, 0)
        b = runner.sample(16, 735211, 303, 1)
        self.assertTrue(torch.equal(a[:, 8], torch.zeros(16)))
        self.assertTrue(torch.equal(b[:, 8], torch.ones(16)))
        self.assertEqual(runner.label_a(a).bincount(minlength=2).tolist(), [8, 8])
        self.assertEqual(runner.label_b(b).bincount(minlength=2).tolist(), [8, 8])
        self.assertEqual(audit.sample(16, 735211, 202, 0).tolist(), a.tolist())
        self.assertEqual(audit.sample(16, 735211, 303, 1).tolist(), b.tolist())

    def test_split_salts_are_disjoint_and_labels_bind_role(self):
        datasets = [runner.sample(256, 735211, salt, role)
                    for salt, role in ((101, 0), (202, 0), (303, 1), (404, 0), (505, 1))]
        sets = [{tuple(row) for row in data.tolist()} for data in datasets]
        self.assertTrue(all(not sets[i] & sets[j] for i in range(5) for j in range(i + 1, 5)))
        self.assertTrue(torch.equal(runner.label_a(datasets[0]), datasets[0][:, 0].long()))
        self.assertTrue(torch.equal(runner.label_b(datasets[2]), 1 - datasets[2][:, 0].long()))

    def test_three_arm_schedule_consumes_same_feedback_and_memory_once_per_rotation(self):
        self.assertEqual(runner.ARMS, ("B_ONLY", "B_DUPLICATE_CONTROL", "A_REHEARSAL"))
        replay_indices = [(arrival * 8 + step) % 16 for arrival in range(16) for step in range(8)]
        self.assertEqual(len(replay_indices), 128)
        self.assertEqual([replay_indices.count(i) for i in range(16)], [8] * 16)
        self.assertEqual(16 * 8, 128)

    def test_duplicate_batch_mean_loss_matches_single_example(self):
        torch.manual_seed(735211)
        model = runner.Core()
        row = runner.sample(2, 735211, 303, 1)[:1]
        label = runner.label_b(row)
        single = F.cross_entropy(model(row), label)
        duplicate = F.cross_entropy(model(row.repeat(2, 1)), label.repeat(2))
        self.assertEqual(float(single), float(duplicate))

    def test_invalid_role_and_stale_scope_yield_without_proposal(self):
        expected = {"status": "YIELD", "selected_role": None, "proposal": None}
        self.assertEqual(runner.route("UNKNOWN", "synthetic-role-v1"), expected)
        self.assertEqual(runner.route("B", "stale-scope"), expected)

    def test_auditor_mount_check_accepts_arbitrary_host_output_paths(self):
        argv = ["docker", "run", "--mount",
                "type=bind,source=C:/worker/source copy,dst=/src,readonly", "--mount",
                "type=bind,source=D:/results/run 01/raw,dst=/out"]
        self.assertTrue(audit.invocation_mounts_valid(argv))
        argv[-1] = "type=bind,source=D:/results/run 01/formal,dst=/in,readonly"
        self.assertFalse(audit.invocation_mounts_valid(argv))

    def test_missing_or_wrong_formal_environment_stops_before_training(self):
        for env, expected in [({}, "STOP_INVALID_TRAINING_ENV"),
                              ({"NEEDLE_OUTPUT": "/unused", "NEEDLE_SEEDS": "1,2,3"},
                               "STOP_SEED_ALLOCATION_MISMATCH")]:
            with patch.dict(os.environ, env, clear=True), \
                 patch.object(runner, "run_seed", side_effect=AssertionError("fit attempted")) as run:
                with self.assertRaises(SystemExit) as raised:
                    runner.main()
                self.assertEqual(str(raised.exception), expected)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
