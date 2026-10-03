import json
import sys
from pathlib import Path

from auditor import audit

fixture = json.loads(Path(sys.argv[1]).read_text())
raw = json.loads(Path(sys.argv[2]).read_text())
result = audit(fixture, raw)
Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS" else 1)
