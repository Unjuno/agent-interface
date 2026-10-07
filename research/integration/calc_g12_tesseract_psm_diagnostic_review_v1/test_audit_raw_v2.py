from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from audit_raw_v2 import PACKAGE, audit_record


class AuditRawV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((PACKAGE / "RAW.json").read_text(encoding="utf-8"))
        cls.image = (PACKAGE / "input-c2.png").read_bytes()

    def test_retained_raw_passes(self):
        result = audit_record(copy.deepcopy(self.raw), self.image)
        self.assertEqual(result["disposition"], "PASS_RAW_INTEGRITY_SCOPED")
        self.assertEqual(result["exact_match_modes"], [6, 7, 8, 10, 13])

    def test_each_non_psm_argument_is_bound(self):
        # argv[4] is the one intentionally varying field; all other positions are fixed.
        for position in (0, 1, 2, 3, 5, 6, 7, 8):
            with self.subTest(position=position):
                raw = copy.deepcopy(self.raw)
                for row in raw["attempts"]:
                    row["argv"][position] = f"tampered-{position}"
                self.assertIn("exact argv", " ".join(audit_record(raw, self.image)["errors"]))

    def test_fixed_option_metadata_is_bound(self):
        for key, value in (("language", "fra"), ("character_whitelist", "")):
            with self.subTest(key=key):
                raw = copy.deepcopy(self.raw)
                raw["fixed_options"][key] = value
                self.assertIn(key.replace("character_whitelist", "character whitelist"),
                              " ".join(audit_record(raw, self.image)["errors"]))

    def test_tampered_scratch_record_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["attempts"][1]["stdout"] = "951\n"
        self.assertEqual(audit_record(raw, self.image)["disposition"], "FAIL_RAW_INTEGRITY")

    def test_default_cli_is_read_only_and_matches_retained_audit(self):
        retained_path = PACKAGE / "AUDIT.json"
        before = retained_path.read_bytes()
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("audit_raw_v2.py")), "--compare-retained"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(retained_path.read_bytes(), before)

    def test_explicit_output_never_overwrites(self):
        script = Path(__file__).with_name("audit_raw_v2.py")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "audit.json"
            result = subprocess.run([sys.executable, str(script), "--write-audit", str(output)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(output.is_file())
            before = output.read_bytes()
            again = subprocess.run([sys.executable, str(script), "--write-audit", str(output)],
                                   capture_output=True, text=True, check=False)
            self.assertEqual(again.returncode, 1)
            self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
