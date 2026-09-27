"""Independent raw audit for the model-free runtime startup and clean finish."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
CASE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/"evidence/runtime-startup-smoke-v5/run-01"
result=json.loads((CASE/"runtime-startup-result.json").read_text())
events=[json.loads(line) for line in (CASE/"client/runtime/events.jsonl").read_text().splitlines() if line]
ready=[e for e in events if e.get("event")=="ready"]
observations=[e for e in events if e.get("event")=="observation"]
finish=[e for e in events if e.get("event")=="independent_evaluation"]
if result.get("status")!="PASS_RUNTIME_STARTUP_NO_MODEL" or result.get("host_model_calls")!=0 or result.get("host_broker_model_calls")!=0:
    raise SystemExit("FAIL_RUNTIME_SMOKE_RESULT")
if result.get("runtime_exit_code")!=0 or result.get("fixture_clean_finish") is not True or len(ready)!=1 or not observations or len(finish)!=1:
    raise SystemExit("FAIL_RUNTIME_SMOKE_LIFECYCLE")
if result.get("authority_granted") is not False or result.get("network")!="none":raise SystemExit("FAIL_RUNTIME_SMOKE_AUTHORITY")
if list((CASE/"client").glob("**/*.broker.json")):raise SystemExit("FAIL_RUNTIME_SMOKE_BROKER_ARTIFACT")
audit={"status":"PASS_RUNTIME_STARTUP_NO_MODEL","host_model_calls":0,"host_broker_model_calls":0,
    "runtime_exit_code":0,"ready_events":1,"observations":len(observations),"clean_finish_events":1,
    "authority_granted":False,"network":"none"}
(CASE.parent/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
print(json.dumps(audit,sort_keys=True))
