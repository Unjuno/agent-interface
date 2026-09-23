import os
from pathlib import Path
import unittest


class RunnerSelectionTest(unittest.TestCase):
    def test_default_is_legacy_runner(self):
        source = Path(__file__).with_name("integrated_efficiency_model_v1.py").read_text()
        self.assertIn("AGENT_INTERFACE_MODEL_RUNNER", source)
        self.assertIn("target_handle_model_runner_v2.py", source)

    def test_host_runner_is_additive_override(self):
        source = Path(__file__).with_name("schema_preflight_v1.py").read_text()
        self.assertIn("AGENT_INTERFACE_MODEL_RUNNER", source)
        self.assertIn("RUNNER.name", source)


if __name__ == "__main__":
    unittest.main()
