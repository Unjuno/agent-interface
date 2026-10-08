"""Append-only auditor correction for the retained one-shot #5730 run."""

import hashlib
import json
from pathlib import Path


BASE = "5ff239141f49c1603c0f6b078268f4a2f6e082df"
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit_values(root: Path):
    errors = []
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    run_raw = (root / "RUN.json").read_bytes()
    stdout = (root / "STDOUT.bin").read_bytes()
    stderr = (root / "STDERR.bin").read_bytes()
    execution = json.loads((root / "EXECUTION.json").read_text(encoding="utf-8"))
    run = json.loads(run_raw)
    if freeze.get("base_main") != BASE or run.get("base_main") != BASE:
        errors.append("base SHA mismatch")
    if run_raw != stdout or stderr:
        errors.append("retained stdout/stderr mismatch")
    if execution.get("exit_code") != 0 or execution.get("run_sha256") != sha(run_raw):
        errors.append("execution receipt mismatch")
    if execution.get("stdout_sha256") != sha(stdout) or execution.get("stderr_sha256") != sha(stderr):
        errors.append("stream digest mismatch")
    frozen_sources = freeze.get("sources", {})
    for name, expected_hash in frozen_sources.items():
        try:
            actual = sha((root / name).read_bytes())
        except OSError:
            actual = None
        if actual != expected_hash or run.get("source_sha256", {}).get(name) != expected_hash:
            errors.append(f"frozen source mismatch: {name}")
    rows = run.get("cases")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("case cardinality mismatch")
        rows = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("malformed case row")
            continue
        name = row.get("case")
        if name in seen or name not in EXPECTED:
            errors.append(f"duplicate or unexpected case: {name}")
            continue
        seen.add(name)
        status, calls = EXPECTED[name]
        result = row.get("outcome", {})
        if result.get("status") != status or result.get("candidate_invocations") != calls or row.get("candidate_calls") != calls:
            errors.append(f"case decision/count mismatch: {name}")
        if status != "ARTIFACT_PUBLISHED":
            if result.get("scientific_result") != "NOT_EVALUATED" or result.get("raw_sha256") is not None:
                errors.append(f"invalid case promoted to evidence: {name}")
        elif result.get("scientific_result") != "READY_FOR_INDEPENDENT_AUDIT":
            errors.append("valid case not ready for independent audit")
        if name == "postwrite_digest_mismatch":
            # This observed transient file is precisely the cleanup gap. It is
            # not a raw scientific digest, but must be reported, not hidden.
            if not row.get("published_artifact_sha256"):
                errors.append("postwrite mutation observation missing")
        elif status != "ARTIFACT_PUBLISHED" and row.get("published_artifact_sha256") is not None:
            errors.append(f"unexpected output-path residue: {name}")
        if name == "valid_success" and result.get("raw_sha256") != row.get("published_artifact_sha256"):
            errors.append("success artifact digest mismatch")
    if seen != set(EXPECTED):
        errors.append("case set mismatch")
    total = sum(item[1] for item in EXPECTED.values())
    if run.get("candidate_invocations") != total or execution.get("candidate_invocations") != total:
        errors.append("aggregate candidate count mismatch")

    cleanup_gap = any(
        row.get("case") == "postwrite_digest_mismatch"
        and row.get("outcome", {}).get("status") == "STOP_POSTWRITE_DIGEST_MISMATCH"
        and row.get("outcome", {}).get("raw_sha256") is None
        and row.get("published_artifact_sha256") is not None
        for row in rows
    )
    if errors:
        decision = "FAIL_AUDIT_INTEGRITY"
    elif cleanup_gap:
        decision = "FAIL_CONSTRUCTION_CLEANUP_GAP"
    else:
        decision = "PASS_CONSTRUCTION_ONLY"
    return {"auditor": "audit_v2.py separate raw-only process", "result": decision,
            "run_sha256": sha(run_raw), "source_hashes_match": not any("source mismatch" in e for e in errors),
            "cases": len(seen), "candidate_invocations": total, "errors": errors,
            "interpretation": "typed STOP and no scientific hash were correct; a tampered output-path file remained observable after STOP, so fail-closed publication cleanup is not demonstrated",
            "scope": "synthetic host-only protocol construction; no GPU/Docker/model/game/GUI/input evidence"}


if __name__ == "__main__":
    output = audit_values(Path(__file__).resolve().parent)
    raw = (json.dumps(output, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (Path(__file__).resolve().parent / "AUDIT_V2.json").write_bytes(raw)
    print(raw.decode("utf-8"), end="")
    raise SystemExit(0 if output["result"] == "PASS_CONSTRUCTION_ONLY" else 1)
