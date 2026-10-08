import json
from pathlib import Path
from auditor import audit

root = Path(__file__).parent
fixture = json.loads((root / "fixture.json").read_text())
truth = json.loads((root / "truth.json").read_text())
rows = json.loads((root / "results" / "t0-01" / "RAW.json").read_text())
result = audit(fixture, truth, rows)
out = root / "results" / "t0-01" / "AUDIT.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
if result["status"] != "PASS_METHOD_SCOPED":
    raise SystemExit(1)
