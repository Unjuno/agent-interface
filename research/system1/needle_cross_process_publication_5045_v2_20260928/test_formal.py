"""Integration regression tests for the frozen host preflight; never invoke Docker."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from formal import (
    EXPECTED_SEED,
    IMAGE,
    frozen_input_sha,
    validate_freeze_identity,
    validate_output_path,
    validate_sources,
)

ROOT = Path(__file__).resolve().parents[3]
EXP = Path(__file__).resolve().parent

class FrozenPreflightTests(unittest.TestCase):
    def test_actual_registered_freeze_has_nested_input_digest(self):
        freeze = json.loads((EXP / "FREEZE.json").read_text(encoding="utf-8"))
        self.assertEqual(freeze["schema"], "needle-cross-process-publication-freeze-v2")
        self.assertEqual(freeze["allocation"], "needle-cross-process-publication-5045-v2-20260928-01")
        self.assertEqual(freeze["issue"], 5066)
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
        freeze = {"schema": "needle-cross-process-publication-freeze-v2",
                  "allocation": "needle-cross-process-publication-5045-v2-20260928-01",
                  "issue": 5066,
                  "image_id": IMAGE, "input_sha256": EXPECTED_SEED}
        with self.assertRaisesRegex(RuntimeError, "input.sha256"):
            validate_freeze_identity(freeze, EXPECTED_SEED)

    def test_wrong_image_and_seed_fail_closed(self):
        good = {"schema": "needle-cross-process-publication-freeze-v2",
                "allocation": "needle-cross-process-publication-5045-v2-20260928-01",
                "issue": 5066,
                "image_id": IMAGE, "input": {"sha256": EXPECTED_SEED}}
        bad_image = dict(good, image_id="sha256:" + "0" * 64)
        with self.assertRaisesRegex(RuntimeError, "image"):
            validate_freeze_identity(bad_image, EXPECTED_SEED)
        with self.assertRaisesRegex(RuntimeError, "input SHA"):
            validate_freeze_identity(good, "0" * 64)

    def test_source_mismatch_and_existing_output_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sample.py").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "source mismatch"):
                validate_sources(root, {"sample.py": "0" * 64})
            output = root / "already-there"
            output.mkdir()
            with self.assertRaisesRegex(RuntimeError, "not exist"):
                validate_output_path(output)

if __name__ == "__main__":
    unittest.main()

