from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit_raw", HERE / "audit_raw.py")
assert spec and spec.loader
audit_raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_raw)


class CleanupReceiptTests(unittest.TestCase):
    def test_cleanup_receipt_requires_present_inside_absent_after(self):
        valid = {
            "copy_exists_inside_scope": True,
            "copy_exists_after_scope": False,
            "copy_removed_after_scope": True,
        }
        self.assertEqual(audit_raw.cleanup_errors(valid, "case"), [])

    def test_pre_context_observation_is_not_cleanup_evidence(self):
        false_receipt = {
            "copy_exists_inside_scope": True,
            "copy_exists_after_scope": True,
            "copy_removed_after_scope": False,
        }
        self.assertEqual(audit_raw.cleanup_errors(false_receipt, "case"), ["cleanup case"])

    def test_missing_post_scope_observation_is_rejected(self):
        incomplete = {"copy_exists_inside_scope": True}
        self.assertTrue(audit_raw.cleanup_errors(incomplete, "case"))

    def test_actual_temporary_directory_lifetime(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "evidence"
            copy.mkdir()
            self.assertTrue(copy.exists())
            inside = copy.exists()
        after = copy.exists()
        self.assertEqual(audit_raw.cleanup_errors({
            "copy_exists_inside_scope": inside,
            "copy_exists_after_scope": after,
            "copy_removed_after_scope": not after,
        }, "actual"), [])


if __name__ == "__main__":
    unittest.main()
