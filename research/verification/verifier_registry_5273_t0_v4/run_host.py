"""One-shot host construction run; no dispatch, GUI, model, or container."""

import json
from pathlib import Path

from candidate import preflight
from audit import audit

HERE = Path(__file__).resolve().parent
cases = json.loads((HERE / "cases.json").read_text())
rows = []
for case in cases:
    observed = preflight(case["ir"], case["assignments"], case["registry_snapshot"], case["resources"])
    rows.append({**case, "observed": observed})
(HERE / "RAW.json").write_text(json.dumps({"schema": "verifier_registry_raw.v4", "rows": rows}, indent=2, sort_keys=True) + "\n")
result = audit({"schema": "verifier_registry_raw.v4", "rows": rows}, cases)
(HERE / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "RUN_COMPLETE_HOST_ONLY", **result}))
