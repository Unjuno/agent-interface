import copy,json,sys
import torch
from torch.nn import functional as F

def check(ok,msg):
    if not ok: raise ValueError(msg)

def audit(doc):
    check(doc.get("schema")=="needle-online-correction-frontier-v2","schema")
    check(len(doc.get("runs",[]))==3,"seed count")
    points=0
    for r in doc["runs"]:
        seed=r["seed"]; w=r["base_final"]; x_a=torch.tensor(r["x_a"],dtype=torch.float32);y_a=torch.tensor(r["y_a"],dtype=torch.long);x_b=torch.tensor(r["x_b"],dtype=torch.float32);y_b=torch.tensor(r["y_b"],dtype=torch.long)
        check(len(r["curve"])==33 and len(r["snapshots"])==33,"curve length")
        check(len(r["support_x"])==32 and len(r["update_ms"])==32,"update count")
        check(r["y_a"]==[int(x[0]) for x in r["x_a"]],"A label contract")
        check(r["y_b"]==[1-int(x[0]) for x in r["x_b"]],"B label contract")
        check(r["support_y"]==[[1-int(x[0]) for x in batch] for batch in r["support_x"]],"support label contract")
        for batch in r["support_x"]: check(sum(int(x[0]) for x in batch)==4,"support balance")
        for k in w: check(w[k]==r["base_initial"][k],"base mutation")
        def base(x): return F.linear(torch.tanh(F.linear(x,torch.tensor(w["l1.weight"]),torch.tensor(w["l1.bias"]))),torch.tensor(w["l2.weight"]),torch.tensor(w["l2.bias"]))
        for j,(snap,row) in enumerate(zip(r["snapshots"],r["curve"])):
            a=torch.tensor(snap["a"],dtype=torch.float32);b=torch.tensor(snap["b"],dtype=torch.float32)
            if j==0: check(torch.count_nonzero(b).item()==0,"zero initial delta")
            def f(x):
                h=torch.tanh(F.linear(x,torch.tensor(w["l1.weight"]),torch.tensor(w["l1.bias"])))
                return F.linear(h,torch.tensor(w["l2.weight"]),torch.tensor(w["l2.bias"]))+(h@b.T@a.T)*0.25
            with torch.no_grad(): pa=f(x_a);pb=f(x_b);ca=int((pa.argmax(-1)==y_a).sum());cb=int((pb.argmax(-1)==y_b).sum());cea=float(F.cross_entropy(pa,y_a));ceb=float(F.cross_entropy(pb,y_b))
            check((ca,cb)==(row["a_correct"],row["b_correct"]),f"{seed} step{j} accuracy")
            check(abs(cea-row["ce_a"])<1e-6 and abs(ceb-row["ce_b"])<1e-6,f"{seed} step{j} CE")
            points+=1
        with torch.no_grad(): check(base(x_a).tolist()==r["base_logits_a"],"base logits")
        final=r["snapshots"][-1];fa=torch.tensor(final["a"],dtype=torch.float32);fb=torch.tensor(final["b"],dtype=torch.float32)
        def final_forward(x):
            h=torch.tanh(F.linear(x,torch.tensor(w["l1.weight"]),torch.tensor(w["l1.bias"])))
            return F.linear(h,torch.tensor(w["l2.weight"]),torch.tensor(w["l2.bias"]))+(h@fb.T@fa.T)*0.25
        with torch.no_grad():
            check(final_forward(x_a).tolist()==r["candidate_final_logits_a"],"final A logits")
            check(final_forward(x_b).tolist()==r["candidate_final_logits_b"],"final B logits")
        controls=r["controls"];check(controls[0]["decision"]=="PROPOSE" and controls[0]["logits"] is not None,"valid route")
        check(all(c["decision"]=="YIELD" and c["logits"] is None for c in controls[1:]),"invalid route")
    return {"disposition":"AUDIT_PASS","runs":3,"curve_points":points,"base_immutable":"PASS","controls":9,"errors":[]}

def main(path):
    doc=json.load(open(path,encoding="utf-8"));result=audit(doc)
    bad=copy.deepcopy(doc);bad["runs"][0]["curve"][1]["a_correct"]+=1
    try: audit(bad)
    except ValueError: result["corruption_controls_rejected"]=1
    else: raise SystemExit("AUDIT_FAIL: corrupted metric accepted")
    bad_logits=copy.deepcopy(doc);bad_logits["runs"][0]["candidate_final_logits_b"][0][0]+=0.1
    try: audit(bad_logits)
    except ValueError: result["logit_corruption_controls_rejected"]=1
    else: raise SystemExit("AUDIT_FAIL: corrupted logits accepted")
    print(json.dumps(result,separators=(",",":")))

if __name__=="__main__": main(sys.argv[1])

