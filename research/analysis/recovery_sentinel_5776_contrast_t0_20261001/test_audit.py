"""Construction-only tests; these do not consume the Docker allocation."""
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


class ContrastAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load("runner")
        cls.audit = load("audit")
        cls.fixture = json.loads((HERE / "fixture.json").read_text())

    def test_complete_population_and_expected_scoped_failure(self):
        raw = self.runner.build(self.fixture)
        result = self.audit.audit(raw, self.fixture)
        self.assertEqual(len(raw["episodes"]), 672)
        self.assertEqual(result["event_rows"], 67200)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["disposition"], "FAIL_METHOD_SCOPED")
        self.assertEqual(result["metrics"]["gradual_recovery_sensitivity"], 1.0)
        self.assertEqual(result["metrics"]["pointwise_margin_sensitivity"], 0.0)
        self.assertEqual(result["metrics"]["minimum_target_warning_lead_ticks"], 14)
        self.assertEqual(result["metrics"]["recovery_false_alarm_rate"], 0.25)
        self.assertEqual(result["metrics"]["recovery_false_alarm_rate_by_load"],
                         {"low": 0.25, "near": 0.25, "high": 0.25})

    def test_fixture_identity_and_event_corruptions_rejected(self):
        raw = self.runner.build(self.fixture)
        altered = json.loads(json.dumps(raw))
        altered["fixture_sha256"] = "0" * 64
        self.assertIn("fixture_identity", self.audit.audit(altered, self.fixture)["errors"])

        altered = json.loads(json.dumps(raw))
        altered["episodes"][0]["events"][12]["service_units"] += 1
        self.assertTrue(self.audit.audit(altered, self.fixture)["errors"])

    def test_population_deletion_rejected(self):
        raw = self.runner.build(self.fixture)
        raw["episodes"].pop()
        self.assertIn("episode_inventory", self.audit.audit(raw, self.fixture)["errors"])


if __name__ == "__main__":
    unittest.main()
