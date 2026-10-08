"""One separate invocation of the pinned completeness-only v2 auditor."""
import hashlib
import json
from pathlib import Path

from audit_v2 import audit


ROOT = Path(__file__).parent
RESULTS = ROOT / "results" / "construction-01"


def main():
    expected = json.loads((ROOT / "expected_inventory.json").read_text(encoding="utf-8"))
    raw_path = RESULTS / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    if raw.get("schema") != "owner-keyup-audit-interop-raw-v1":
        errors.append("raw_schema_invalid")
    records = raw.get("records")
    errors.extend(audit(expected, records))
    result = {
        "auditor": "PR-5415-audit_v2.py-verbatim",
        "auditor_scope": "release identity, owner interval, inventory cardinality, non-authority flags",
        "caller_nesting_audited_here": False,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "record_count": len(records) if isinstance(records, list) else None,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    (RESULTS / "AUDIT.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
