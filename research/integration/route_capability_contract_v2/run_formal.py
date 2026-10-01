#!/usr/bin/env python3
import json
from pathlib import Path
from selector import catalog,choose
root=Path(__file__).resolve().parent; sent=root/".formal-invoked"
if sent.exists(): raise SystemExit("formal allocation already invoked")
sent.write_text("1\n"); cat=catalog(root); matrix=json.loads((root/"requests.json").read_text()); rows=[]
for q in matrix["requests"]: rows.append({"request_id":q["id"],"required_dimensions":q["required_dimensions"],"allowed_routes":q["allowed_routes"],"baseline":choose(q,cat,"flat"),"candidate":choose(q,cat,"dim")})
out={"schema":"route-capability-formal-result-v1","formal_invocations":1,"catalog":cat,"rows":rows}; (root/"formal-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True))
