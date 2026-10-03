import json
import sys
from pathlib import Path

from candidate import run

fixture = json.loads(Path(sys.argv[1]).read_text())
out = run(fixture)
out["allocation_id"] = "CGREF-6645-T0C-ORB-20261003-03"
Path(sys.argv[2]).write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({"allocation_id": out["allocation_id"], "rows": len(out["rows"]),
                  "alternatives": out["refinement_alternatives"]}, sort_keys=True))
