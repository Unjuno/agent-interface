#!/usr/bin/env python3
"""Finite initial/future property scorer for Issue #6611."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def score(f,scenario_id,route_name):
    route=f["routes"][route_name];transform=next(s for s in f["scenarios"] if s["id"]==scenario_id)["transforms"][route_name]
    required=f["required_properties"];initial_missing=sorted(set(required)-set(route["properties"]))
    initial_pass=not initial_missing
    if transform.get("open") is False:
        status="FAIL";missing=[];cosmetic=[];transport=False
    elif transform.get("dependency_available") is False:
        status="UNKNOWN";missing=[];cosmetic=[];transport=True
    else:
        missing=sorted(set(transform.get("drop",[])) & set(required))
        cosmetic=sorted(set(transform.get("cosmetic",[])) & set(f["cosmetic_fields"]))
        status="FAIL" if missing else "PASS";transport=True
    repair=route["repair_cost_ms"] if status=="FAIL" else 0
    total=route["initial_cost_ms"]+route["reopen_cost_ms"]+(repair or 0) if status!="UNKNOWN" else None
    return {"scenario":scenario_id,"route":route_name,"initial_pass":initial_pass,
      "initial_missing":initial_missing,"transport_success":transport,"later_status":status,
      "missing_significant_properties":missing,"cosmetic_differences":cosmetic,
      "hash_is_semantic_oracle":False,"cumulative_cost_ms":total}

def run(f):
    return {"schema":"unjuno.issue6611.t0.candidate.v1",
      "initial":[{"route":name,"pass":all(f["routes"][name]["properties"].get(k)==f["expected_properties"][k] for k in f["required_properties"])}
                 for name in sorted(f["routes"])],
      "later":[score(f,s["id"],route) for s in f["scenarios"] for route in sorted(f["routes"])]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    f=json.loads((HERE/"fixture.json").read_text(encoding="utf-8"));r=run(f)
    r["fixture_sha256"]=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest()
    r["candidate_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"initial_routes":len(r["initial"]),"future_rows":len(r["later"]),"later_statuses":{x:sum(y["later_status"]==x for y in r["later"]) for x in ("PASS","FAIL","UNKNOWN")}}))
if __name__=="__main__":main()
