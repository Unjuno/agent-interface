"""Independent stdlib-only auditor for the published synthetic raw bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def audit(raw_path: Path, receipt_path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        raw_bytes = raw_path.read_bytes()
    except OSError:
        return ("raw_unreadable",)
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ("receipt_unreadable",)
    if not isinstance(receipt, dict):
        return ("receipt_shape",)
    if receipt.get("schema") != "gpu-diagnostic-receipt-v1":
        errors.append("receipt_schema")
    if receipt.get("candidate_exit_code") != 0:
        errors.append("candidate_exit")
    actual_sha = hashlib.sha256(raw_bytes).hexdigest()
    if receipt.get("raw_sha256") != actual_sha:
        errors.append("raw_digest")
    try:
        raw = json.loads(raw_bytes)
    except (UnicodeError, json.JSONDecodeError):
        errors.append("raw_json")
        raw = None
    if not isinstance(raw, dict) or raw.get("schema") != "gpu-diagnostic-raw-v1":
        errors.append("raw_schema")
    elif raw.get("complete") is not True or not isinstance(raw.get("rows"), list):
        errors.append("raw_incomplete")
    if receipt.get("status") != "CANDIDATE_ARTIFACT_VALID":
        errors.append("receipt_status")
    return tuple(errors)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(json.dumps({"errors": ["usage"]}, sort_keys=True, separators=(",", ":")))
        return 2
    errors = audit(Path(args[0]), Path(args[1]))
    print(json.dumps({"errors": list(errors)}, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

