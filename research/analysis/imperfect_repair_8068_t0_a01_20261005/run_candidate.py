import json
from pathlib import Path

from repair_profile import enumerate_histories, summarize

out = Path(__file__).with_name("candidate_raw.json")
rows = enumerate_histories()
payload = {"rows": rows, "summary": summarize(rows)}
out.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"rows": len(rows), "operators": sorted(payload["summary"]), "output": out.name}, sort_keys=True))
