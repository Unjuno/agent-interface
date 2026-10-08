import json
import hashlib
import unittest
from pathlib import Path

import candidate
import audit


ROOT = Path(__file__).parent


class CounterpartyConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.calibration_bytes = (ROOT / "calibration.json").read_bytes()
        cls.calibration = json.loads(cls.calibration_bytes)
        cls.calibration_sha256 = hashlib.sha256(cls.calibration_bytes).hexdigest()
        cls.raw = candidate._simulate(cls.fixture, cls.calibration, cls.calibration_sha256)
        cls.audit = audit.audit(cls.fixture, cls.calibration, cls.calibration_bytes, cls.raw)

    def test_independent_rows_and_all_mutations(self):
        self.assertTrue(self.audit["pass"])
        self.assertEqual(self.audit["reconstructed_rows"], 64)
        self.assertEqual(self.audit["mutation_rejections"], [True] * 5)

    def test_prefix_is_the_only_reactive_selector_signal(self):
        for row in self.raw["rows"]:
            if row["policy"] == "REACTIVE_DECLARED":
                self.assertEqual(set(row["selector_input"]), {"public_prefix", "stage"})
                self.assertNotIn("truth", row["selector_input"])
            if row["policy"] in {"STATIC_BALANCED", "FREQUENCY_MATCHED_REPLAY"}:
                self.assertNotIn("public_prefix", row["selector_input"])

    def test_equal_variant_marginals_and_same_truth(self):
        metrics = self.raw["metrics"]
        for route in ("plain", "effect_boundary"):
            for policy in ("STATIC_BALANCED", "FREQUENCY_MATCHED_REPLAY", "REACTIVE_DECLARED"):
                self.assertEqual(metrics[f"{policy}:{route}"]["variant_counts"], {"V0": 4, "V1": 4})
        self.assertEqual({r["variant_truth_id"] for r in self.raw["rows"]}, {"save-document-01"})
        self.assertEqual({r["target_id"] for r in self.raw["rows"]}, {"document-01"})

    def test_boundary_distinguishes_attempt_from_effect(self):
        metrics = self.raw["metrics"]
        self.assertEqual(metrics["REACTIVE_DECLARED:plain"]["unauthorized_effects"], 4)
        self.assertEqual(metrics["REACTIVE_DECLARED:effect_boundary"]["unauthorized_effects"], 0)
        self.assertEqual(metrics["REACTIVE_DECLARED:effect_boundary"]["unauthorized_proposals"], 4)

    def test_auditor_holds_outcome_fitted_calibration(self):
        bad = dict(self.calibration, heldout_derived=True)
        self.assertFalse(audit.audit(self.fixture, bad, json.dumps(bad).encode(), self.raw)["pass"])


if __name__ == "__main__":
    unittest.main()
