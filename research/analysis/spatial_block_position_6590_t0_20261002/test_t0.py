from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).resolve().parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class SpatialBlockT0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = candidate.generate(FIXTURE)
        cls.audit = auditor.audit(FIXTURE, cls.raw)

    def test_exact_finite_rows_and_unique_source_noise_ids(self):
        self.assertEqual(self.raw["schema"], "spatial-block-position-6590-t0-raw-v1")
        self.assertEqual(len(self.raw["rows"]), 12_800)
        ids = [row["row_id"] for row in self.raw["rows"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len({row["source_id"] for row in self.raw["rows"]}), len(ids))
        self.assertEqual(len({row["noise_id"] for row in self.raw["rows"]}), len(ids))

    def test_independent_auditor_reconstructs_all_rows_and_method_gates(self):
        self.assertEqual(self.audit["decision"], "METHOD_PASS")
        self.assertEqual(self.audit["errors"], [])
        self.assertTrue(all(self.audit["gates"].values()))

    def test_uniform_positive_control_has_zero_block_range(self):
        field = self.audit["field_summaries"]["uniform_positive_control"]
        self.assertEqual(field["block_holdout"]["max_minus_min_block_rate"], 0.0)
        self.assertTrue(all(b["positive_accept_rate"] == 0.8 for b in field["block_holdout"]["blocks"]))

    def test_hotspot_is_detected_without_using_it_to_choose_blocks(self):
        field = self.audit["field_summaries"]["planted_local_failure_control"]["block_holdout"]
        self.assertEqual(field["worst_block_ids"], ["b11"])
        self.assertEqual(field["minimum_positive_accept_rate"], 0.2)
        self.assertGreaterEqual(field["random_minus_worst_block_rate"], 0.2)
        self.assertTrue(all(b["support_state"] == "QUALIFIED" for b in field["blocks"]))

    def test_random_split_position_overlap_is_labeled_diagnostic_only(self):
        for field in self.audit["field_summaries"].values():
            self.assertEqual(field["random_split"]["scope"], "diagnostic_only")
            self.assertEqual(field["random_split"]["positions_shared_between_random_train_and_test"], 64)
        for field in self.audit["field_summaries"].values():
            self.assertTrue(all(fold["position_overlap_count"] == 0 for fold in field["block_holdout"]["fold_leakage"]))

    def test_empty_support_is_insufficient_and_overlap_probe_is_rejected(self):
        self.assertEqual(self.audit["mutation_controls"]["empty_block_outcome"], "INSUFFICIENT")
        self.assertEqual(self.audit["mutation_controls"]["intentional_position_overlap"], "REJECTED")
        self.assertEqual(auditor._support_state(0, 0, FIXTURE["decision_gate"]), "INSUFFICIENT")

    def test_raw_corruption_fails_closed(self):
        mutated = deepcopy(self.raw)
        mutated["rows"][0]["status"] = "ACCEPT" if mutated["rows"][0]["status"] != "ACCEPT" else "REJECT"
        result = auditor.audit(FIXTURE, mutated)
        self.assertEqual(result["decision"], "HOLD_AUDIT_INTEGRITY")
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
