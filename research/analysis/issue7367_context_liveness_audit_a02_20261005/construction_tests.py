#!/usr/bin/env python3
"""Pre-freeze tests, including an audit-only CLI exercise on retained A01 bytes."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FROZEN_FILES = [
    "PROTOCOL.md", "RUN.md", "CONSTRUCTION.md", "PRE-RUN.json", "workload.json",
    "run_a01.py", "audit_a01.py", "A01_RAW.json", "A01_AUDIT_V1.json",
    "audit_a02.py", "test_workload_binding.py", "construction_tests.py",
    "CONSTRUCTION_REPRO.json", "construction_mutation/workload.json",
    "construction_mutation/RAW.json", "construction_mutation/AUDIT_V1.json",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    test = subprocess.run(
        [sys.executable, "-m", "unittest", "-v",
         "research.analysis.issue7367_context_liveness_audit_a02_20261005.test_workload_binding"],
        cwd=ROOT.parents[2], text=True, capture_output=True)
    sys.stdout.write(test.stdout)
    sys.stderr.write(test.stderr)
    if test.returncode:
        raise SystemExit(test.returncode)

    manifest = {
        "format": "issue7367-a02-construction-freeze-v1",
        "sha256": {name: sha(ROOT / name) for name in FROZEN_FILES},
    }
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        freeze = temp / "FREEZE.json"
        output = temp / "AUDIT_V2.json"
        freeze.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "audit_a02.py"), "--freeze", str(freeze), "--out", str(output)],
            cwd=ROOT, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            sys.stderr.write(result.stderr)
        if result.returncode:
            raise SystemExit("A02_CONSTRUCTION_AUDIT_FAILED:" + str(result.returncode))
        audit = json.loads(output.read_text(encoding="utf-8"))
        if audit.get("classification") != "PASS_AUDIT_BINDING_REVALIDATED":
            raise SystemExit("A02_CONSTRUCTION_CLASSIFICATION_MISMATCH")
        if audit["checks"].get("candidate_invocations") != 0:
            raise SystemExit("UNEXPECTED_CANDIDATE_INVOCATION")
    print("CONSTRUCTION_TESTS_PASS")


if __name__ == "__main__":
    main()
