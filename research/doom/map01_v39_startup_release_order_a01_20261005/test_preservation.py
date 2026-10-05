from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[3]


class PreservationTests(unittest.TestCase):
    def test_readonly_audit_does_not_replace_frozen_audit(self) -> None:
        target = PACKAGE / "results/AUDIT.json"
        before = target.read_bytes()
        completed = subprocess.run(
            [sys.executable, str(PACKAGE / "audit_readonly.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(completed.stdout.strip())
        self.assertEqual(target.read_bytes(), before)

    def test_guarded_freeze_builder_refuses_existing_freeze(self) -> None:
        target = PACKAGE / "FREEZE.json"
        before = target.read_bytes()
        completed = subprocess.run(
            [sys.executable, str(PACKAGE / "build_freeze_once.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("refusing to overwrite", completed.stderr + completed.stdout)
        self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
