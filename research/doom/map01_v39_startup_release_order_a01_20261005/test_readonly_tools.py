from __future__ import annotations

import subprocess
import sys
import unittest
import json
from pathlib import Path


PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[2]


class ReadOnlyToolTests(unittest.TestCase):
    def test_audit_does_not_replace_retained_audit_result(self) -> None:
        output = PKG / "results" / "AUDIT.json"
        before = output.read_bytes()

        result = subprocess.run(
            [sys.executable, str(PKG / "audit.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertTrue(result.stdout.strip())
        self.assertEqual(output.read_bytes(), before)

    def test_freeze_builder_prints_proposal_without_replacing_retained_freeze(self) -> None:
        output = PKG / "FREEZE.json"
        before = output.read_bytes()

        result = subprocess.run(
            [sys.executable, str(PKG / "build_freeze.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        proposed = json.loads(result.stdout)
        self.assertEqual(proposed["base_commit"], "b347d6f1ede81f6980932f2d7cba6d4758bf49c9")
        self.assertIn("source_sha256", proposed)
        self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
