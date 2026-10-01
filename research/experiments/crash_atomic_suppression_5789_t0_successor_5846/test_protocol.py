"""Construction-only checks; these tests are not formal experiment rows."""

import unittest

import protocol


class ProtocolConstructionTests(unittest.TestCase):
    def test_schedule_has_unique_case_policy_pairs(self):
        pairs = [(row["case"], row["policy"]) for row in protocol.CASES]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(len(protocol.CASES), 15)

    def test_cutpoint_inventory_is_frozen(self):
        cases = {row["case"] for row in protocol.CASES}
        self.assertEqual(
            cases,
            {
                "pre_write",
                "partial_split_write",
                "pre_commit",
                "post_commit_pre_ack",
                "acknowledged_restart",
                "new_generation_same_fingerprint",
                "changed_target_same_label",
                "reactivation",
                "expiry_gc_tombstone",
                "malformed_record",
                "repeated_restart",
            },
        )

    def test_identity_binds_target_not_only_display_label(self):
        first = protocol.identity("fp-1", "target-A", "same-label")
        changed = protocol.identity("fp-1", "target-B", "same-label")
        self.assertNotEqual(first, changed)

    def test_identity_is_stable_and_rejects_empty_components(self):
        expected = protocol.identity("fp-1", "target-A", "label")
        self.assertEqual(expected, protocol.identity("fp-1", "target-A", "label"))
        for parts in (("", "t", "l"), ("f", "", "l"), ("f", "t", "")):
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                protocol.identity(*parts)

    def test_schedule_hash_is_stable(self):
        self.assertEqual(protocol.schedule_sha256(), protocol.schedule_sha256())
        self.assertEqual(len(protocol.schedule_sha256()), 64)


if __name__ == "__main__":
    unittest.main()
