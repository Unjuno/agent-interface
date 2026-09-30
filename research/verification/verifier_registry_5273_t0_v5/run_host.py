"""Single host-only frozen decision-precedence construction run."""

import json
from pathlib import Path

from audit import audit
from candidate import preflight

HERE = Path(__file__).resolve().parent
cases = json.loads((HERE / "cases.json").read_text())
rows = []
for case in cases:
    result = preflight(case["ir"], case["assignments"], case["registry_snapshot"], case["resources"])
    rows.append({**case, "observed": result})
raw = {"schema": "verifier_registry_raw.v5", "rows": rows}
(HERE / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
result = audit(raw, cases)
(HERE / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
