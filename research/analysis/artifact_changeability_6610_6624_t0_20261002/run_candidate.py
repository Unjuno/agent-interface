import json
import sys
from pathlib import Path

from candidate import run

here = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
if out.exists():
    raise SystemExit("STOP_OUTPUT_COLLISION")
public = json.loads((here / "cases_public.json").read_text(encoding="utf-8"))
out.write_text(json.dumps(run(public["cases"]), indent=2, sort_keys=True) + "\n", encoding="utf-8")
