import json
from pathlib import Path

import candidate

root = Path(__file__).parent
model = json.loads((root / "model.json").read_text(encoding="utf-8"))
result = {
    "run_id": "gui-reversibility-7949-t0-a01-20261005",
    "model_id": model["model_id"],
    "candidate": "candidate.py",
    "cases": candidate.run(model),
}
serialized = json.dumps(result, sort_keys=True, indent=2) + "\n"
(root / "raw" / "candidate.stdout.json").write_text(serialized, encoding="utf-8")
print(serialized, end="")
