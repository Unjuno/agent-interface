from pathlib import Path
import hashlib,json
def j(p,n):return json.loads((p/"run"/n).read_text(encoding="utf-8"))
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
p=Path(__file__).resolve().parent;c=json.loads((p/"conditions.json").read_text(encoding="utf-8"));obs=j(p,"observation-parsed.json");rep=obs["receipt"]["report"];close=j(p,"close-raw.txt")
ok=all(sha(p/n)==h for h,n in (line.split("  ",1) for line in (p/"FROZEN_SHA256SUMS").read_text(encoding="ascii").splitlines()))
a={"schema":"win32-standard-calculator-r13-audit-v1","attempt_id":c["attempt_id"],"frozen_manifest_matches":ok,"observation_status":rep["status"],"error":rep.get("error"),"input_dispatched":rep["input_dispatched"],"session_call_count":rep["session"]["call_count"],"baseline_display":j(p,"uia-baseline.json")["parsed"]["display_digits"],"close_status":close["status"],"close_session_state":close["session"]["state"],"unresolved_call_ids":close["session"]["unresolved_call_ids"],"dispatch_record_present":any("dispatch" in f.name for f in (p/"run").iterdir()),"disposition":"PRE_INPUT_STOP: oversized client capture; no input."}
assert ok and rep["status"]=="observation_failed" and not rep["input_dispatched"] and close["status"]=="closed"
(p/"run"/"audit.json").write_text(json.dumps(a,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(a,ensure_ascii=True,indent=2))
