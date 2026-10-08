from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

import audit


ROOT = Path(__file__).resolve().parents[3]
PRED = ROOT / audit.PREDECESSOR


class OmittedBaselineAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = json.loads((PRED / "fixture.json").read_text())
        oracle = json.loads((PRED / "oracle.json").read_text())
        raw = json.loads((PRED / "results/allocation-01/candidate/candidate.json").read_text())
        old_audit = json.loads((PRED / "results/allocation-01/audit/audit.json").read_text())
        cls.result = audit.analyze(fixture, oracle, raw, old_audit)

    def test_archive_reconstruction_matches_predecessor_without_regrading(self) -> None:
        self.assertEqual(self.result["integrity_status"], "PASS_ARCHIVE_RECONSTRUCTION", self.result["errors"])
        self.assertEqual(self.result["predecessor_disposition"], "FAIL_METHOD")
        self.assertEqual((self.result["rows"], self.result["seeds"]), (8192, 32))

    def test_ochiai_uses_missing_as_missing_and_pooling_is_not_stratified(self) -> None:
        seed = self.result["seed_results"][0]
        new = seed["new_baselines"]
        self.assertIsNone(new["scores"]["ochiai"]["render"])
        self.assertEqual(new["counts"]["render"]["missing_exposure"], 256)
        cache = new["counts"]["cache"]
        expected = cache["failed_exposed"] / math.sqrt(
            (cache["failed_exposed"] + cache["failed_unexposed"])
            * (cache["failed_exposed"] + cache["passed_exposed"])
        )
        self.assertAlmostEqual(new["scores"]["ochiai"]["cache"], expected)
        self.assertEqual(seed["predecessor_ranks_reconstructed"], True)

    def test_posthoc_baseline_metrics_are_reported_without_gate(self) -> None:
        metrics = self.result["metrics"]
        for name in ("ochiai", "failed_exposure_count", "failed_exposure_rate"):
            self.assertIn(name, metrics)
            self.assertGreaterEqual(metrics[name]["mean_first_fault_reciprocal_rank"], 0.0)
            self.assertLessEqual(metrics[name]["mean_first_fault_reciprocal_rank"], 1.0)


if __name__ == "__main__":
    unittest.main()
