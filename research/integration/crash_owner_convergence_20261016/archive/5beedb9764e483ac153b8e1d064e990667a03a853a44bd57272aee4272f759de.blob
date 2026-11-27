"""Raw-only audit for the opt-in process-owner integration contract run."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def audit():
    errors = []
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8-sig"))
    run = json.loads((HERE / "RUN.json").read_text(encoding="utf-8-sig"))
    for relative, expected in freeze["source_sha256"].items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing_source:{relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"source_hash_mismatch:{relative}")
    if run.get("schema") != "v39-v15-process-owner-integration-run-v1":
        errors.append("run_schema")
    for field in ("test_exit_code", "py_compile_exit_code", "diff_check_exit_code"):
        if run.get(field) != 0:
            errors.append(f"nonzero:{field}")
    test_output = (HERE / run["test_output"]).read_text(encoding="utf-8-sig")
    if "Ran 55 tests" not in test_output or "OK (skipped=2)" not in test_output:
        errors.append("test_output_does_not_match_frozen_disposition")
    compile_output = (HERE / run["py_compile_output"]).read_text(encoding="utf-8-sig")
    if compile_output.strip():
        errors.append("py_compile_output_not_empty")
    return {"schema": "v39-v15-process-owner-integration-audit-v1",
            "status": "PASS_STATIC_INTEGRATION_CONTRACT" if not errors else "FAIL",
            "checks": {"source_hashes": not any(e.startswith(("missing_source", "source_hash")) for e in errors),
                       "tests": run.get("test_exit_code") == 0,
                       "py_compile": run.get("py_compile_exit_code") == 0,
                       "diff_check": run.get("diff_check_exit_code") == 0,
                       "scope_limited": freeze.get("scope", "").startswith("Static/unit")},
            "errors": errors}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
