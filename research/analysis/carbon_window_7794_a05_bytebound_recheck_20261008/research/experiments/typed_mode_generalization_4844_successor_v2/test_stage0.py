"""Construction and audit-contract controls; no formal output is created."""
from __future__ import annotations

import unittest
import hashlib
import json
from pathlib import Path

from audit import audit_bytes, mutation_controls, validate
from experiment import ALLOCATION, BLOCKS, PRIMARY, run

CONSTRUCTION_TRAIN_SEED = 17001
CONSTRUCTION_TEST_SEED = 17002


class Stage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(CONSTRUCTION_TRAIN_SEED, CONSTRUCTION_TEST_SEED)

    def test_positive_row_accounting_and_seeds(self):
        self.assertEqual(self.result["allocation"], ALLOCATION)
        self.assertEqual((self.result["train_seed"], self.result["test_seed"]), (CONSTRUCTION_TRAIN_SEED, CONSTRUCTION_TEST_SEED))
        self.assertEqual(len(self.result["rows"]), 4800)
        self.assertEqual(set(self.result["summary"]), set(BLOCKS))
        self.assertEqual(set(self.result["primary_blocks"]), set(PRIMARY))
        self.assertEqual(validate(self.result, CONSTRUCTION_TRAIN_SEED, CONSTRUCTION_TEST_SEED), [])

    def test_frozen_source_hashes_and_freeze_sidecar(self):
        root = Path(__file__).parent
        freeze_bytes = (root / "FREEZE.json").read_bytes()
        freeze = json.loads(freeze_bytes)
        sidecar = (root / "FREEZE.sha256").read_text(encoding="ascii").strip()
        self.assertEqual(hashlib.sha256(freeze_bytes).hexdigest(), sidecar)
        for name, expected in freeze["source_sha256"].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected, name)

    def test_each_block_is_balanced_and_fixed_size(self):
        for block in BLOCKS:
            rows = [row for row in self.result["rows"] if row["block"] == block]
            self.assertEqual(len(rows), 960)
            self.assertEqual([sum(row["mode"] == mode for row in rows) for mode in range(5)], [192] * 5)

    def test_all_frozen_mutations_reject(self):
        controls = mutation_controls(self.result, CONSTRUCTION_TRAIN_SEED, CONSTRUCTION_TEST_SEED)
        self.assertEqual(len(controls), 16)
        self.assertTrue(all(controls.values()), controls)

    def test_auditor_binds_canonical_bytes_and_rejects_duplicate_json_keys(self):
        encoded = (json.dumps(self.result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
        accepted = audit_bytes(encoded, hashlib.sha256(encoded).hexdigest(), CONSTRUCTION_TRAIN_SEED, CONSTRUCTION_TEST_SEED)
        self.assertTrue(accepted["accepted"], accepted["errors"])
        duplicate = b'{"allocation":"bad","allocation":"bad"}\n'
        rejected = audit_bytes(duplicate, hashlib.sha256(duplicate).hexdigest(), CONSTRUCTION_TRAIN_SEED, CONSTRUCTION_TEST_SEED)
        self.assertFalse(rejected["accepted"])

    def test_complete_and_unknown_controls(self):
        self.assertEqual(len(self.result["full_observation"]), 5)
        self.assertTrue(all(row["direct"] == row["typed"] == row["truth"] for row in self.result["full_observation"]))
        self.assertIsNone(self.result["unknown"]["direct"])
        self.assertIsNone(self.result["unknown"]["typed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
