#!/usr/bin/env python3
"""Independent, finite reconstruction of Issue #3188 formal-02 raw output."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_RAW_SHA256 = "8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324"
EXPECTED_PREREG_SHA256 = "a03047ae51adc7ed1ba5d97b295a6bfe8607f0e34933e00cb00172eb27c791b8"
SOURCE_COMMIT = "eca4bcc1ee839b80442397e27f238c97d6dd6bb4"
EXPECTED_SOURCE_SHA256 = {
    "run.py": "e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822",
    "audit.py": "72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d",
}
FIELDS = [
    "physical_task_effect_endpoint",
    "task_effect_contract",
    "matched_arm",
    "arm_bound_audit",
    "terminal_integrity",
]
CONTROL_NAMES = {
    "missing_receipt",
    "stale_binding",
    "unknown_boundary",
    "cleanup_failure",
    "corrupt_recomputation",
}
SCHEMA = "map01-recovery-entry-gate-3008-v2"


class AuditError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact_bytes_for_frozen_digest(data: bytes, expected: str) -> tuple[bytes, str]:
    """Accept exact bytes, or prove CRLF checkout normalization yields the frozen blob."""
    digest = sha256(data)
    if digest == expected:
        return data, "exact"
    if b"\r\n" in data:
        normalized = data.replace(b"\r\n", b"\n")
        if sha256(normalized) == expected:
            return normalized, "crlf_checkout_normalized_to_frozen_blob"
    raise AuditError(f"raw digest mismatch: got {digest}, expected {expected}")


def verify_frozen_inputs(repo_root: Path) -> dict[str, str]:
    paths = {
        "raw.json": "research/integration/issue_3188_source_bound_entry_gate_v1/results/formal-02/raw.json",
        "PREREG-FORMAL-02.md": "research/integration/issue_3188_source_bound_entry_gate_v1/PREREG-FORMAL-02.md",
        "run.py": "research/analysis/map01_matched_recovery_entry_gate_3008_v2/run.py",
        "audit.py": "research/analysis/map01_matched_recovery_entry_gate_3008_v2/audit.py",
    }
    expected = {
        "raw.json": EXPECTED_RAW_SHA256,
        "PREREG-FORMAL-02.md": EXPECTED_PREREG_SHA256,
        **EXPECTED_SOURCE_SHA256,
    }
    modes: dict[str, str] = {}
    for label, relative in paths.items():
        _, mode = exact_bytes_for_frozen_digest((repo_root / relative).read_bytes(), expected[label])
        modes[label] = mode
    return modes


def reconstruct(raw_bytes: bytes, expected_sha256: str = EXPECTED_RAW_SHA256) -> dict[str, Any]:
    frozen_bytes, byte_mode = exact_bytes_for_frozen_digest(raw_bytes, expected_sha256)
    try:
        raw = json.loads(frozen_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"raw JSON parse failed: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise AuditError("schema mismatch")
    if raw.get("fields") != FIELDS:
        raise AuditError("field list/order mismatch")

    vectors = raw.get("vectors")
    if not isinstance(vectors, list) or len(vectors) != 32:
        raise AuditError("vector cardinality mismatch")
    expected_rows = list(itertools.product((False, True), repeat=len(FIELDS)))
    observed: list[tuple[bool, ...]] = []
    authorize = 0
    for index, (row, expected_bits) in enumerate(zip(vectors, expected_rows, strict=True)):
        if not isinstance(row, dict):
            raise AuditError(f"vector {index} is not an object")
        bits = tuple(row.get(field) for field in FIELDS)
        if any(type(bit) is not bool for bit in bits):
            raise AuditError(f"vector {index} contains a non-Boolean bit")
        if bits != expected_bits:
            raise AuditError(f"vector order/coverage mismatch at row {index}")
        expected_decision = "AUTHORIZE" if all(expected_bits) else "HOLD"
        if row.get("decision") != expected_decision:
            raise AuditError(f"decision mismatch at vector {index}")
        observed.append(bits)
        authorize += expected_decision == "AUTHORIZE"

    if len(set(observed)) != 32:
        raise AuditError("duplicate vector")
    controls = raw.get("controls")
    if not isinstance(controls, list) or len(controls) != 5:
        raise AuditError("negative-control cardinality mismatch")
    names: list[str] = []
    for control in controls:
        if not isinstance(control, dict):
            raise AuditError("negative control is not an object")
        name = control.get("name")
        if name not in CONTROL_NAMES:
            raise AuditError(f"unexpected control name: {name!r}")
        names.append(name)
        if control.get("decision") != "HOLD":
            raise AuditError(f"negative control admitted: {name}")
        if any(type(control.get(field)) is not bool for field in FIELDS):
            raise AuditError(f"negative control has non-Boolean field: {name}")
    if set(names) != CONTROL_NAMES or len(names) != len(set(names)):
        raise AuditError("negative-control names are missing or duplicated")
    if authorize != 1:
        raise AuditError(f"expected exactly one AUTHORIZE vector, got {authorize}")

    return {
        "status": "PASS_RAW_RECONSTRUCTION",
        "source_commit": SOURCE_COMMIT,
        "raw_sha256": expected_sha256,
        "input_byte_mode": byte_mode,
        "schema": SCHEMA,
        "vectors": 32,
        "unique_vectors": len(set(observed)),
        "authorize": authorize,
        "vector_hold": 32 - authorize,
        "negative_controls": len(controls),
        "negative_controls_hold": len(controls),
        "rows": len(vectors) + len(controls),
        "current_snapshot": "HOLD",
        "errors": [],
    }


def corruption_challenges(raw_bytes: bytes) -> dict[str, bool]:
    """Each challenge must be rejected while the external expected digest stays fixed."""
    frozen, _ = exact_bytes_for_frozen_digest(raw_bytes, EXPECTED_RAW_SHA256)
    original = json.loads(frozen)
    challenges: dict[str, bytes] = {}

    changed = json.loads(frozen)
    changed["vectors"][0][FIELDS[0]] = True
    challenges["vector_bit"] = json.dumps(changed, separators=(",", ":")).encode()
    changed = json.loads(frozen)
    changed["vectors"].pop()
    challenges["row_count"] = json.dumps(changed, separators=(",", ":")).encode()
    changed = json.loads(frozen)
    changed["vectors"][0]["decision"] = "AUTHORIZE"
    challenges["class_label"] = json.dumps(changed, separators=(",", ":")).encode()
    changed = json.loads(frozen)
    changed["controls"][0]["decision"] = "AUTHORIZE"
    challenges["control_admission"] = json.dumps(changed, separators=(",", ":")).encode()
    challenges["digest"] = frozen + b" "

    results: dict[str, bool] = {}
    for name, payload in challenges.items():
        try:
            reconstruct(payload, EXPECTED_RAW_SHA256)
        except AuditError:
            results[name] = True
        else:
            results[name] = False
    return results


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: audit_raw.py <repository-root> <output.json>", file=sys.stderr)
        return 2
    repo_root, output_path = map(Path, sys.argv[1:])
    raw_path = repo_root / "research/integration/issue_3188_source_bound_entry_gate_v1/results/formal-02/raw.json"
    raw_bytes = raw_path.read_bytes()
    try:
        result_modes = verify_frozen_inputs(repo_root)
        result = reconstruct(raw_bytes)
        result["frozen_input_byte_modes"] = result_modes
        result["corruption_controls_rejected"] = corruption_challenges(raw_bytes)
        if not all(result["corruption_controls_rejected"].values()):
            raise AuditError("one or more corruption challenges were accepted")
    except AuditError as exc:
        result = {"status": "FAIL_RAW_RECONSTRUCTION", "errors": [str(exc)]}
    encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    output_path.write_bytes(encoded)
    print(encoded.decode(), end="")
    return 0 if result["status"] == "PASS_RAW_RECONSTRUCTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
