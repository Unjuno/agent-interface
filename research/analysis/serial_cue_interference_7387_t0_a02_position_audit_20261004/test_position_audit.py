from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from audit_positions import audit_presentation_schema, audit_rows


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "research/analysis/serial_cue_interference_7387_t0_20261004"
RAW = REPO_ROOT / "research/analysis/serial_cue_interference_7387_t0_20261004_a02/formal_01/output"
DESIGN = json.loads((SOURCE / "design.json").read_text(encoding="utf-8"))
ROWS = [
    json.loads(line)
    for line in (RAW / "isolated.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
PRESENTATION_ROWS = [
    json.loads(line)
    for line in (RAW / "presentations.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
FROZEN_AUDITOR_SPEC = importlib.util.spec_from_file_location(
    "frozen_serial_cue_auditor", SOURCE / "auditor.py"
)
FROZEN_AUDITOR = importlib.util.module_from_spec(FROZEN_AUDITOR_SPEC)
FROZEN_AUDITOR_SPEC.loader.exec_module(FROZEN_AUDITOR)
class PositionAuditTests(unittest.TestCase):
    def test_retained_a02_positions_match_token_bound_oracle(self):
        result = audit_rows(ROWS, DESIGN)
        self.assertEqual(result, {
            "ok": True,
            "errors": [],
            "position_rows": 16,
            "expected_rows": 16,
        })

    def test_retained_presentation_rows_have_exact_allowed_fields(self):
        result = audit_presentation_schema(PRESENTATION_ROWS, DESIGN)
        self.assertEqual(result, {
            "ok": True, "errors": [], "presentation_rows": 288, "expected_rows": 288,
        })

    def test_answer_bearing_presentation_field_is_rejected(self):
        mutated = copy.deepcopy(PRESENTATION_ROWS)
        mutated[0]["answer"] = "red_square"
        result = audit_presentation_schema(mutated, DESIGN)
        self.assertFalse(result["ok"])
        self.assertEqual(result["errors"], ["presentation-schema-mismatch"])

    def test_truncated_presentation_rows_are_rejected(self):
        result = audit_presentation_schema(PRESENTATION_ROWS[:-1], DESIGN)
        self.assertFalse(result["ok"])
        self.assertIn("presentation-denominator", result["errors"])

    def test_non_object_presentation_row_is_rejected(self):
        mutated = copy.deepcopy(PRESENTATION_ROWS)
        mutated[0] = ["token", "arm", "prompt", "source_indices", "frames"]
        result = audit_presentation_schema(mutated, DESIGN)
        self.assertFalse(result["ok"])
        self.assertIn("presentation-schema-mismatch", result["errors"])

    def test_non_object_isolated_row_is_rejected(self):
        mutated = copy.deepcopy(ROWS)
        mutated[0] = ["token", "position", "prompt", "source_indices", "frames"]
        result = audit_rows(mutated, DESIGN)
        self.assertFalse(result["ok"])
        self.assertIn("isolated-schema-mismatch", result["errors"])

    def test_cli_returns_nonzero_and_false_json_for_corrupted_position(self):
        with tempfile.TemporaryDirectory(prefix="7387-cli-audit-") as temp:
            isolated_path = Path(temp) / "isolated.jsonl"
            presentations_path = Path(temp) / "presentations.jsonl"
            mutated = copy.deepcopy(ROWS)
            mutated[0]["position"] = next(
                position for position in DESIGN["isolated_positions"]
                if position != mutated[0]["position"]
            )
            isolated_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in mutated),
                encoding="utf-8",
            )
            presentations_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in PRESENTATION_ROWS),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("audit_positions.py")),
                 "--design", str(SOURCE / "design.json"),
                 "--isolated", str(isolated_path),
                 "--presentations", str(presentations_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertFalse(result["ok"])
            self.assertIn("isolated-position-mismatch", result["position_audit"]["errors"])

    def test_cli_returns_nonzero_and_denominator_error_for_truncated_manifest(self):
        with tempfile.TemporaryDirectory(prefix="7387-cli-denominator-") as temp:
            isolated_path = Path(temp) / "isolated.jsonl"
            presentations_path = Path(temp) / "presentations.jsonl"
            isolated_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in ROWS),
                encoding="utf-8",
            )
            presentations_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in PRESENTATION_ROWS[:-1]),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("audit_positions.py")),
                 "--design", str(SOURCE / "design.json"),
                 "--isolated", str(isolated_path),
                 "--presentations", str(presentations_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertFalse(result["ok"])
            self.assertIn("presentation-denominator", result["presentation_schema_audit"]["errors"])

    def test_effective_wrong_position_mutation_is_rejected(self):
        mutated = copy.deepcopy(ROWS)
        old_position = mutated[0]["position"]
        alternatives = [p for p in DESIGN["isolated_positions"] if p != old_position]
        mutated[0]["position"] = alternatives[0]
        self.assertNotEqual(mutated[0]["position"], old_position)
        result = audit_rows(mutated, DESIGN)
        self.assertFalse(result["ok"])
        self.assertIn("isolated-position-mismatch", result["errors"])

    def test_missing_position_is_rejected(self):
        mutated = copy.deepcopy(ROWS)
        del mutated[0]["position"]
        result = audit_rows(mutated, DESIGN)
        self.assertFalse(result["ok"])
        self.assertIn("isolated-position-mismatch", result["errors"])

    def test_original_frozen_auditor_accepts_effective_position_mutation(self):
        with tempfile.TemporaryDirectory(prefix="7387-position-audit-") as temp:
            generated_output = Path(temp) / "generated-output"
            subprocess.run(
                ["python", "-B", str(SOURCE / "candidate.py"), "--out", str(generated_output)],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            generated_rows = [
                json.loads(line)
                for line in (generated_output / "isolated.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(generated_rows, ROWS)
            self.assertTrue(FROZEN_AUDITOR.audit_package(generated_output)["ok"])
            mutated_output = Path(temp) / "mutated-output"
            shutil.copytree(generated_output, mutated_output)
            isolated_path = mutated_output / "isolated.jsonl"
            rows = [json.loads(line) for line in isolated_path.read_text(encoding="utf-8").splitlines()]
            old_position = rows[0]["position"]
            rows[0]["position"] = next(
                position for position in DESIGN["isolated_positions"] if position != old_position
            )
            self.assertNotEqual(rows[0]["position"], old_position)
            isolated_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            refresh_checksums(mutated_output)
            original_result = FROZEN_AUDITOR.audit_package(mutated_output)
            self.assertTrue(original_result["ok"], original_result["errors"])
            self.assertFalse(audit_rows(rows, DESIGN)["ok"])

    def test_original_frozen_auditor_accepts_answer_field_in_presentation(self):
        with tempfile.TemporaryDirectory(prefix="7387-schema-audit-") as temp:
            generated_output = Path(temp) / "generated-output"
            subprocess.run(
                ["python", "-B", str(SOURCE / "candidate.py"), "--out", str(generated_output)],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            generated_rows = [
                json.loads(line)
                for line in (generated_output / "presentations.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(generated_rows, PRESENTATION_ROWS)
            mutated = copy.deepcopy(generated_rows)
            mutated[0]["answer"] = "red_square"
            (generated_output / "presentations.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in mutated),
                encoding="utf-8",
            )
            refresh_checksums(generated_output)
            original_result = FROZEN_AUDITOR.audit_package(generated_output)
            self.assertTrue(original_result["ok"], original_result["errors"])
            self.assertFalse(audit_presentation_schema(mutated, DESIGN)["ok"])


def refresh_checksums(output: Path) -> None:
    files = sorted(
        path for path in output.rglob("*")
        if path.is_file() and path.name not in {"SHA256SUMS", "audit.json"}
    )
    checksum_text = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
        f"{path.relative_to(output).as_posix()}\n"
        for path in files
    )
    (output / "SHA256SUMS").write_text(checksum_text, encoding="ascii")


if __name__ == "__main__":
    unittest.main()
