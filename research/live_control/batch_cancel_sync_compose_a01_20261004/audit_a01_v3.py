"""Read-only A01 auditor that binds the retained trace before parsing it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_a01_v2 import audit as audit_v2

ROOT = Path(__file__).resolve().parent


def audit_trace(raw_bytes: bytes, freeze: dict, manifest: dict) -> list[str]:
    expected = freeze.get("raw_trace_sha256")
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if not isinstance(expected, str) or actual != expected:
        return ["raw_trace_hash_mismatch"]
    try:
        raw = json.loads(raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ["raw_trace_invalid_json"]
    return audit_v2(raw, manifest)


def main() -> None:
    freeze = json.loads(
        (ROOT / "AUDIT_REPAIR_V2_FREEZE.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8")
    )
    raw_bytes = (ROOT / "raw/trace.json").read_bytes()
    errors = audit_trace(raw_bytes, freeze, manifest)
    status = "PASS_SYNTHETIC_COMPOSITION" if not errors else "FAIL_AUDIT"
    print(json.dumps({"schema": "batch-cancel-sync-composition-a01-audit-v3",
                      "status": status, "case_count": 2, "errors": errors},
                     sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
