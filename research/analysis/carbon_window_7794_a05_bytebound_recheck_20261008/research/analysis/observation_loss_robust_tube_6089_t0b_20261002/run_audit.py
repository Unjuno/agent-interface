import json
import sys
from pathlib import Path

from audit import audit

HERE = Path(__file__).resolve().parent
raw = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
if out.exists():
    raise SystemExit("STOP_OUTPUT_COLLISION")
cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
result = audit(cases, json.loads(raw.read_text(encoding="utf-8")))
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
sys.exit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
