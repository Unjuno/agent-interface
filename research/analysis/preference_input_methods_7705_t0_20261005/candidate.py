"""Candidate menu evaluator for synthetic preference-input cases only."""
import json,math
from pathlib import Path
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/"cases.json").read_text())
CRITERIA=tuple(DATA["criteria"])


def dominates(a,b,criteria):
    av=[a["outcomes"][k] for k in criteria]; bv=[b["outcomes"][k] for k in criteria]
    return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))


def evaluate(case,routes=None,criteria=None):
    routes=case.get("routes",DATA["routes"]) if routes is None else routes
    criteria=CRITERIA if criteria is None else tuple(criteria)
    valid=[]
    for r in routes:
        if set(r.get("outcomes",{}))!=set(criteria): return {"status":"HOLD_MENU_INCOMPLETE","selected":[],"pareto":[]}
        if r.get("eligible"):
            values=list(r["outcomes"].values())
            if any(not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in values):
                return {"status":"HOLD_MENU_INVALID","selected":[],"pareto":[]}
            valid.append(r)
    front=[r["id"] for r in valid if not any(dominates(q,r,criteria) for q in valid if q is not r)]
    mode=case.get("mode"); inp=case.get("input",{})
    if mode=="weights":
        w=inp.get("weights",{})
        if set(w)!=set(criteria) or any(not isinstance(x,(int,float)) or x<0 for x in w.values()) or abs(sum(w.values())-1)>1e-9:
            return {"status":"HOLD_INPUT_INVALID","selected":[],"pareto":front}
        score=lambda r:sum(w[k]*r["outcomes"][k] for k in criteria)
        best=min(score(r) for r in valid)
        selected=[r["id"] for r in valid if abs(score(r)-best)<=1e-12]
    elif mode=="classify":
        if set(inp)!=set(criteria): return {"status":"HOLD_INPUT_INCOMPLETE","selected":[],"pareto":front}
        selected=[]
        for r in valid:
            ok=True
            for k,v in inp.items():
                status=v.get("status")
                if status not in ("target","accept","free"): return {"status":"HOLD_INPUT_INVALID","selected":[],"pareto":front}
                if status!="free" and ("limit" not in v or r["outcomes"][k]>v["limit"]): ok=False
            if ok: selected.append(r["id"])
    elif mode=="pairwise":
        chosen=next((r for r in valid if r["id"]==inp.get("route_id")),None)
        if chosen is None: return {"status":"HOLD_INELIGIBLE_SELECTION","selected":[],"pareto":front}
        selected=[chosen["id"]]
    else: return {"status":"HOLD_MODE_UNKNOWN","selected":[],"pareto":front}
    status="NO_FEASIBLE_ROUTE" if not selected else "AMBIGUOUS_SET" if len(selected)>1 else "SELECTED"
    return {"status":status,"selected":selected,"pareto":front}


def main():
    rows=[{"case_id":c["id"],"result":evaluate(c)} for c in DATA["cases"]]
    out=ROOT/"formal_01";out.mkdir(exist_ok=True)
    raw=json.dumps(rows,indent=2)+"\n"
    (out/"RAW.json").write_text(raw)
    import hashlib
    (out/"CANDIDATE_RECEIPT.json").write_text(json.dumps({"command":"python3 -B candidate.py","exit_code":0,"cases":len(rows),"raw_sha256":hashlib.sha256(raw.encode()).hexdigest()},indent=2)+"\n")
    print(json.dumps(rows))


if __name__=="__main__":main()
