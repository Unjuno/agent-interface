import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
COMMON_GIT_DIR = subprocess.check_output(
    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    cwd=PACKAGE,
    text=True,
).strip()


class SavedResultAuditIntegrityTests(unittest.TestCase):
    def run_audit(self, mutate=None):
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp) / "package"
            shutil.copytree(PACKAGE, scratch, ignore=shutil.ignore_patterns("__pycache__"))
            result_path = scratch / "RESULT.json"
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if mutate:
                mutate(result)
                result_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            env = dict(os.environ)
            env["GIT_DIR"] = COMMON_GIT_DIR
            return subprocess.run(
                [sys.executable, "audit.py"],
                cwd=scratch,
                env=env,
                text=True,
                capture_output=True,
            )

    def test_accepts_unmodified_result(self):
        proc = self.run_audit()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS_INDEPENDENT_RAW_RECONSTRUCTION_SCOPED", proc.stdout)

    def test_rejects_corrupt_ack_gap_summary(self):
        proc = self.run_audit(
            lambda result: result["same_step_ack_gap_ms"].__setitem__("median", 9999.0)
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("FAIL_SAVED_RESULT_MISMATCH", proc.stdout)

    def test_rejects_corrupt_per_admission_ack_gap(self):
        proc = self.run_audit(
            lambda result: result["rows"][0].__setitem__("ack_gap_ns", 999999999999)
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("FAIL_SAVED_RESULT_MISMATCH", proc.stdout)

    def test_rejects_corrupt_admission_count(self):
        proc = self.run_audit(
            lambda result: result["counts"].__setitem__("admissions", 0)
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("FAIL_SAVED_RESULT_MISMATCH", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
