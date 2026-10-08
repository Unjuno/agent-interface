"""Standalone independent audit entrypoint; only reads retained raw outputs."""

import json
import sys
from pathlib import Path

import audit_core

ROOT = Path(__file__).parent
raw = json.loads((ROOT / "results/candidate.raw.json").read_text())
errors = []
for row in raw["cases"]:
    errors.extend(f"{row['id']}:{e}" for e in audit_core.verify_case(row, ROOT / "results/db"))
result = {"status": "PASS" if not errors and len(raw["cases"]) == 6 else "FAIL", "case_count": len(raw["cases"]), "errors": errors}
(ROOT / "results/audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
sys.exit(0 if result["status"] == "PASS" else 1)
