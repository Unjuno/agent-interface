"""Zero-optimizer-update checks for role routing and separate online skills."""
import os
import sys
import unittest
from unittest.mock import patch

import torch
import torch.nn.functional as F

import audit
import runner
import construction


class RoleRouterConstruction(unittest.TestCase):
    def test_excluded_construction_seed_is_successor_only(self):
        self.assertEqual(runner.ALLOCATION, "needle-role-skill-joint-retention-20260928-v5")
        self.assertEqual(runner.SEEDS, (9970211, 9970311, 9970411))
        self.assertNotIn(9970014, runner.SEEDS)
        self.assertNotIn(736514, runner.SEEDS)

    def test_construction_rejects_wrong_seed_and_missing_output_before_fit(self):
        cases = [
            (["construction.py", "--seed", "9970211"], {}, "STOP_CONSTRUCTION_SEED_MISMATCH"),
            (["construction.py", "--seed", "9970014"], {}, "STOP_CONSTRUCTION_OUTPUT_MISSING"),
        ]
        for argv, env, expected in cases:
            with patch.object(sys, "argv", argv), patch.dict(os.environ, env, clear=True), \
                 patch.object(runner, "run_seed", side_effect=AssertionError("fit attempted")) as fit:
                with self.assertRaises(SystemExit) as raised:
                    construction.main()
                self.assertEqual(str(raised.exception), expected)
                fit.assert_not_called()

    def test_fresh_seeds_and_role_conditioned_splits(self):
        self.assertEqual(runner.SEEDS, (9970211, 9970311, 9970411))
        self.assertEqual(runner.ARMS, ("SHARED_B_ONLY", "SHARED_A_REPLAY",
                                       "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS"))
        data = [runner.sample(256, 9970014, salt, role)
                for salt, role in ((101, 0), (202, 0), (303, 1), (404, 0), (505, 1))]
        sets = [{tuple(row) for row in rows.tolist()} for rows in data]
        self.assertTrue(all(not sets[i] & sets[j] for i in range(5) for j in range(i + 1, 5)))
        self.assertTrue(torch.equal(data[0][:, 8], torch.zeros(256)))
        self.assertTrue(torch.equal(data[2][:, 8], torch.ones(256)))
        self.assertTrue(torch.equal(runner.label_a(data[0]), data[0][:, 0].long()))
        self.assertTrue(torch.equal(runner.label_b(data[2]), 1 - data[2][:, 0].long()))
        self.assertEqual(audit.sample(256, 9970014, 303, 1).tolist(), data[2].tolist())

    def test_dataset_hash_contract_requires_exact_keys_and_binds_schedule(self):
        fields = {key: [index, key] for index, key in enumerate(runner.DATASET_FIELDS)}
        hashes = runner.dataset_hashes(fields)
        self.assertEqual(set(hashes), set(runner.DATASET_FIELDS))
        self.assertEqual(hashes["base_row_indices"], runner.sha(runner.canonical(fields["base_row_indices"])))
        broken = dict(fields)
        del broken["base_row_indices"]
        with self.assertRaisesRegex(ValueError, "dataset_hash_key_set_mismatch"):
            runner.dataset_hashes(broken)

    def test_route_receipts_fail_closed_and_bind_adapter_generation_scope(self):
        ready = runner.route("B", "synthetic-role-v1", 3, 3)
        self.assertEqual(ready["status"], "READY")
        self.assertEqual(ready["adapter_id"], "skill-B-online-v1")
        self.assertEqual(runner.route("A", "synthetic-role-v1", 3, 3)["adapter_id"],
                         "skill-A-immutable-v1")
        self.assertEqual(runner.route("A", "synthetic-role-v1", 3, 3, False)["adapter_id"],
                         "role-shared-online-v1")
        self.assertEqual(runner.route("B", "synthetic-role-v1", 3, 3, False)["adapter_id"],
                         "role-shared-online-v1")
        for args in (("UNKNOWN", "synthetic-role-v1", 3, 3),
                     ("A", "wrong", 3, 3), ("B", "synthetic-role-v1", 2, 3)):
            result = runner.route(*args)
            self.assertEqual(result["status"], "YIELD")
            self.assertIsNone(result["adapter_id"])
            self.assertIsNone(result["proposal"])

    def test_freeze_sidecar_requires_exact_bare_digest_line(self):
        payload = b'{"allocation":"test"}\n'
        digest = runner.sha(payload).encode("ascii")
        self.assertTrue(audit.valid_freeze_sidecar(digest + b"\n", payload))
        self.assertFalse(audit.valid_freeze_sidecar(digest + b"  FREEZE.json\n", payload))
        self.assertFalse(audit.valid_freeze_sidecar(digest.upper() + b"\n", payload))

    def test_batch_schedules_and_skill_identity(self):
        expected_replay = [(arrival * 8 + step) % 16 for arrival in range(16) for step in range(8)]
        self.assertEqual(len(expected_replay), 128)
        self.assertEqual([expected_replay.count(index) for index in range(16)], [8] * 16)
        adapter_a, adapter_b = runner.Adapter(), runner.Adapter()
        self.assertIsNot(adapter_a, adapter_b)
        self.assertNotEqual(adapter_a.left.data_ptr(), adapter_b.left.data_ptr())

    def test_duplicate_batch_mean_loss_control(self):
        torch.manual_seed(9970211)
        model = runner.Core()
        row = runner.sample(2, 9970211, 303, 1)[:1]
        label = runner.label_b(row)
        self.assertLessEqual(abs(float(F.cross_entropy(model(row), label)) -
                                  float(F.cross_entropy(model(row.repeat(2, 1)), label.repeat(2)))),
                             1e-6)

    def test_invalid_formal_env_and_seed_stop_before_fit(self):
        for env, expected in (({}, "STOP_INVALID_TRAINING_ENV"),
                              ({"NEEDLE_OUTPUT": "/unused", "NEEDLE_SEEDS": "1,2,3"},
                               "STOP_SEED_ALLOCATION_MISMATCH")):
            with patch.dict(os.environ, env, clear=True), \
                 patch.object(runner, "run_seed", side_effect=AssertionError("fit attempted")) as fit:
                with self.assertRaises(SystemExit) as raised:
                    runner.main()
                self.assertEqual(str(raised.exception), expected)
                fit.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)

