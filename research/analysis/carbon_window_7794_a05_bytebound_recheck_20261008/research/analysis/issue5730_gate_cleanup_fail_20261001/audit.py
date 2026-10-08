"""Independent raw-only auditor; uses only the Python standard library."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "empty_inventory": ("STOP_INVENTORY_OUTPUT_EMPTY_OR_MISSING", 0),
    "inventory_command_failure": ("STOP_INVENTORY_COMMAND_FAILED", 0),
    "malformed_inventory": ("STOP_INVENTORY_OUTPUT_MALFORMED", 0),
    "inventory_schema_invalid": ("STOP_INVENTORY_SCHEMA_INVALID", 0),
    "incomplete_source_identity": ("STOP_SOURCE_IDENTITY_INCOMPLETE", 0),
    "changed_source_digest": ("STOP_SOURCE_IDENTITY_CHANGED", 0),
    "candidate_nonzero": ("STOP_CANDIDATE_NONZERO", 1),
    "candidate_output_absent": ("STOP_OUTPUT_MISSING_OR_TRUNCATED", 1),
    "candidate_json_truncated": ("STOP_OUTPUT_MISSING_OR_TRUNCATED", 1),
    "postwrite_digest_mismatch": ("STOP_POSTWRITE_DIGEST_MISMATCH", 1),
    "valid_success": ("ARTIFACT_PUBLISHED", 1),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit():
    errors = []
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    run_raw = (ROOT / "RUN.json").read_bytes()
    stdout = (ROOT / "STDOUT.bin").read_bytes()
    stderr = (ROOT / "STDERR.bin").read_bytes()
    execution = json.loads((ROOT / "EXECUTION.json").read_text(encoding="utf-8"))
    run = json.loads(run_raw)
    if freeze.get("base_main") != "5ff239141f49c1603c0f6b078268f4a2f6e082df":
        errors.append("base SHA mismatch")
    if run_raw != stdout:
        errors.append("stdout bytes differ from retained RUN.json")
    if stderr:
        errors.append("unexpected stderr bytes")
    if execution.get("exit_code") != 0 or execution.get("run_sha256") != sha(run_raw):
        errors.append("execution receipt mismatch")
    if execution.get("stdout_sha256") != sha(stdout) or execution.get("stderr_sha256") != sha(stderr):
        errors.append("stdout/stderr digest mismatch")
    if run.get("base_main") != freeze.get("base_main"):
        errors.append("run/freeze base mismatch")
    actual_hashes = {name: sha((ROOT / name).read_bytes()) for name in freeze.get("sources", {})}
    if actual_hashes != freeze.get("sources") or actual_hashes != run.get("source_sha256"):
        errors.append("frozen source digest mismatch")
    cases = run.get("cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED):
        errors.append("case cardinality mismatch")
        cases = []
    seen = set()
    for row in cases:
        if not isinstance(row, dict):
            errors.append("case row is not an object")
            continue
        name = row.get("case")
        if name in seen:
            errors.append(f"duplicate case: {name}")
            continue
        seen.add(name)
        if name not in EXPECTED:
            errors.append(f"unexpected case: {name}")
            continue
        expected_status, expected_calls = EXPECTED[name]
        outcome = row.get("outcome")
        if not isinstance(outcome, dict) or outcome.get("status") != expected_status:
            errors.append(f"{name}: status mismatch")
            continue
        if row.get("candidate_calls") != expected_calls or outcome.get("candidate_invocations") != expected_calls:
            errors.append(f"{name}: candidate invocation count mismatch")
        if expected_calls == 0 and (outcome.get("raw_sha256") is not None or outcome.get("scientific_result") != "NOT_EVALUATED"):
            errors.append(f"{name}: prerequisite STOP promoted to evidence")
        if expected_status != "ARTIFACT_PUBLISHED" and outcome.get("raw_sha256") is not None:
            errors.append(f"{name}: invalid output received a scientific raw hash")
        if expected_status != "ARTIFACT_PUBLISHED" and row.get("published_artifact_sha256") is not None:
            errors.append(f"{name}: invalid output published")
        if expected_status == "ARTIFACT_PUBLISHED":
            if outcome.get("scientific_result") != "READY_FOR_INDEPENDENT_AUDIT":
                errors.append("success: wrong scientific state")
            if outcome.get("raw_sha256") != row.get("published_artifact_sha256"):
                errors.append("success: published digest mismatch")
    if seen != set(EXPECTED):
        errors.append("expected case set mismatch")
    expected_total = sum(value[1] for value in EXPECTED.values())
    if run.get("candidate_invocations") != expected_total or execution.get("candidate_invocations") != expected_total:
        errors.append("aggregate invocation count mismatch")
    return {"auditor": "audit.py independent process", "result": "PASS" if not errors else "FAIL",
            "cases": len(EXPECTED), "candidate_invocations": expected_total,
            "run_sha256": sha(run_raw), "source_hashes_match": not any("source digest" in e for e in errors),
            "errors": errors,
            "scope": "synthetic host-only protocol construction; no GPU/Docker/model/game/GUI/input evidence"}


if __name__ == "__main__":
    result = audit()
    raw = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (ROOT / "AUDIT.json").write_bytes(raw)
    print(raw.decode("utf-8"), end="")
    raise SystemExit(0 if result["result"] == "PASS" else 1)
