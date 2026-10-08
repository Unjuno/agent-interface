import hashlib
import json
import unittest

from make_dataset import CLASSES, build, row_class
from audit_raw import reference_bind, reference_effect
from protocol import bind_intent, simulate_bound


class FrozenDatasetTests(unittest.TestCase):
    def test_deterministic_construction_seed(self):
        a = json.dumps(build(73194011), sort_keys=True, separators=(",", ":")).encode()
        b = json.dumps(build(73194011), sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(a).digest(), hashlib.sha256(b).digest())

    def test_two_distinct_same_pool_support_samplings(self):
        doc = build(73194011)
        self.assertEqual(len(doc["support_pool"]), 128)
        self.assertEqual(set(doc["supports"]), {"imbalanced", "balanced"})
        a, b = doc["supports"]["imbalanced"], doc["supports"]["balanced"]
        self.assertEqual(len(a), 32)
        self.assertEqual(len(b), 32)
        self.assertNotEqual([r["case_id"] for r in a], [r["case_id"] for r in b])
        self.assertEqual(doc["support_counts"]["imbalanced"]["set"], 16)
        self.assertEqual(doc["support_counts"]["balanced"], {name: 4 for name in CLASSES})

    def test_heldout_has_eight_fresh_rows_per_frozen_class(self):
        doc = build(73194011)
        self.assertEqual(len(doc["heldout_pool"]), 256)
        self.assertEqual(len(doc["heldout"]), 64)
        self.assertEqual({c: sum(row_class(r) == c for r in doc["heldout"]) for c in CLASSES},
                         {c: 8 for c in CLASSES})

    def test_no_identity_or_prompt_leakage(self):
        doc = build(73194011)
        support = doc["support_pool"]
        held = doc["heldout_pool"]
        self.assertFalse({r["case_id"] for r in support} & {r["case_id"] for r in held})
        self.assertFalse({r["state"]["scope_id"] for r in support} & {r["state"]["scope_id"] for r in held})
        self.assertFalse({r["task"] for r in support} & {r["task"] for r in held})

    def test_all_rows_have_frozen_oracle_annotations(self):
        doc = build(73194011)
        for row in doc["support_pool"] + doc["heldout_pool"]:
            self.assertEqual(row["class"], row_class(row))
            self.assertIn("status", row["expected_bound"])
            self.assertIn("changed", row["expected_effect"])

    def test_independent_auditor_oracle_matches_generator_oracle(self):
        doc = build(73194011)
        for row in doc["support_pool"] + doc["heldout_pool"]:
            bound = reference_bind(row["intent"], row["state"], row["requested_generation"])
            effect = reference_effect(bound, row["state"])
            self.assertEqual(bound, bind_intent(row["intent"], row["state"], row["requested_generation"]))
            self.assertEqual(effect, simulate_bound(bound, row["state"]))


if __name__ == "__main__":
    unittest.main()
