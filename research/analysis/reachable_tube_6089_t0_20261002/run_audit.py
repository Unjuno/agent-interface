import json
import sys
from pathlib import Path

from audit import audit


HERE = Path(__file__).resolve().parent
cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
raw_path = Path(sys.argv[1]).resolve()
output_path = Path(sys.argv[2]).resolve()
if output_path.exists():
    raise SystemExit("STOP_OUTPUT_COLLISION")
records = json.loads(raw_path.read_text(encoding="utf-8"))
result = audit(cases, records)
output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
sys.exit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
