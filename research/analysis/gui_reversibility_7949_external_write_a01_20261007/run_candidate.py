import json
from pathlib import Path

import candidate

ROOT = Path(__file__).parent
model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
print(json.dumps({"run_id": model["run_id"], "cases": candidate.run(model)}, sort_keys=True, indent=2))
