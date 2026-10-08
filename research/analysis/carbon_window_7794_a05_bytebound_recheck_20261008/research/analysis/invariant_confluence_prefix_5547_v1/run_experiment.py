import json
from pathlib import Path

from experiment import execute

out = Path(__file__).resolve().parent / "raw.json"
result = execute()
out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"output": out.name, "disposition": result["disposition"],
                  "pairs": result["ordered_pair_count"]}, sort_keys=True))
