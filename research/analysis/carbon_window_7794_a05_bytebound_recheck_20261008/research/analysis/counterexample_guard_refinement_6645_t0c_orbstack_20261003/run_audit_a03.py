import json
import sys
from pathlib import Path

from auditor import audit

fixture = json.loads(Path(sys.argv[1]).read_text())
raw = json.loads(Path(sys.argv[2]).read_text())
errors = []
if raw.get("allocation_id") != "CGREF-6645-T0C-ORB-20261003-03":
    errors.append("allocation_identity")
result = audit(fixture, raw)
result["errors"] = errors + result["errors"]
result["status"] = "PASS" if not result["errors"] else "FAIL"
Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS" else 1)
