import json
import subprocess
import sys
import tempfile
import os
import unittest
from pathlib import Path


HERE = Path(__file__).parent


def sample(decision="ACCEPT", emitted=False, order=True, missed=0):
    values = {
        "sample": 1, "scheduled_ns": 100, "sample_started_ns": 100,
        "capture_ns": 110, "typed_ready_ns": 120,
        "sample_finished_ns": 130, "frame_sha256": "a" * 64, "epoch": 1,
        "missed_periods_before": missed, "decision": decision,
        "input_emitted": emitted,
    }
    if not order:
        values["typed_ready_ns"] = 90
    return values


class AuditTest(unittest.TestCase):
    def run_audit(self, rows):
        handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        try:
            handle.write("\n".join(json.dumps(row) for row in rows))
            handle.close()
            return subprocess.run(
                [sys.executable, str(HERE / "audit.py"), handle.name],
                text=True, capture_output=True,
            )
        finally:
            os.unlink(handle.name)

    def test_valid_row_and_explicit_missed_period_pass(self):
        result = self.run_audit([sample(missed=2)])
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_timestamp_order_is_required(self):
        self.assertNotEqual(self.run_audit([sample(order=False)]).returncode, 0)

    def test_rejected_row_cannot_emit_input(self):
        self.assertNotEqual(self.run_audit([sample("REJECT", emitted=True)]).returncode, 0)

    def test_sample_sequence_must_increase(self):
        self.assertNotEqual(self.run_audit([sample(), sample()]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
