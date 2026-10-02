import json
import sys
from pathlib import Path

from candidate import run

HERE = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
if out.exists():
    raise SystemExit("STOP_OUTPUT_COLLISION")
cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
out.write_text(json.dumps(run(cases), indent=2, sort_keys=True) + "\n", encoding="utf-8")
