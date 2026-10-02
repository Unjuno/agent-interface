import json
import sys
from pathlib import Path

from candidate import run


HERE = Path(__file__).resolve().parent
cases_path = HERE / "cases.json"
output_path = Path(sys.argv[1]).resolve()
if output_path.exists():
    raise SystemExit("STOP_OUTPUT_COLLISION")
cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
output_path.write_text(json.dumps(run(cases), indent=2, sort_keys=True) + "\n", encoding="utf-8")
