import json
from pathlib import Path

from model import execute

out = Path(__file__).resolve().parent / "raw.json"
result = execute()
out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"disposition": result["disposition"], "states": result["state_count"],
                  "pairs": result["pair_row_count"], "counterexamples": result["counterexample_count"]}, sort_keys=True))
