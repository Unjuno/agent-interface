"""Mutation controls for the independent terminal-release matrix auditor."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
AUDIT = HERE / "audit.py"
RAW = HERE / "RAW.json"


class AuditMutationTests(unittest.TestCase):
    def _run_mutation(self, mutate) -> subprocess.CompletedProcess:
        raw = json.loads(RAW.read_text(encoding="utf-8"))
        mutate(raw)
        with tempfile.TemporaryDirectory() as directory:
            raw_path = Path(directory) / "mutated.json"
            audit_path = Path(directory) / "audit.json"
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(AUDIT), str(raw_path), str(audit_path)],
                cwd=HERE,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_acceptance_mutation_is_rejected(self):
        def mutate(raw):
            row = next(
                row for row in raw["rows"]
                if row["status_case"] == "failed"
                and row["release_case"] == "source_owner_release"
            )
            row["observed"] = "accepted"

        result = self._run_mutation(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL_COMPOSITION_MATRIX", result.stdout)

    def test_duplicate_cell_is_rejected(self):
        def mutate(raw):
            raw["rows"][-1] = raw["rows"][0]

        result = self._run_mutation(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate or unknown matrix key", result.stderr)


if __name__ == "__main__":
    unittest.main()
