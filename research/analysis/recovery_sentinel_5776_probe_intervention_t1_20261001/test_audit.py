"""Host-only construction tests; never count as the formal allocation."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProbeInterventionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load("runner")
        cls.auditor = load("audit")
        cls.fx = json.loads((HERE / "fixture.json").read_text())

    def test_population_replays_and_target_is_outcome_eligible(self):
        raw = self.runner.build(self.fx)
        result = self.auditor.audit(raw, self.fx)
        self.assertEqual(len(raw["pairs"]), 90)
        self.assertEqual(result["event_rows_reconstructed"], 17_280)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["eligible_target"])
        self.assertEqual(result["metrics_by_mechanism"]["gradual_capacity_loss"]["eligible_no_probe_losses"], 18)
        self.assertEqual(result["metrics_by_mechanism"]["gradual_capacity_loss"]["eligible_probe_losses"], 18)
        for load in ("low", "near", "high"):
            cell = result["metrics_by_load_and_mechanism"][f"{load}:gradual_capacity_loss"]
            self.assertEqual(cell["pairs"], 6)
            self.assertEqual(cell["no_probe_losses"], 6)
            self.assertEqual(cell["probe_losses"], 6)

    def test_measurement_effect_is_a_predeclared_paired_gate(self):
        result = self.auditor.audit(self.runner.build(self.fx), self.fx)
        target = result["metrics_by_mechanism"]["gradual_capacity_loss"]
        self.assertGreaterEqual(target["median_loss_advance_ticks"], 4)
        self.assertEqual(result["disposition"], "PASS_PROBE_ADVANCES_ENDPOINT_IN_FIXTURE")

    def test_auditor_rejects_event_mutation(self):
        raw = self.runner.build(self.fx)
        raw["pairs"][0]["probe"]["events"][20]["served"] += 1
        self.assertTrue(self.auditor.audit(raw, self.fx)["errors"])

    def test_auditor_rejects_missing_pair(self):
        raw = self.runner.build(self.fx)
        raw["pairs"].pop()
        self.assertIn("pair_inventory_or_order", self.auditor.audit(raw, self.fx)["errors"])


if __name__ == "__main__":
    unittest.main()
