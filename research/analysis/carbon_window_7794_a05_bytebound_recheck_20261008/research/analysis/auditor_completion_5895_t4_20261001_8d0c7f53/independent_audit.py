"""Independent raw-only audit of the registered #5895 T4 candidate bundle."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ALLOCATION = "AUDIT-COMPLETION-5895-T4-ORBSTACK-20261001-01-8d0c7f53"
CASE_ORDER = ["control", "bool_false", "float_zero", "null", "string_zero",
              "missing_code", "duplicate_success", "success_plus_failure"]
EXPECTED_EXIT = dict(zip(CASE_ORDER, [0, 0, 0, 1, 1, 1, 1, 0]))
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
FROZEN = {
    "audit_formal_x11.py": ("da805fb83f70a57ad68a0768186e214524689d40",
                            "f74da3f66fa979db99c17213df31d295056b99ae04c8d8b59bd6d5b5d71a93e0"),
    "EXPECTED.json": ("3d33bda096c4c8789e183e3f864ee7626e643a7e",
                      "7bf403b88773ecdfd04243f023c17e26e859c3286b71ccf5eb2db3101e0ef076"),
    "test_audit_formal_x11.py": ("d1eb9a854cc810fa77ca173d7e2de287ee1bd64a",
                                 "1fbb4b86fec10ad8ed578efa476df1857d38e82617d802ff8e0252ff848163f5"),
}
RUNNER_SHA256 = "59981d7bd7574389e20755d1e131e379b5b64ce929da66f6e971484255a56738"
MATRIX_SHA256 = "ffc2ce99a2605b08a6de5f989e8fda3a42af4e8db1915be4e547e7f23fce5162"


def completion_exit(rows: list[dict]) -> int:
    """Independent transcription of the registered equality/cardinality predicate."""
    selected = [row for row in rows if row.get("event") == "runner_complete" and row.get("exit_code") == 0]
    return 0 if len(selected) == 1 else 1


def expected_completion_rows(case_id: str) -> list[dict]:
    import copy
    return copy.deepcopy(EXPECTED_COMPLETIONS[case_id])


def completion_rows_match(case_id: str, rows: list[dict]) -> bool:
    if case_id not in EXPECTED_COMPLETIONS:
        return False
    expected = EXPECTED_COMPLETIONS[case_id]
    if len(rows) != len(expected):
        return False
    for actual_row, expected_row in zip(rows, expected):
        if actual_row.keys() != expected_row.keys():
            return False
        for key, expected_value in expected_row.items():
            actual_value = actual_row[key]
            if key == "exit_code" and type(actual_value) is not type(expected_value):
                return False
            if actual_value != expected_value:
                return False
    return True


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frozen_noncompletion(target: Path) -> list[dict]:
    fixture_path = target / "test_audit_formal_x11.py"
    spec = importlib.util.spec_from_file_location("frozen_t4_fixture", fixture_path)
    if spec is None or spec.loader is None:
        raise OSError("cannot load frozen fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [row for row in module.fixture_rows() if row.get("event") != "runner_complete"]


def audit_bundle(manifest_path: str | Path, target_dir: str | Path) -> list[str]:
    manifest_file = Path(manifest_path).resolve(strict=True)
    root = manifest_file.parent.resolve(strict=True)
    target = Path(target_dir).resolve(strict=True)
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        expected_bytes = (target / "EXPECTED.json").read_bytes()
        expected = json.loads(expected_bytes)
        baseline_noncompletion = _frozen_noncompletion(target)
    except (OSError, json.JSONDecodeError, ValueError, AttributeError) as exc:
        return [f"frozen input unavailable or malformed: {type(exc).__name__}"]

    if manifest.get("allocation") != ALLOCATION:
        errors.append("allocation identity mismatch")
    if manifest.get("disposition") != "CANDIDATE_EXPECTED":
        errors.append("candidate disposition is not expected")
    if manifest.get("runner_sha256") != RUNNER_SHA256:
        errors.append("candidate runner digest mismatch")
    if manifest.get("matrix_sha256") != MATRIX_SHA256:
        errors.append("candidate matrix digest mismatch")
    if manifest.get("expected_sha256") != hashlib.sha256(expected_bytes).hexdigest():
        errors.append("expected fixture digest mismatch")
    for name, (blob, digest) in FROZEN.items():
        try:
            actual = _sha(target / name)
        except OSError:
            errors.append(f"frozen source missing: {name}")
            continue
        if actual != digest or manifest.get({
                "audit_formal_x11.py": "target_sha256",
                "EXPECTED.json": "expected_sha256",
                "test_audit_formal_x11.py": "fixture_sha256",
        }[name]) != digest:
            errors.append(f"frozen source digest mismatch: {name}")
        if manifest.get({
                "audit_formal_x11.py": "target_git_blob",
                "EXPECTED.json": "expected_git_blob",
                "test_audit_formal_x11.py": "fixture_git_blob",
        }[name]) != blob:
            errors.append(f"frozen Git blob mismatch: {name}")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or [c.get("case_id") for c in cases if isinstance(c, dict)] != CASE_ORDER:
        errors.append("case inventory/order mismatch")
        cases = cases if isinstance(cases, list) else []
    control_noncompletion = None
    for case in cases:
        if not isinstance(case, dict):
            errors.append("case manifest entry is not an object")
            continue
        case_id = case.get("case_id")
        if case_id not in EXPECTED_EXIT:
            errors.append(f"unknown case {case_id!r}")
            continue
        relative = {
            "raw": f"{case_id}/raw.jsonl", "audit": f"{case_id}/audit.json",
            "stdout": f"{case_id}/stdout.txt", "stderr": f"{case_id}/stderr.txt",
        }
        for key, expected_path in relative.items():
            if case.get(f"{key}_path") != expected_path:
                errors.append(f"{case_id}: {key} path mismatch")
        paths = {key: root / name for key, name in relative.items()}
        if any(path.is_symlink() or not path.resolve().is_relative_to(root) for path in paths.values()):
            errors.append(f"{case_id}: artifact escapes result root")
            continue
        try:
            raw_bytes, audit_bytes = paths["raw"].read_bytes(), paths["audit"].read_bytes()
            stdout_bytes, stderr_bytes = paths["stdout"].read_bytes(), paths["stderr"].read_bytes()
            rows = [json.loads(line) for line in raw_bytes.splitlines() if line]
            audit, stdout_audit = json.loads(audit_bytes), json.loads(stdout_bytes)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{case_id}: artifact unavailable/invalid: {type(exc).__name__}")
            continue
        for key, data in (("raw", raw_bytes), ("audit", audit_bytes), ("stdout", stdout_bytes),
                          ("stderr", stderr_bytes)):
            if hashlib.sha256(data).hexdigest() != case.get(f"{key}_sha256"):
                errors.append(f"{case_id}: {key} digest mismatch")
        if stderr_bytes:
            errors.append(f"{case_id}: unexpected stderr")
        if stdout_audit != audit:
            errors.append(f"{case_id}: stdout/audit disagree")
        if raw_bytes.count(b"\n") != len(rows):
            errors.append(f"{case_id}: raw JSONL line framing mismatch")
        expected_exit = EXPECTED_EXIT[case_id]
        if type(case.get("expected_exit")) is not int or case.get("expected_exit") != expected_exit:
            errors.append(f"{case_id}: candidate expected exit mismatch")
        if type(case.get("actual_exit")) is not int or case.get("actual_exit") != expected_exit:
            errors.append(f"{case_id}: target actual exit mismatch")
        completions = [row for row in rows if row.get("event") == "runner_complete"]
        if not completion_rows_match(case_id, completions):
            errors.append(f"{case_id}: completion mutation differs from frozen table")
        noncompletion = [row for row in rows if row.get("event") != "runner_complete"]
        if noncompletion != baseline_noncompletion:
            errors.append(f"{case_id}: baseline non-completion rows changed")
        fixtures = [row for row in noncompletion if row.get("event") == "fixture"]
        if len(fixtures) != 1 or fixtures[0].get("synthetic_only") is not True \
                or fixtures[0].get("evidence_mode") != "synthetic-cli" \
                or fixtures[0].get("allocation") != expected.get("allocation") \
                or fixtures[0].get("frozen_main") != expected.get("frozen_main"):
            errors.append(f"{case_id}: frozen synthetic fixture identity mismatch")
        expected_status = "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY" if expected_exit == 0 else "FAIL_AUDIT"
        if audit.get("status") != expected_status:
            errors.append(f"{case_id}: target status/error shape mismatch")
        if expected_exit == 0 and audit.get("errors") != []:
            errors.append(f"{case_id}: expected target success contains errors")
        if expected_exit == 1 and (not isinstance(audit.get("errors"), list) or not audit["errors"]):
            errors.append(f"{case_id}: expected target failure lacks errors")
        if audit.get("raw_sha256") != case.get("raw_sha256") or audit.get("raw_rows") != len(rows):
            errors.append(f"{case_id}: target raw binding mismatch")
        if audit.get("expected_sha256") != manifest.get("expected_sha256"):
            errors.append(f"{case_id}: target expected-source binding mismatch")
        if audit.get("allocation") != expected.get("allocation"):
            errors.append(f"{case_id}: target fixture allocation mismatch")
        if audit.get("host_launch_receipt_sha256") is not None \
                or audit.get("host_launch_receipt_authenticated") is not False \
                or audit.get("host_launch_receipt_bindings_valid") is not False \
                or "no X server" not in audit.get("scope", ""):
            errors.append(f"{case_id}: synthetic scope boundary mismatch")
        if case_id == "control":
            control_noncompletion = noncompletion
        elif control_noncompletion is not None and noncompletion != control_noncompletion:
            errors.append(f"{case_id}: control baseline differs")

    expected_files = {"candidate_manifest.json"}
    for case_id in CASE_ORDER:
        expected_files.update({f"{case_id}/raw.jsonl", f"{case_id}/audit.json",
                              f"{case_id}/stdout.txt", f"{case_id}/stderr.txt"})
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual_files != expected_files:
        errors.append("result artifact inventory mismatch")
    if any(path.is_symlink() for path in root.rglob("*")):
        errors.append("result tree contains symlink")
    return errors


def main(manifest_path: str, target_dir: str) -> int:
    errors = audit_bundle(manifest_path, target_dir)
    print(json.dumps({"status": "PASS_INDEPENDENT_RAW_AUDIT" if not errors else "FAIL_INDEPENDENT_RAW_AUDIT",
                      "errors": errors, "allocation": ALLOCATION, "cases": len(CASE_ORDER)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: independent_audit.py CANDIDATE_MANIFEST.json FROZEN_TARGET_DIR")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
