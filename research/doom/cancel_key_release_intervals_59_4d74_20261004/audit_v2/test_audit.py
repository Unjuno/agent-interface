import json
from pathlib import Path
import subprocess
import sys
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
AUDIT = HERE / "audit.py"


class ManifestAuditV2Tests(unittest.TestCase):
    def test_reconciles_tracked_manifest_without_generated_bytecode(self):
        run = subprocess.run(
            [sys.executable, "-B", str(AUDIT)],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertTrue(result["pass"])
        self.assertEqual(result["manifest_entries"], 20)
        self.assertEqual(result["verified_tracked_entries"], 17)
        self.assertEqual(
            result["unmanifested_tracked_files"], ["AUDIT.json", "FILES.sha256"]
        )
        self.assertEqual(
            result["missing_generated_bytecode"],
            [
                "baseline/__pycache__/executor_v3.cpython-314.pyc",
                "baseline/__pycache__/input_owner_v12.cpython-314.pyc",
                "baseline/__pycache__/lease.cpython-314.pyc",
            ],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
