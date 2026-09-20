"""Independent raw-only audit for the model-free runner image wiring smoke."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CASE=Path(sys.argv[1]).resolve()/"run-01" if len(sys.argv)>1 else HERE/"evidence/runner-smoke-v1/run-01"
from sys import path
path.insert(0,str(ROOT/"research/live_control"))
from plain_form_points_v1 import validate
ipc=CASE/"ipc";reqs=list(ipc.glob("*.request.json"));rsps=list(ipc.glob("*.response.jsonl"));receipts=list(ipc.glob("*.broker.json"))
if not(len(reqs)==len(rsps)==len(receipts)==1):raise SystemExit("FAIL_SMOKE_CARDINALITY")
req=json.loads(reqs[0].read_text());receipt=json.loads(receipts[0].read_text());raw=rsps[0].read_bytes()
rows=[json.loads(line) for line in raw.splitlines()];messages=[r["item"] for r in rows if r.get("type")=="item.completed" and r.get("item",{}).get("type")=="agent_message"]
errors=[r["item"] for r in rows if r.get("type")=="item.completed" and r.get("item",{}).get("type")=="error"]
turns=[r for r in rows if r.get("type")=="turn.completed"]
if req.get("mode")!="handle" or req.get("image") is not None or req.get("authority_granted") is not False:raise SystemExit("FAIL_SMOKE_REQUEST")
if len(messages)!=1 or len(errors)!=1 or len(turns)!=1 or not turns[0].get("usage"):raise SystemExit("FAIL_SMOKE_EVENTS")
validate(json.loads(messages[0]["text"]))
if receipt.get("host_cli_invoked") is not False or receipt.get("authority_granted") is not False:raise SystemExit("FAIL_SMOKE_FAKE_RECEIPT")
command=json.loads((CASE/"command.json").read_text())
image="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
if image not in command:raise SystemExit("FAIL_SMOKE_IMAGE_BINDING")
result={"status":"PASS_RUNNER_COMMAND_SMOKE","host_model_calls":0,"host_broker_model_calls":0,"fake_ipc_requests":1,"assistant_messages":1,"auxiliary_errors":1,"schema_valid":True,"image":command[-12],"response_sha256":hashlib.sha256(raw).hexdigest()}
(CASE.parent/"independent-audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
