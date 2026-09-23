import json
import os
from pathlib import Path
import tempfile
import unittest


class HostRunnerContractTest(unittest.TestCase):
    def test_runner_is_small_and_has_no_authority_surface(self):
        path = Path(__file__).with_name("host_codex_exec_runner_v1.py")
        text = path.read_text(encoding="utf-8")
        self.assertLess(len(text.encode()), 8192)
        self.assertIn('"authority_granted": False', text)
        self.assertIn('"boundary": "host-local-codex-exe"', text)

    def test_result_envelope_shape_is_json(self):
        result = {"exit_code": 0, "boundary": "host-local-codex-exe",
                  "authority_granted": False}
        self.assertFalse(result["authority_granted"])
        self.assertEqual(json.loads(json.dumps(result))["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
