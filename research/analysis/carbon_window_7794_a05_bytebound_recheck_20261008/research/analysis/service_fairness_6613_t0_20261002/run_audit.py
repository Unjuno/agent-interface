import json
import sys
from pathlib import Path

from audit import audit

ROOT = Path(__file__).resolve().parent
raw_path, out_path = (Path(value).resolve() for value in sys.argv[1:3])
if out_path.exists():
    raise SystemExit("STOP_OUTPUT_COLLISION")
public = json.loads((ROOT / "fixture_public.json").read_text(encoding="utf-8"))
oracle = json.loads((ROOT / "oracle_truth.json").read_text(encoding="utf-8"))
raw = json.loads(raw_path.read_text(encoding="utf-8"))
result = audit(public, oracle, raw)
out_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "rows": result["rows"],
                  "errors": result["errors"], "output": str(out_path)}, sort_keys=True))
sys.exit(0 if result["status"] == "METHOD_PASS_SCOPED" else 1)
