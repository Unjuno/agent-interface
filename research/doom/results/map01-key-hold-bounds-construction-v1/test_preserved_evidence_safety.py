"""Ensure frozen evidence helpers cannot overwrite the one-shot result."""
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent
FROZEN = (
    "RAW-30.json", "AUDIT.json", "RUN.json", "PRE-RUN.json",
    "SHA256SUMS.txt", "REPO-SOURCE-AUDIT.json",
)
GUARDS = (
    "run_hold_bound_30.py", "run_hold_bound_30_safe.py",
    "audit_hold_bound_30.py", "audit_repo_sources.py",
    "freeze_hold_bound.py", "make_run_receipt.py",
)


def frozen_hashes():
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in FROZEN
    }


class PreservedEvidenceSafetyTests(unittest.TestCase):
    def test_read_only_verifier_passes(self):
        before = frozen_hashes()
        result = subprocess.run(
            [sys.executable, "-B", "verify_preserved_hold_bound_30.py"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"read_only": true', result.stdout)
        self.assertEqual(frozen_hashes(), before)

    def test_historical_writers_fail_closed_without_mutating_evidence(self):
        before = frozen_hashes()
        for script in GUARDS:
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, "-B", script], cwd=ROOT,
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stdout or result.stderr)
                self.assertEqual(frozen_hashes(), before)


if __name__ == "__main__":
    unittest.main()
