#!/usr/bin/env python3
"""Run the frozen Issue #3188 audit-v3 unittest suite from pinned bytes."""
from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import io
import json
import pathlib
import unittest
from typing import Any

BASE = pathlib.Path("research/integration/issue_3188_source_bound_entry_gate_v1/audit_v3_control_hardening_v1")
TESTS = pathlib.Path("research/integration/issue_3188_source_bound_entry_gate_v1/audit_v3_control_hardening_v1/test_audit_v3.py")
AUDITOR = pathlib.Path("research/integration/issue_3188_source_bound_entry_gate_v1/audit_v3_control_hardening_v1/independent_audit_v3.py")
RAW = pathlib.Path("research/integration/issue_3188_source_bound_entry_gate_v1/results/formal-02/raw.json")
RUN = pathlib.Path("research/analysis/map01_matched_recovery_entry_gate_3008_v2/run.py")
CANDIDATE_AUDIT = pathlib.Path("research/analysis/map01_matched_recovery_entry_gate_3008_v2/audit.py")


class FrozenBytesLoader:
    def __init__(self, payload: bytes):
        self.payload = payload

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        exec(compile(self.payload, module.__spec__.origin or module.__name__, "exec"), module.__dict__)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run_once(repo_root: pathlib.Path, freeze: dict[str, Any], payloads: dict[str, bytes]):
    expected = {
        "runner": freeze["runner"]["sha256"],
        "protocol": freeze["protocol_sha256"],
        "auditor": freeze["auditor_sha256"],
        "tests": freeze["tests_sha256"],
        "raw": freeze["frozen_inputs"]["raw"],
        "run": freeze["frozen_inputs"]["run"],
        "candidate_audit": freeze["frozen_inputs"]["candidate_audit"],
    }
    actual = {name: sha256(payloads[name]) for name in expected}
    mismatches = [name for name, digest in expected.items() if actual[name] != digest]
    if mismatches:
        return {
            "status": "STOP_FROZEN_INPUT_HASH_MISMATCH",
            "mismatches": mismatches,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "tests_run": 0,
        }

    test_path = repo_root / TESTS
    auditor_path = repo_root / AUDITOR
    frozen_modules = {
        "test_audit_v3": payloads["tests"],
        "independent_audit_v3": payloads["auditor"],
    }
    original_spec = importlib.util.spec_from_file_location

    def frozen_spec(name, location, *args, **kwargs):
        if name in frozen_modules:
            spec = importlib.machinery.ModuleSpec(
                name, FrozenBytesLoader(frozen_modules[name]), origin=str(location)
            )
            spec.has_location = True
            return spec
        return original_spec(name, location, *args, **kwargs)

    importlib.util.spec_from_file_location = frozen_spec
    try:
        spec = importlib.machinery.ModuleSpec(
            "test_audit_v3", FrozenBytesLoader(payloads["tests"]), origin=str(test_path)
        )
        spec.has_location = True
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    finally:
        importlib.util.spec_from_file_location = original_spec

    raw_after = sha256(payloads["raw"])
    status = (
        "PASS_AUDIT_V3_CONTROLS_SCOPED"
        if result.wasSuccessful() and result.testsRun == 5 and raw_after == expected["raw"]
        else "FAIL_AUDIT_V3"
    )
    return {
        "status": status,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "test_output": output.getvalue(),
        "raw_sha256_before": expected["raw"],
        "raw_sha256_after": raw_after,
        "source_sha256": actual,
        "docker_validation": "NOT_RUN_DAEMON_UNAVAILABLE",
    }
