import json
import sys
from pathlib import Path

import audit_core

ROOT = Path(__file__).parent
raw = json.loads((ROOT / "results/candidate.raw.json").read_text())
result = audit_core.audit(raw)
(ROOT / "results/audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
sys.exit(0 if result["status"] == "PASS" else 1)
