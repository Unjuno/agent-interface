"""Independent result-ledger integrity checks for Issue #4665."""

from __future__ import annotations

import hashlib
from pathlib import Path


INPUTS = {
    "audit_freeze": ("audit_freeze.json", "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/FREEZE.json", "2d9b0e4ee289bad1402e5e6fe58f4734a788becd56d5e783dda1816518fbaf94"),
    "audit_plan": ("audit_plan.md", "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/PLAN.md", "79741322f5c4b43d7d6a5a7b847bf3505bf94d2bc2f486ff27e40592515dd795"),
    "audit_source": ("audit_source.py", "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/audit.py", "ca3ccf5191d876eeda824555589c4580537dc04ec771fc52ef8914300ec289be"),
    "audit_result": ("audit_result.json", "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/result/RESULT.json", "4bb36c596ee85a48f79c21b18ae4dd6a08b09b7e6e72d351e89bb1188196ae54"),
    "formal_freeze": ("formal_freeze.json", "research/integration/issue_3711_downstream_truncation_v1/successor-02/FREEZE.json", "b7b2d2bebd24bfc54abc4a20bb00da452eafb084ed09fa7b2a2c57ad146658cd"),
    "formal_raw": ("formal_raw.json", "research/integration/issue_3711_downstream_truncation_v1/formal-02/raw.json", "3f51dc5a4c9c8acb48fc2929a8219260575271e5794cd5bd4afedf6f712afc73"),
    "accepted": ("accepted.json", "research/integration/issue_3711_downstream_truncation_v1/formal-02/accepted.json", "e8ef9f6dd897325a22b1927d27e7fba2948051bb309cc472bbf2a1bfaba863d1"),
    "delivered_prefix": ("delivered_prefix.bin", "research/integration/issue_3711_downstream_truncation_v1/formal-02/delivered-prefix.bin", "0450145d98f8ff197766d91827a438db1aa5800d556b4bee24eb57b33e168d4a"),
    "audit_v1_result": ("audit_v1.json", "research/integration/issue_3711_downstream_truncation_v1/formal-02/audit.json", "69454ea54a9c3b6b91ca6331645e4b0a7dc071cd9da4abb9b88bff7888afa7ca"),
    "audit_v2_01_failure": ("audit_v2_01_result.json", "research/integration/issue_3711_downstream_truncation_v1/audit-v2/formal-02-recheck/RESULT.json", "faeed58dc95b32ffc29add42f4e860ac5049db654b790d903b6ee3cb48931315"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive_input_ledger(input_dir: Path) -> tuple[dict, list[str]]:
    """Derive role/path/hash entries only from immutable input bytes."""
    ledger = {}
    errors = []
    for role, (filename, repo_path, expected_sha) in INPUTS.items():
        try:
            actual = sha256((input_dir / filename).read_bytes())
        except OSError:
            errors.append(f"INPUT_MISSING:{role}")
            continue
        ledger[role] = {"path": repo_path, "sha256": actual}
        if actual != expected_sha:
            errors.append(f"INPUT_SHA256_MISMATCH:{role}")
    return ledger, errors


def audit_result_ledger(result: dict, actual_ledger: dict) -> list[str]:
    """Bind every reported ledger row to independently derived input bytes."""
    errors = []
    reported = result.get("input_sha256") if isinstance(result, dict) else None
    expected_roles = set(INPUTS)
    if not isinstance(reported, dict):
        return ["RESULT_INPUT_LEDGER_NOT_OBJECT"]
    if set(reported) != expected_roles:
        errors.append("RESULT_INPUT_LEDGER_ROLE_SET_MISMATCH")
    if set(actual_ledger) != expected_roles:
        errors.append("ACTUAL_INPUT_LEDGER_ROLE_SET_MISMATCH")
    for role in sorted(expected_roles & set(reported) & set(actual_ledger)):
        row = reported[role]
        actual = actual_ledger[role]
        if not isinstance(row, dict):
            errors.append(f"RESULT_INPUT_LEDGER_ROW_NOT_OBJECT:{role}")
            continue
        if row.get("path") != actual["path"]:
            errors.append(f"RESULT_INPUT_LEDGER_PATH_MISMATCH:{role}")
        if row.get("sha256") != actual["sha256"]:
            errors.append(f"RESULT_INPUT_LEDGER_SHA256_MISMATCH:{role}")
    return errors


def audit(input_dir: Path, result: dict) -> dict:
    ledger, input_errors = derive_input_ledger(input_dir)
    errors = input_errors + audit_result_ledger(result, ledger)
    return {
        "schema": "issue4649-result-ledger-audit-v1",
        "decision": "PASS_RESULT_LEDGER_BINDING_SCOPED" if not errors else "FAIL_RESULT_LEDGER_BINDING",
        "input_count": len(ledger),
        "actual_input_sha256": ledger,
        "errors": errors,
    }
