import json
from pathlib import Path
from candidate import run, canonical_sha

here = Path(__file__).resolve().parent
result = run()
(here / "candidate_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "rows": len(result["rows"]), "sha256": canonical_sha(result)}, sort_keys=True))
