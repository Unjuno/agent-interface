"""CPU-only composition tests for dataset generation and independent sampler audit."""
from __future__ import annotations

import copy
import unittest

from audit_sampler import audit_support_selection
from make_dataset import build


FORMAL_SEED = 73194111  # synthetic construction sentinel; not a study seed
OTHER_FORMAL_SEED = 73194112
SUPPORT_SEED = 51829177  # synthetic construction sentinel; not an allocation seed
ALLOCATION = "qwen5139-construction-only-fixture"


class DatasetConstructionTests(unittest.TestCase):
    def test_full_generated_dataset_satisfies_support_audit_and_split_shape(self):
        dataset = build(FORMAL_SEED, SUPPORT_SEED, ALLOCATION)
        self.assertEqual(audit_support_selection(dataset), [])
        self.assertEqual(len(dataset["support_pool"]), 128)
        self.assertEqual(len(dataset["heldout_pool"]), 256)
        self.assertEqual(len(dataset["heldout"]), 64)
        self.assertEqual(len(dataset["supports"]["imbalanced"]), 32)
        self.assertEqual(len(dataset["supports"]["balanced"]), 32)
        self.assertFalse(
            {r["case_id"] for r in dataset["support_pool"]}
            & {r["case_id"] for r in dataset["heldout_pool"]}
        )
        self.assertFalse(
            {r["state"]["scope_id"] for r in dataset["support_pool"]}
            & {r["state"]["scope_id"] for r in dataset["heldout_pool"]}
        )
        self.assertFalse(
            {r["task"] for r in dataset["support_pool"]}
            & {r["task"] for r in dataset["heldout_pool"]}
        )

    def test_formal_seed_change_does_not_change_support_rows(self):
        first = build(FORMAL_SEED, SUPPORT_SEED, ALLOCATION)
        second = build(OTHER_FORMAL_SEED, SUPPORT_SEED, ALLOCATION)
        self.assertEqual(first["support_pool"], second["support_pool"])
        self.assertEqual(first["supports"], second["supports"])
        self.assertNotEqual(first["heldout_pool"], second["heldout_pool"])
        self.assertEqual(audit_support_selection(second), [])

    def test_independent_auditor_detects_changed_support_seed(self):
        dataset = build(FORMAL_SEED, SUPPORT_SEED, ALLOCATION)
        mutated = copy.deepcopy(dataset)
        mutated["support_seed"] = SUPPORT_SEED + 1
        self.assertIn("selected_id_order:balanced", audit_support_selection(mutated))


if __name__ == "__main__":
    unittest.main()
