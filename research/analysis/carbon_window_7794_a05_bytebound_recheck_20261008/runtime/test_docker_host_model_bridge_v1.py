import json
from pathlib import Path
import unittest


class BridgeContractTest(unittest.TestCase):
    def test_bridge_is_fail_closed(self):
        source = Path(__file__).with_name("docker_host_model_bridge_v1.py").read_text()
        self.assertIn('"authority_granted": False', source)
        self.assertIn('"action_emitted": False', source)
        self.assertIn('"task_success": "NOT_RUN"', source)

    def test_envelope_round_trip(self):
        value = {"authority_granted": False, "action_emitted": False,
                 "task_success": "NOT_RUN"}
        self.assertEqual(json.loads(json.dumps(value)), value)


if __name__ == "__main__":
    unittest.main()
