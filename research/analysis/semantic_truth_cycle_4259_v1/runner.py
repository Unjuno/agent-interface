from __future__ import annotations
import argparse,json,pathlib
from model import *
from schedule import SCHEDULE

def run():
    base={k:"UNKNOWN" for k in BASES}; gen={k:0 for k in BASES}
    naive={d:"UNKNOWN" for d in DERIVED}; cand={d:"UNKNOWN" for d in DERIVED}
    rows=[]; candidate_recomputes=0; global_recomputes=0
    for idx,(name,updates) in enumerate(SCHEDULE):
        changed=[]
        for k,v in updates.items():
            if base[k]!=v or name.startswith(k.upper()+"_RESTORE"):
                base[k]=v; gen[k]+=1; changed.append(k)
        oracle_vals=oracle(base)
        naive=local_support_retain(naive,base)
        cand,region=scc_grounded_retract(cand,base,changed)
        candidate_recomputes += len(region)
        global_recomputes += len(DERIVED)
        rows.append({
          "step":idx,"name":name,"base":dict(base),"generation":dict(gen),
          "changed":changed,"affected":sorted(region),"oracle":oracle_vals,
          "naive":dict(naive),"candidate":dict(cand),
          "oracle_macro":macro_ready(oracle_vals),"naive_macro":macro_ready(naive),
          "candidate_macro":macro_ready(cand),"authority":"none",
        })
    stale=[]
    for r in rows:
        for d in DERIVED:
            if r["naive"][d]=="TRUE" and r["oracle"][d]!="TRUE": stale.append([r["name"],d,r["oracle"][d]])
    return {"schema":"semantic-truth-cycle-v1","rows":rows,"candidate_recomputes":candidate_recomputes,
            "global_recomputes":global_recomputes,"naive_stale_true":stale,"authority":"none"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); ap.add_argument("--mode",choices=["construction","formal"],required=True); a=ap.parse_args()
    p=pathlib.Path(a.out); p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): raise SystemExit("OUTPUT_EXISTS")
    data=run(); data["mode"]=a.mode
    p.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"rows":len(data["rows"]),"naive_stale_true":len(data["naive_stale_true"]),"candidate_recomputes":data["candidate_recomputes"],"global_recomputes":data["global_recomputes"]},sort_keys=True))
if __name__=="__main__": main()
