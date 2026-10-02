"""Independent receipt/raw check for Issue #5895 T6."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path


CASE_ORDER = [
    "control", "bool_false", "float_zero", "null", "string_zero",
    "missing_code", "duplicate_success", "success_plus_failure",
]
EXPECTED_EXIT = {
    "control": 0,
    "bool_false": 0,
    "float_zero": 0,
    "null": 1,
    "string_zero": 1,
    "missing_code": 1,
    "duplicate_success": 1,
    "success_plus_failure": 0,
}
EXPECTED_COMPLETIONS = {
    "control": [{"event": "runner_complete", "exit_code": 0}],
    "bool_false": [{"event": "runner_complete", "exit_code": False}],
    "float_zero": [{"event": "runner_complete", "exit_code": 0.0}],
    "null": [{"event": "runner_complete", "exit_code": None}],
    "string_zero": [{"event": "runner_complete", "exit_code": "0"}],
    "missing_code": [{"event": "runner_complete"}],
    "duplicate_success": [{"event": "runner_complete", "exit_code": 0},
                          {"event": "runner_complete", "exit_code": 0}],
    "success_plus_failure": [{"event": "runner_complete", "exit_code": 0},
                             {"event": "runner_complete", "exit_code": 1}],
}


def completion_filter_accepts(records: list[dict]) -> bool:
    """Independent transcription of the frozen target's completion predicate."""
    successful = [
        row for row in records
        if row.get("event") == "runner_complete" and row.get("exit_code") == 0
    ]
    return len(successful) == 1


def expected_completion_rows(case_id: str) -> list[dict]:
    """Return a fresh copy of the literal preregistered completion records."""
    import copy
    return copy.deepcopy(EXPECTED_COMPLETIONS[case_id])


def fixture_identity_matches(fixture: dict, expected: dict) -> bool:
    return (fixture.get("allocation") == expected.get("allocation")
            and fixture.get("frozen_main") == expected.get("frozen_main"))


def frozen_noncompletion_rows(target_path: str) -> list[dict]:
    """Load the pinned fixture builder only; never call the target audit function."""
    import importlib
    import os
    import sys

    target = Path(target_path).resolve(strict=True)
    target_text = str(target)
    prior_cwd = Path.cwd()
    sys.path.insert(0, target_text)
    try:
        os.chdir(target)
        module = importlib.import_module("test_audit_formal_x11")
        return [row for row in module.fixture_rows() if row.get("event") != "runner_complete"]
    finally:
        os.chdir(prior_cwd)
        if sys.path and sys.path[0] == target_text:
            sys.path.pop(0)


def main(manifest_path: str, target_path: str) -> int:
    manifest_file = Path(manifest_path)
    root = manifest_file.parent
    target = Path(target_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    errors: list[str] = []
    frozen = {
        "audit_formal_x11.py": ("da805fb83f70a57ad68a0768186e214524689d40",
                                "f74da3f66fa979db99c17213df31d295056b99ae04c8d8b59bd6d5b5d71a93e0"),
        "EXPECTED.json": ("3d33bda096c4c8789e183e3f864ee7626e643a7e",
                          "7bf403b88773ecdfd04243f023c17e26e859c3286b71ccf5eb2db3101e0ef076"),
        "test_audit_formal_x11.py": ("d1eb9a854cc810fa77ca173d7e2de287ee1bd64a",
                                     "1fbb4b86fec10ad8ed578efa476df1857d38e82617d802ff8e0252ff848163f5"),
    }
    try:
        expected_bytes = (target / "EXPECTED.json").read_bytes()
        expected = json.loads(expected_bytes)
    except (OSError, json.JSONDecodeError):
        expected_bytes = b""
        expected = {}
        errors.append("frozen expected fixture is unreadable/invalid")
    if expected_bytes and hashlib.sha256(expected_bytes).hexdigest() != manifest.get("expected_sha256"):
        errors.append("manifest expected fixture digest mismatch")
    try:
        baseline_noncompletion = frozen_noncompletion_rows(str(target))
    except (OSError, ImportError, AttributeError, json.JSONDecodeError):
        baseline_noncompletion = None
        errors.append("frozen fixture reconstruction failed")
    if manifest.get("allocation") != "AUDIT-COMPLETION-5895-T6-AMD64-20261001-01-8d0c7f53":
        errors.append("allocation identity mismatch")
    if manifest.get("disposition") != "CANDIDATE_EXPECTED":
        errors.append("candidate disposition is not the preregistered expected state")
    for name, (blob, digest) in frozen.items():
        try:
            source_bytes = (target / name).read_bytes()
            actual = hashlib.sha256(source_bytes).hexdigest()
            if actual != digest:
                errors.append(f"frozen source SHA-256 mismatch: {name}")
            recorded_field = {"audit_formal_x11.py": "target_sha256", "EXPECTED.json": "expected_sha256",
                              "test_audit_formal_x11.py": "fixture_sha256"}[name]
            if manifest.get(recorded_field) != digest:
                errors.append(f"manifest source SHA-256 mismatch: {name}")
            blob_field = {"audit_formal_x11.py": "target_git_blob", "EXPECTED.json": "expected_git_blob",
                          "test_audit_formal_x11.py": "fixture_git_blob"}[name]
            if manifest.get(blob_field) != blob:
                errors.append(f"manifest source Git blob mismatch: {name}")
        except OSError:
            errors.append(f"frozen source missing: {name}")
    cases = manifest.get("cases")
    if (not isinstance(cases, list) or any(not isinstance(c, dict) for c in cases)
            or [c.get("case_id") for c in cases] != CASE_ORDER):
        errors.append("case inventory/order mismatch")
        cases = cases if isinstance(cases, list) else []
    control_noncompletion = None
    for case in cases:
        case_id = case.get("case_id")
        if case_id not in EXPECTED_EXIT:
            errors.append(f"unknown case {case_id!r}")
            continue
        if case.get("raw_path") != f"{case_id}/raw.jsonl" or case.get("audit_path") != f"{case_id}/audit.json":
            errors.append(f"{case_id}: artifact path mismatch")
            continue
        if case.get("stdout_path") != f"{case_id}/stdout.txt" or case.get("stderr_path") != f"{case_id}/stderr.txt":
            errors.append(f"{case_id}: log path mismatch")
            continue
        raw_path = root / case["raw_path"]
        audit_path = root / case["audit_path"]
        stdout_path = root / case["stdout_path"]
        stderr_path = root / case["stderr_path"]
        paths = (raw_path, audit_path, stdout_path, stderr_path)
        if any(path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) for path in paths):
            errors.append(f"{case_id}: artifact escapes result directory")
            continue
        try:
            raw_bytes = raw_path.read_bytes()
            audit_bytes = audit_path.read_bytes()
            stdout_bytes = stdout_path.read_bytes()
            stderr_bytes = stderr_path.read_bytes()
            rows = [json.loads(line) for line in raw_bytes.splitlines() if line]
            audit = json.loads(audit_bytes)
            stdout_audit = json.loads(stdout_bytes)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{case_id}: artifact unreadable/invalid: {type(exc).__name__}")
            continue
        if raw_bytes.count(b"\n") != len(rows):
            errors.append(f"{case_id}: raw JSONL has unterminated or blank records")
        if hashlib.sha256(raw_bytes).hexdigest() != case.get("raw_sha256"):
            errors.append(f"{case_id}: raw artifact digest mismatch")
        if hashlib.sha256(audit_bytes).hexdigest() != case.get("audit_sha256"):
            errors.append(f"{case_id}: audit artifact digest mismatch")
        if hashlib.sha256(stdout_bytes).hexdigest() != case.get("stdout_sha256"):
            errors.append(f"{case_id}: stdout digest mismatch")
        if hashlib.sha256(stderr_bytes).hexdigest() != case.get("stderr_sha256"):
            errors.append(f"{case_id}: stderr digest mismatch")
        if stderr_bytes:
            errors.append(f"{case_id}: unexpected stderr")
        if stdout_audit != audit:
            errors.append(f"{case_id}: stdout/audit artifact disagreement")
        if not isinstance(case.get("actual_exit"), int) or type(case.get("actual_exit")) is not int:
            errors.append(f"{case_id}: actual exit is not an integer")
        elif case["actual_exit"] != EXPECTED_EXIT[case_id]:
            errors.append(f"{case_id}: target exit mismatch")
        if type(case.get("expected_exit")) is not int or case.get("expected_exit") != EXPECTED_EXIT[case_id]:
            errors.append(f"{case_id}: candidate expected exit mismatch")
        if audit.get("raw_sha256") != case.get("raw_sha256"):
            errors.append(f"{case_id}: target raw digest mismatch")
        if audit.get("raw_sha256") is None:
            errors.append(f"{case_id}: target raw digest missing")
        if audit.get("raw_rows") != len(rows):
            errors.append(f"{case_id}: target row count mismatch")
        if audit.get("expected_sha256") != manifest.get("expected_sha256"):
            errors.append(f"{case_id}: expected-input digest mismatch")
        if audit.get("allocation") != expected.get("allocation"):
            errors.append(f"{case_id}: target allocation mismatch")
        if not isinstance(audit.get("errors"), list):
            errors.append(f"{case_id}: target errors field is not a list")
        fixtures = [row for row in rows if row.get("event") == "fixture"]
        if (len(fixtures) != 1 or fixtures[0].get("synthetic_only") is not True
                or fixtures[0].get("evidence_mode") != "synthetic-cli"
                or not fixture_identity_matches(fixtures[0], expected)):
            errors.append(f"{case_id}: synthetic fixture identity mismatch")
        if (audit.get("host_launch_receipt_sha256") is not None
                or audit.get("host_launch_receipt_authenticated") is not False
                or audit.get("host_launch_receipt_bindings_valid") is not False
                or audit.get("scope", "").find("no X server") < 0):
            errors.append(f"{case_id}: synthetic scope/authority boundary mismatch")
        success = completion_filter_accepts(rows)
        completion_rows = [row for row in rows if row.get("event") == "runner_complete"]
        if completion_rows != expected_completion_rows(case_id):
            errors.append(f"{case_id}: completion mutation differs from preregistration")
        expected_success = EXPECTED_EXIT[case_id] == 0
        if success != expected_success:
            errors.append(f"{case_id}: independent completion oracle mismatch")
        expected_status = "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY" if expected_success else "FAIL_AUDIT"
        if audit.get("status") != expected_status:
            errors.append(f"{case_id}: target status mismatch")
        if expected_success != (not audit.get("errors")):
            errors.append(f"{case_id}: target errors/status disagree")
        noncompletion = [row for row in rows if row.get("event") != "runner_complete"]
        if baseline_noncompletion is not None and noncompletion != baseline_noncompletion:
            errors.append(f"{case_id}: non-completion fixture differs from frozen source")
        if case_id == "control":
            control_noncompletion = noncompletion
        elif control_noncompletion is not None and noncompletion != control_noncompletion:
            errors.append(f"{case_id}: non-completion evidence changed")
    expected_files = {"candidate_manifest.json"}
    for case_id in CASE_ORDER:
        expected_files.update({f"{case_id}/raw.jsonl", f"{case_id}/audit.json",
                               f"{case_id}/stdout.txt", f"{case_id}/stderr.txt"})
    try:
        actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
        if actual_files != expected_files:
            errors.append("result file inventory mismatch")
        if any(path.is_symlink() for path in root.rglob("*")):
            errors.append("result tree contains a symlink")
    except OSError:
        errors.append("result file inventory could not be read")
    print(json.dumps({"status": "PASS_INDEPENDENT_RAW_AUDIT" if not errors else "FAIL_INDEPENDENT_RAW_AUDIT",
                      "errors": errors, "cases": len(cases)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: independent_audit.py CANDIDATE_MANIFEST.json FROZEN_TARGET_DIR")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
