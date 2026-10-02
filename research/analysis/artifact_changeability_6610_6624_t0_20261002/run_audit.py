import json
import sys
from pathlib import Path

from audit import audit

here = Path(__file__).resolve().parent
raw_path, out_path = map(lambda p: Path(p).resolve(), sys.argv[1:3])
if out_path.exists():
    raise SystemExit("STOP_OUTPUT_COLLISION")
public = json.loads((here / "cases_public.json").read_text(encoding="utf-8"))
truth = json.loads((here / "oracle_truth.json").read_text(encoding="utf-8"))
costs = json.loads((here / "costs.json").read_text(encoding="utf-8"))
raw = json.loads(raw_path.read_text(encoding="utf-8"))
result = audit(public, truth, costs, raw)
out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
sys.exit(0 if result["status"] == "METHOD_PASS_SCOPED" else 1)
