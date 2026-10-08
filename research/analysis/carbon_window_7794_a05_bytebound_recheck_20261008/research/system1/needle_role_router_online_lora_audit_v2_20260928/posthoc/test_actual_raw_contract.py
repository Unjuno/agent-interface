"""Mutation checks against the immutable #4899 formal raw (audit-only)."""
import json
import unittest
from pathlib import Path

import audit_successor as successor
import audit as predecessor


RAW = Path("/data/raw/formal_result.json")


class ActualFormalRawContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_bytes = RAW.read_bytes()
        cls.raw = json.loads(cls.raw_bytes,
                             object_pairs_hook=predecessor.unique_pairs)

    def test_original_byte_identity_and_all_three_seed_rows(self):
        self.assertEqual(len(self.raw_bytes), successor.EXPECTED_RAW_BYTES)
        self.assertEqual(successor.sha(self.raw_bytes),
                         successor.EXPECTED_RAW_SHA256)
        self.assertEqual([row["seed"] for row in self.raw["runs"]],
                         list(predecessor.SEEDS))

    def test_registered_producer_digest_keyset_is_valid_without_schedule_digest(self):
        for row in self.raw["runs"]:
            with self.subTest(seed=row["seed"]):
                self.assertNotIn("base_row_indices", row["dataset_sha256"])
                self.assertEqual(successor.validate_run_raw(row, row["seed"]), [])

    def test_missing_required_dataset_digest_rejects(self):
        for row in self.raw["runs"]:
            damaged = json.loads(json.dumps(row))
            del damaged["dataset_sha256"]["support_x"]
            self.assertIn(f'{row["seed"]}:dataset_digest_field_set',
                          successor.validate_run_raw(damaged, row["seed"]))

    def test_extra_dataset_digest_rejects(self):
        row = self.raw["runs"][0]
        damaged = json.loads(json.dumps(row))
        damaged["dataset_sha256"]["unexpected"] = "0" * 64
        self.assertIn(f'{row["seed"]}:dataset_digest_field_set',
                      successor.validate_run_raw(damaged, row["seed"]))

    def test_schedule_reorder_rejects(self):
        row = self.raw["runs"][0]
        damaged = json.loads(json.dumps(row))
        damaged["base_row_indices"][0], damaged["base_row_indices"][1] = (
            damaged["base_row_indices"][1], damaged["base_row_indices"][0])
        self.assertIn(f'{row["seed"]}:schedule_reconstruction',
                      successor.validate_run_raw(damaged, row["seed"]))

    def test_schedule_duplicate_rejects(self):
        row = self.raw["runs"][0]
        damaged = json.loads(json.dumps(row))
        damaged["base_row_indices"][1] = damaged["base_row_indices"][0]
        self.assertIn(f'{row["seed"]}:schedule_reconstruction',
                      successor.validate_run_raw(damaged, row["seed"]))

    def test_schedule_value_mutation_rejects(self):
        row = self.raw["runs"][0]
        damaged = json.loads(json.dumps(row))
        damaged["base_row_indices"][0] = (damaged["base_row_indices"][0] + 1) % 256
        self.assertIn(f'{row["seed"]}:schedule_reconstruction',
                      successor.validate_run_raw(damaged, row["seed"]))

    def test_dataset_value_or_digest_mutation_rejects(self):
        row = self.raw["runs"][0]
        for field, mutate in (
            ("support_x", lambda x: x[0].__setitem__(0, 1.0-x[0][0])),
            ("support_x_digest", lambda x: None),
        ):
            damaged = json.loads(json.dumps(row))
            if field == "support_x_digest":
                damaged["dataset_sha256"]["support_x"] = "0" * 64
            else:
                mutate(damaged[field])
            errors = successor.validate_run_raw(damaged, row["seed"])
            self.assertTrue(any(error.startswith(f'{row["seed"]}:support_x:')
                                for error in errors))

    def test_wrong_seed_binding_rejects(self):
        row = self.raw["runs"][0]
        damaged = json.loads(json.dumps(row))
        self.assertIn("736311:seed_identity",
                      successor.validate_run_raw(damaged, 736311))


if __name__ == "__main__":
    unittest.main(verbosity=2)

