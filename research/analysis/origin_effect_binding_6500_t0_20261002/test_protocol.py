from __future__ import annotations

import copy
import unittest

import auditor
import candidate


class OriginEffectBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = candidate.run()
        cls.audit = auditor.audit(cls.raw)

    def test_all_frozen_rows_reconstruct(self):
        self.assertEqual(self.audit["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(self.audit["expected_rows"], 24)
        self.assertEqual(self.audit["received_rows"], 24)
        self.assertEqual(self.audit["unique_rows"], 24)
        self.assertEqual(self.audit["errors"], [])

    def test_origin_gate_blocks_every_nonlegitimate_effect(self):
        self.assertEqual(self.audit["false_allows"]["origin_bound"], 0)
        self.assertEqual(self.audit["legitimate_origin_allows"], 2)

    def test_visual_and_similarity_comparators_admit_lookalikes(self):
        self.assertGreater(self.audit["false_allows"]["visual_only"], 0)
        self.assertGreater(self.audit["false_allows"]["similarity_alarm"], 0)

    def test_missing_process_provenance_is_unknown_not_allow(self):
        row = next(r for r in self.raw["rows"] if r["case_id"] == "UNKNOWN_PROCESS_PROVENANCE"
                   and r["policy"] == "ORIGIN_BOUND")
        self.assertEqual(row["classification"], "UNKNOWN")
        self.assertFalse(row["would_admit"])

    def test_embedded_untrusted_origin_and_recipient_swap_are_rejected(self):
        for case_id in ("UNTRUSTED_EMBEDDED_CONTENT", "WRONG_EFFECT_RECIPIENT"):
            row = next(r for r in self.raw["rows"] if r["case_id"] == case_id
                       and r["policy"] == "ORIGIN_BOUND")
            self.assertEqual(row["classification"], "MISMATCH")
            self.assertFalse(row["would_admit"])

    def test_all_six_frozen_mutation_controls_are_rejected(self):
        self.assertEqual(set(self.audit["mutations_rejected"]), {
            "origin_swap", "stale_generation", "similarity_score_inversion",
            "omit_embedded_origin", "target_identity_change", "recipient_misbinding"})
        self.assertTrue(all(self.audit["mutations_rejected"].values()))

    def test_candidate_truth_or_policy_tampering_is_rejected(self):
        changed = copy.deepcopy(self.raw)
        changed["rows"][0]["effect_origin"] = "app://evil.example"
        self.assertEqual(auditor.audit(changed)["disposition"], "FAIL_AUDIT")

    def test_missing_and_duplicate_rows_are_rejected(self):
        missing = copy.deepcopy(self.raw)
        missing["rows"].pop()
        duplicate = copy.deepcopy(self.raw)
        duplicate["rows"].append(copy.deepcopy(duplicate["rows"][0]))
        self.assertEqual(auditor.audit(missing)["disposition"], "FAIL_AUDIT")
        self.assertEqual(auditor.audit(duplicate)["disposition"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
