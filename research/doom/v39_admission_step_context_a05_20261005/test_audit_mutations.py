"""Mutation regressions for RESULT fields the independent auditor must check."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE / "audit.py"
RESULT = HERE / "RESULT.json"


def mutated_result(mutator):
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    mutator(result)
    return result


def reject_mutation(result):
    with tempfile.TemporaryDirectory() as temp:
        temp_path = Path(temp)
        (temp_path / "RESULT.json").write_text(json.dumps(result), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(AUDIT), "--result", str(temp_path / "RESULT.json"), "--check-only"],
            cwd=HERE, capture_output=True, text=True, check=False,
        )
    return completed.returncode, completed.stdout + completed.stderr


class AuditMutationTests(unittest.TestCase):
    def test_rejects_mutated_ack_gap_summary_median(self):
        result = mutated_result(lambda d: d["same_step_ack_gap_ms"].update(median=9999))
        code, output = reject_mutation(result)
        self.assertNotEqual(code, 0, output)

    def test_rejects_mutated_row_ack_gap(self):
        result = mutated_result(lambda d: d["rows"][0].update(ack_gap_ns=999999999999))
        code, output = reject_mutation(result)
        self.assertNotEqual(code, 0, output)

    def test_rejects_mutated_association(self):
        result = mutated_result(lambda d: d["rows"][0].update(association="NO_SAME_STEP_AGGREGATE_ACK"))
        code, output = reject_mutation(result)
        self.assertNotEqual(code, 0, output)

    def test_rejects_negative_row_ack_gap(self):
        result = mutated_result(lambda d: d["rows"][0].update(ack_gap_ns=-1))
        code, output = reject_mutation(result)
        self.assertNotEqual(code, 0, output)

    def test_rejects_mutated_admission_count(self):
        result = mutated_result(lambda d: d["counts"].update(admissions=0))
        code, output = reject_mutation(result)
        self.assertNotEqual(code, 0, output)

    def test_rejects_boolean_alias_for_step_number(self):
        result = mutated_result(lambda d: d["rows"][0]["step_context"].update(step=True))
        code, output = reject_mutation(result)
        self.assertNotEqual(code, 0, output)


if __name__ == "__main__":
    unittest.main()
