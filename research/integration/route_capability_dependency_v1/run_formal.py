#!/usr/bin/env python3
import json
from pathlib import Path
from selector import load_receipt,evaluate
root=Path(__file__).resolve().parent
sent=root/".formal-invoked"
if sent.exists(): raise SystemExit("formal allocation already invoked")
sent.write_text("1\n")
receipt=load_receipt(root); matrix=json.loads((root/"cases.json").read_text()); required=matrix["required_dimensions"]
rows=[]
for case in matrix["cases"]:
    rows.append({"case_id":case["id"],"current_context":case["current_context"],"required_dimensions":required,"baseline":evaluate(case,required,receipt,"dimension_only"),"candidate":evaluate(case,required,receipt,"dimension_plus_dependency")})
out={"schema":"route-capability-dependency-result-v1","formal_invocations":1,"receipt_route":receipt["route"],"verified_dimensions":receipt["verified_dimensions"],"rows":rows}
(root/"formal-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
