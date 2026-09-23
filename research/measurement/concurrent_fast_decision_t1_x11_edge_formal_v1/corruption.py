from __future__ import annotations
import argparse, copy, json, tempfile
from pathlib import Path
from audit import audit_obj

def check(name,obj):
    out=audit_obj(obj)
    return {"name":name,"rejected":out["decision"]!="PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED","decision":out["decision"]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("result"); ap.add_argument("--out",required=True)
    a=ap.parse_args(); base=json.loads(Path(a.result).read_text())
    tests=[]
    x=copy.deepcopy(base); x["formal_invocations"]=0; tests.append(check("formal_invocation",x))
    x=copy.deepcopy(base); x["cases"]=x["cases"][:-1]; tests.append(check("row_count",x))
    x=copy.deepcopy(base); 
    if x["cases"] and x["cases"][0].get("samples"): x["cases"][0]["samples"][0]["disposition"]="BOGUS"
    tests.append(check("selector_vocabulary",x))
    x=copy.deepcopy(base)
    cand=next((c for c in x["cases"] if c.get("arm")=="DETERMINISTIC_FAST_LANE"),None)
    if cand:
        cand.setdefault("effects",[]).append({"t_ns":cand.get("start_ns",0),"effect_kind":"harm"})
        cand.setdefault("score",{})["harm_pixels"]=1
    tests.append(check("harm_effect",x))
    out={"all_rejected":all(t["rejected"] for t in tests),"tests":tests}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0 if out["all_rejected"] else 5

if __name__=="__main__":
    raise SystemExit(main())
