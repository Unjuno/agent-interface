"""CPU-only current-main dataset and sampler controls for Issue #5139."""
import copy
import hashlib
import json
import unittest

from audit_reference import reconstruct_dataset
from make_dataset import CLASSES, build, row_class
from sampler import COUNTS

TEST_SEEDS = (801001, 801003, 801007)


class DatasetTests(unittest.TestCase):
    def test_deterministic_bytes_and_distinct_seed_contract(self):
        a = json.dumps(build(*TEST_SEEDS), sort_keys=True, separators=(",", ":")).encode()
        b = json.dumps(build(*TEST_SEEDS), sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(a).digest(), hashlib.sha256(b).digest())
        with self.assertRaisesRegex(ValueError, "seeds_must_be_distinct"):
            build(801001, 801001, 801007)
        with self.assertRaisesRegex(ValueError, "seed_must_be_positive_integer"):
            build(801001, 0, 801007)

    def test_pool_sizes_counts_nesting_and_separate_heldout(self):
        doc = build(*TEST_SEEDS)
        self.assertEqual(len(doc["support_pool"]), 128)
        self.assertEqual(len(doc["heldout_pool"]), 256)
        self.assertEqual(len(doc["heldout"]), 64)
        for arm, rows in doc["supports"].items():
            self.assertEqual(len(rows), 32)
            self.assertEqual({c: sum(r["class"] == c for r in rows) for c in CLASSES}, COUNTS[arm])
        for class_name in CLASSES:
            small = {r["case_id"] for r in doc["supports"]["balanced"] if r["class"] == class_name}
            large = {r["case_id"] for r in doc["supports"]["imbalanced"] if r["class"] == class_name}
            # Each arm is a prefix of the same independently ranked class pool.
            # The balanced arm intentionally has more examples in the four
            # abstention classes, while the imbalanced arm has more `set` rows.
            if COUNTS["balanced"][class_name] <= COUNTS["imbalanced"][class_name]:
                self.assertTrue(small.issubset(large))
            else:
                self.assertTrue(large.issubset(small))
            self.assertEqual(sum(r["class"] == class_name for r in doc["heldout"]), 8)
        self.assertNotEqual(doc["support_seed"], doc["heldout_seed"])
        self.assertTrue({r["case_id"] for r in doc["support_pool"]}.isdisjoint(r["case_id"] for r in doc["heldout_pool"]))
        self.assertTrue({r["state"]["scope_id"] for r in doc["support_pool"]}.isdisjoint(r["state"]["scope_id"] for r in doc["heldout_pool"]))

    def test_independent_oracle_reconstructs_every_input_row(self):
        doc = build(*TEST_SEEDS)
        self.assertEqual(reconstruct_dataset(doc), [])
        mutated = copy.deepcopy(doc)
        mutated["supports"]["balanced"][0]["case_id"] = "forged"
        self.assertTrue(reconstruct_dataset(mutated))

    def test_split_ids_classes_and_annotations_are_exact(self):
        doc = build(*TEST_SEEDS)
        for pool in (doc["support_pool"], doc["heldout_pool"]):
            self.assertEqual({r["class"] for r in pool}, set(CLASSES))
            for row in pool:
                self.assertEqual(row["class"], row_class(row))
                self.assertIn("status", row["expected_bound"])
                self.assertIn("changed", row["expected_effect"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
