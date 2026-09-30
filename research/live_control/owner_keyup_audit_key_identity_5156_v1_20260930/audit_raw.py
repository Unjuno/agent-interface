"""Separate raw-only invocation for the frozen key-identity fixture."""
import json
from pathlib import Path
from audit_v3 import audit

ROOT = Path(__file__).parent

def main():
    expected = json.loads((ROOT / "expected_inventory.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "raw_input.json").read_text(encoding="utf-8"))
    errors = audit(expected, raw.get("records"))
    print(json.dumps({"status": "PASS" if not errors else "FAIL",
                      "record_count": len(raw.get("records", [])),
                      "errors": errors}, sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
