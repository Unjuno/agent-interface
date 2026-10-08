import json
import sys
from pathlib import Path

from candidate import run

fixture = json.loads(Path(sys.argv[1]).read_text())
out = run(fixture)
Path(sys.argv[2]).write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({"rows": len(out["rows"]), "alternatives": out["refinement_alternatives"],
                  "invalidated": out["cache_invalidation"]}, sort_keys=True))
