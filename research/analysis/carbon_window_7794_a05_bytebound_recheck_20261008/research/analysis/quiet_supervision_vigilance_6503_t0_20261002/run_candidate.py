import json
from pathlib import Path
from candidate import build

root = Path(__file__).parent
fixture = json.loads((root / "fixture.json").read_text())
rows = build(fixture)
out = root / "results" / "t0-01"
out.mkdir(parents=True, exist_ok=True)
(out / "RAW.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "CONSTRUCTED", "rows": len(rows), "allocation": fixture["allocation"]}, sort_keys=True))
