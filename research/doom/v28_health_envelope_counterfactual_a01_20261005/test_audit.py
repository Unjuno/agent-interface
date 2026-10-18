"""Black-box corruption controls for the independent raw-only auditor."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
RAW = HERE / "outputs/a01/candidate-raw.json"
AUDITOR = HERE / "audit.py"


class AuditCorruptionTests(unittest.TestCase):
    def rejects(self, mutate, expected_error):
        raw = json.loads(RAW.read_text(encoding="utf-8"))
        mutate(raw)
        with tempfile.TemporaryDirectory(prefix="v28-a01-audit-corruption-") as temp:
            raw_path = Path(temp) / "mutated-raw.json"
            audit_path = Path(temp) / "audit.json"
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(AUDITOR), str(raw_path), str(audit_path)],
                cwd=HERE.parents[2], capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertIn(expected_error, completed.stderr)
            self.assertFalse(audit_path.exists(), "rejected input must not emit a PASS audit")

    def test_rejects_source_span_transcription_change(self):
        self.rejects(
            lambda raw: raw["spans"][0].__setitem__("trigger_health", 96),
            "raw span transcription mismatch",
        )

    def test_rejects_guard_outcome_change(self):
        self.rejects(
            lambda raw: raw["sweep"][0]["span_outcomes"][0].__setitem__(
                "effective_hard_floor", 99
            ),
            "sweep outcome mismatch",
        )

    def test_rejects_threshold_omission(self):
        self.rejects(lambda raw: raw["sweep"].pop(), "sweep outcome mismatch")


if __name__ == "__main__":
    unittest.main()
