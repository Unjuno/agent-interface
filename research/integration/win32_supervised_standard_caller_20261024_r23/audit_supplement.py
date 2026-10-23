from pathlib import Path
import json
p=Path(__file__).resolve().parent
a=json.loads((p/"audit.json").read_text(encoding="utf-8"))
assert a["status"] in ("PASS_SCOPED","FAIL_OR_UNKNOWN")
(p/"audit_supplement.json").write_text(json.dumps({"schema":"win32-supervised-standard-caller-r23-summary-v1","attempt_id":a["attempt_id"],"status":a["status"],"passed":a["passed"],"total":a["total"],"raw_sha256":a["raw_sha256"]},indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"status":a["status"],"passed":a["passed"],"total":a["total"]},sort_keys=True))
