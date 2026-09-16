#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from selector import load_evidence, derive_catalog, select

def main():
    root=Path(__file__).resolve().parent
    sentinel=root/".formal-invoked"
    if sentinel.exists(): raise SystemExit("formal allocation already invoked")
    sentinel.write_text("1\n")
    scale,center=load_evidence(root); catalog=derive_catalog(scale,center)
    matrix=json.loads((root/"requests.json").read_text())
    rows=[]
    for req in matrix["requests"]:
        rows.append({"request_id":req["id"],"required_dimensions":req["required_dimensions"],"allowed_routes":req["allowed_routes"],"baseline":select(req,catalog,"flat_route_success"),"candidate":select(req,catalog,"effect_dimension_match")})
    out={"schema":"route-capability-formal-result-v1","formal_invocations":1,"catalog":catalog,"rows":rows}
    (root/"formal-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
