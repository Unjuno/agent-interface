import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import audit


class AuditorExitContractTests(unittest.TestCase):
    def test_main_returns_zero_for_duplicate_boundary_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = pathlib.Path(directory) / "raw.json"
            out = pathlib.Path(directory) / "audit.json"
            raw.write_text(json.dumps({"schema": "7748-duplicate-id-a01-raw-v1", "rows": []}), encoding="utf-8")
            expected = {"status": "PASS_DUPLICATE_ID_BOUNDARY_SCOPED", "errors": [], "case_count": 0}
            with patch.object(audit, "audit", return_value=expected), patch(
                "sys.argv", ["audit.py", "--raw", str(raw), "--output", str(out)]
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(audit.main(), 0)

    def test_main_returns_nonzero_for_audit_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = pathlib.Path(directory) / "raw.json"
            out = pathlib.Path(directory) / "audit.json"
            raw.write_text("{}", encoding="utf-8")
            failed = {"status": "FAIL_AUDIT", "errors": ["schema"], "case_count": 0}
            with patch.object(audit, "audit", return_value=failed), patch(
                "sys.argv", ["audit.py", "--raw", str(raw), "--output", str(out)]
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(audit.main(), 1)


if __name__ == "__main__":
    unittest.main()
