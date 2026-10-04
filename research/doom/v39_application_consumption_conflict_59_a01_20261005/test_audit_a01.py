#!/usr/bin/env python3
"""Regression tests for the saved A01 result auditor."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class SavedResultAuditTests(unittest.TestCase):
    def run_auditor_in_copy(self, mutate=False):
        with tempfile.TemporaryDirectory(prefix="a01-audit-test-") as temporary:
            copied_root = Path(temporary) / "experiment"
            shutil.copytree(ROOT, copied_root)
            raw_path = copied_root / "raw" / "A01.json"
            if mutate:
                raw = json.loads(raw_path.read_text())
                for implementation in ("baseline", "candidate"):
                    cases = raw["interval_sweep"][implementation]["cases"]
                    paired = next(row for row in cases
                                  if row["expected_ordered"] is True)
                    incomplete = next(row for row in cases
                                      if row["expected_ordered"] is False)
                    for row, claimed_ordered in ((paired, False), (incomplete, True)):
                        row["expected_ordered"] = claimed_ordered
                        row["status"] = (
                            "adapter_edge_brackets_paired" if claimed_ordered else
                            "adapter_edge_receipt_incomplete")
                        row["down_edge_interval_ns"] = (
                            row["down"] if claimed_ordered else None)
                        row["up_edge_interval_ns"] = (
                            row["up"] if claimed_ordered else None)
                raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
            return subprocess.run(
                [sys.executable, str(copied_root / "audit_a01.py")],
                capture_output=True, text=True, check=False)

    def test_unmodified_saved_bundle_passes(self):
        result = self.run_auditor_in_copy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS_SAVED_RESULT_AUDIT", result.stdout)

    def test_swapped_classifications_fail_even_when_aggregate_is_preserved(self):
        result = self.run_auditor_in_copy(mutate=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ordering mismatch", result.stdout)
        self.assertIn('"paired": 15', result.stdout)
        self.assertIn('"incomplete": 85', result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
