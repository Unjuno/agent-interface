#!/usr/bin/env python3
"""Run the frozen candidate audit against isolated corruption-control directories."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.environ.get("OUTPUT_DIR", "/tmp/golden-v3-audit-output"))
CANDIDATE = ROOT / "research/integration/golden_v3_schema_reconciliation_2198_v1/audit.py"
SCHEMA = ROOT / "research/integration/golden_v3_result_schema_2186_v1/schema.json"
REPORT = ROOT / "runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def has_file_reads(source: str) -> bool:
    tree = ast.parse(source)
    names = {"open", "read_text", "read_bytes", "loads", "load", "Path", "read"}
    return any(isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id in names) or (isinstance(node.func, ast.Attribute) and node.func.attr in names)) for node in ast.walk(tree))


def run_candidate(schema: bytes | None, report: bytes | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="golden-v3-control-") as tmp:
        directory = Path(tmp)
        if schema is not None:
            (directory / "schema.json").write_bytes(schema)
        if report is not None:
            (directory / "report.json").write_bytes(report)
        proc = subprocess.run([sys.executable, str(CANDIDATE)], cwd=directory, text=True, capture_output=True, check=False)
        return {"exit_code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    candidate_bytes, schema_bytes, report_bytes = CANDIDATE.read_bytes(), SCHEMA.read_bytes(), REPORT.read_bytes()
    schema_obj, report_obj = json.loads(schema_bytes), json.loads(report_bytes)
    cases: dict[str, tuple[bytes | None, bytes | None]] = {
        "unaltered": (schema_bytes, report_bytes),
        "missing_both": (None, None),
        "renamed_required_field": (schema_bytes, json.dumps({**report_obj, "task_success_renamed": report_obj.get("passed")}, sort_keys=True).encode()),
        "prose_only_field_claim": (schema_bytes, b'{"note":"task_success and lifecycle are present in documentation"}'),
        "synthetic_schema_v1_report": (schema_bytes, json.dumps({"schema":"golden-v3-result-v1","program_completed":True,"task_success":True,"authority_granted":False,"status":"success","partial_effects":[],"cleanup_error":None,"lifecycle":[],"usage":{}}, sort_keys=True).encode()),
        "mutated_schema_value": (schema_bytes, json.dumps({**report_obj, "schema":"golden-v3-result-v1"}, sort_keys=True).encode()),
    }
    outputs = {name: run_candidate(*files) for name, files in cases.items()}
    independent = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "independent_audit.py")], cwd=ROOT, text=True, capture_output=True, check=False)
    independent_result = json.loads(independent.stdout) if independent.returncode == 0 else {"error": independent.stderr}
    summary = {
        "experiment": "golden_v3_existing_audit_input_binding_v1",
        "source_commit": os.environ.get("SOURCE_COMMIT", "recorded-in-plan; git not installed in minimal image"),
        "candidate_audit_sha256": sha(candidate_bytes),
        "schema_sha256": sha(schema_bytes),
        "report_sha256": sha(report_bytes),
        "candidate_audit_has_file_reads_by_ast": has_file_reads(candidate_bytes.decode("utf-8")),
        "controls": outputs,
        "all_candidate_outputs_identical": len({json.dumps(value, sort_keys=True) for value in outputs.values()}) == 1,
        "independent_audit_exit_code": independent.returncode,
        "independent_audit": independent_result,
        "candidate_disposition": "FAIL_AUDITOR_INPUT_BINDING_SCOPED" if not has_file_reads(candidate_bytes.decode("utf-8")) or len({json.dumps(value, sort_keys=True) for value in outputs.values()}) == 1 else "PASS_AUDITOR_INPUT_BINDING_SCOPED",
        "schema_reconciliation_disposition": independent_result.get("disposition", "HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE"),
        "environment": {"python": sys.version, "platform": sys.platform, "container": os.environ.get("CONTAINER", "Docker Desktop; isolated python:3.12-slim container"), "docker_image": "python:3.12-slim"},
    }
    serialized = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    (OUT / "RESULT.json").write_text(serialized, encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if independent.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
