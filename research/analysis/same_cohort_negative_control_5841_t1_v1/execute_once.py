"""One candidate subprocess invocation after FREEZE.json is recorded."""
import json
from pathlib import Path

from candidate import evaluate

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
fixture = json.loads((ROOT / "fixture.json").read_text())
result = evaluate(fixture)
(RESULTS / "candidate.stdout.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": "CANDIDATE_COMPLETE", "case_count": len(result["cases"]),
                  "row_count": sum(len(case["rows"]) for case in result["cases"]),
                  "result": str(RESULTS / "candidate.stdout.json")}))
