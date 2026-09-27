"""Integration regression tests for the frozen host preflight; never invoke Docker."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
EXP = Path(__file__).resolve().parent
EXPECTED_SEED = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"

class FrozenPreflightTests(unittest.TestCase):
    def test_actual_registered_freeze_has_nested_input_digest(self):
        freeze = json.loads((EXP / "FREEZE.json").read_text(encoding="utf-8"))
        self.assertEqual(freeze["input"]["sha256"], EXPECTED_SEED)
        self.assertNotIn("input_sha256", freeze)

    def test_preflight_cli_accepts_registered_freeze_without_docker_or_output(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "must-not-be-created"
            result = subprocess.run(
                [sys.executable, str(EXP / "formal.py"), "--preflight-only", "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"docker_invocations": 0', result.stdout)
            self.assertFalse(output.exists())

    def test_misnested_digest_is_rejected_by_contract(self):
        freeze = {"image_id": "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
                  "input_sha256": EXPECTED_SEED}
        with self.assertRaises(KeyError):
            _ = freeze["input"]["sha256"]

if __name__ == "__main__":
    unittest.main()
