from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
c=json.loads((ROOT/"conditions.json").read_text(encoding="utf-8"))
r=json.loads((ROOT/"result.json").read_text(encoding="utf-8"))
t=json.loads((ROOT/"tool-receipts.json").read_text(encoding="utf-8"))
img=(ROOT/"raw/final-result.jpg").read_bytes()
checks={
 "attempt_id_matches": c["attempt_id"]==r["attempt_id"],
 "expected_value_frozen": c["action"]["expected_display"]=="42",
 "operation_and_final_readback_match": t["actions"][-1]["observed_final"]=="12 + 30 = 42" and "exact visible operation 12 + 30 = 42" in r["result"],
 "fresh_observation_after_each_click": all(a["fresh_screenshot"] for a in t["actions"]) and len(t["actions"])==7,
 "no_retry": t["retry_count"]==0 and r["retry_count"]==0,
 "final_screenshot_is_jpeg": img.startswith(bytes.fromhex("ffd8ff")),
 "limits_retained": any("key-up" in x for x in r["limits"]) and any("WSLc" in x for x in r["limits"]),
}
out={"schema":"win32-computer-use-smoke-s02-audit-v1","checks":checks,"passed":all(checks.values()),"final_screenshot_sha256":hashlib.sha256(img).hexdigest()}
(ROOT/"audit.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
print(json.dumps(out,indent=2,sort_keys=True))
if not out["passed"]: raise SystemExit(1)
