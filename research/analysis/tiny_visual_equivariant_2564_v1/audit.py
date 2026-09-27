from __future__ import annotations

import argparse,base64,hashlib,json
from pathlib import Path
import numpy as np
from prepare import ALLOCATION,ARMS,EVAL_CENTERS,FORMAL_SEEDS,evaluation_data,training_data
from models import cnn_fit,cnn_predict,mlp_fit,mlp_predict,model_bytes

def read_jsonl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]

def independently_check(root:Path):
    predictions=read_jsonl(root/"predictions.jsonl"); receipts=read_jsonl(root/"training_receipts.jsonl")
    train=read_jsonl(root/"training_manifest.jsonl"); ev=read_jsonl(root/"evaluation_manifest.jsonl")
    bykey={(r["seed"],r["arm"],r["stratum"],r["case_id"]):r for r in predictions}
    assert len(bykey)==len(predictions)==5*2*9*80
    assert len(receipts)==10 and len(train)==5*2*160 and len(ev)==5*9*80
    expected=[]
    receipt_by={(r["seed"],r["arm"]):r for r in receipts}
    for seed in FORMAL_SEEDS:
        for arm in ARMS:
            x,y,meta=training_data(seed+1,arm)
            model=(mlp_fit(x.reshape(len(x),-1),y.astype(np.float32),seed+5) if arm=="control"
                   else cnn_fit(x,y.astype(np.float32),seed+5))
            raw=model_bytes(model); weight_sha=hashlib.sha256(raw).hexdigest()
            receipt=receipt_by[(seed,arm)]
            assert receipt["final_weights_sha256"]==weight_sha
            assert receipt["training_inputs_sha256"]==hashlib.sha256(x.tobytes(order="C")).hexdigest()
            assert receipt["training_rows"]==160 and receipt["positive_rows"]==80 and receipt["negative_rows"]==80
            assert receipt["parameters"]==(19217 if arm=="control" else 45)
            saved=base64.b64decode((root/"weights"/f"{seed}-{arm}.npz.b64").read_text().strip())
            assert hashlib.sha256(saved).hexdigest()==weight_sha
            for sidx,(name,center,dseed) in enumerate([("base",(20,15),seed+2)]+[(f"heldout_{i}",c,seed+10+i) for i,c in enumerate(EVAL_CENTERS)]):
                xx,yy,rows=evaluation_data(dseed,center,name)
                pp=(mlp_predict(model,xx.reshape(len(xx),-1)) if arm=="control" else cnn_predict(model,xx))
                for row,label,p in zip(rows,yy.tolist(),pp.tolist()):
                    key=(seed,arm,name,row["case_id"]); actual=bykey[key]
                    assert actual["image_sha256"]==row["image_sha256"] and actual["label"]==label
                    assert abs(actual["probability"]-p)<2e-6
                    assert actual["weight_sha256"]==weight_sha
                    assert actual["model_decision"]==("ACCEPT" if p>=.75 else "YIELD" if p>=.25 else "REJECT")
                    assert actual["classification"]==int(p>=.5)
                    expected.append(actual)
    # Verify training manifests are exact regenerated data, including negative pairing.
    tm={(r["seed"],r["arm"],r["case_id"]):r for r in train}
    for seed in FORMAL_SEEDS:
        for arm in ARMS:
            _,_,rows=training_data(seed+1,arm)
            for row in rows:
                got=tm[(seed,arm,row["case_id"])]
                assert got["image_sha256"]==row["image_sha256"] and got["label"]==row["label"]
    counts={}
    for arm in ARMS:
        for stratum in ["base"]+[f"heldout_{i}" for i in range(8)]:
            rs=[r for r in predictions if r["arm"]==arm and r["stratum"]==stratum]
            pos=[r for r in rs if r["label"]==1]; neg=[r for r in rs if r["label"]==0]
            accept=sum(r["model_decision"]=="ACCEPT" for r in pos)
            false=sum(r["model_decision"]=="ACCEPT" for r in neg)
            acc=sum(r["classification"]==r["label"] for r in rs)/len(rs)
            counts[f"{arm}/{stratum}"]={"positive_accept":accept,"positive_total":len(pos),
                "negative_accept":false,"negative_total":len(neg),"accuracy":acc,
                "accept_rate":accept/len(pos) if pos else 0}
    fixture=json.loads((root/"gate_fixture.json").read_text(encoding="utf-8"))
    assert len(fixture)==4 and all(not r["final_accept"] for r in fixture if r["case_id"]!="live_positive")
    assert next(r for r in fixture if r["case_id"]=="live_positive")["final_accept"]
    tp=[r for r in predictions if r["arm"]=="treatment" and r["stratum"].startswith("heldout_") and r["label"]==1]
    cp=[r for r in predictions if r["arm"]=="control" and r["stratum"].startswith("heldout_") and r["label"]==1]
    tn=[r for r in predictions if r["arm"]=="treatment" and r["stratum"].startswith("heldout_") and r["label"]==0]
    pooled=sum(r["model_decision"]=="ACCEPT" for r in tp)/len(tp)
    control=sum(r["model_decision"]=="ACCEPT" for r in cp)/len(cp)
    per=[counts[f"treatment/heldout_{i}"]["accept_rate"] for i in range(8)]
    false=sum(r["model_decision"]=="ACCEPT" for r in tn)
    base=counts["treatment/base"]["accept_rate"]
    env=json.loads((root/"environment.json").read_text(encoding="utf-8"))
    total_fit=sum(r["fit_seconds"] for r in receipts)
    warm_p95=env["warm_inference_p95_ms_per_row"]
    outcome={"schema":"tiny-visual-equivariant-4814-audit-v1","allocation":ALLOCATION,"counts":counts,
        "treatment_heldout_pooled_accept_rate":pooled,"control_heldout_pooled_accept_rate":control,
        "heldout_lift_points":100*(pooled-control),"treatment_heldout_accept_rate_by_center":per,
        "treatment_base_accept_rate":base,"treatment_heldout_false_accepts":false,
        "total_fit_seconds":total_fit,"warm_inference_p95_ms_per_row":warm_p95,
        "pass_components":{"pooled_at_least_80pct":pooled>=.8,"each_center_at_least_50pct":all(x>=.5 for x in per),
            "base_at_least_95pct":base>=.95,"zero_heldout_false_accepts":false==0,
            "lift_at_least_20pp":pooled-control>=.2,"gate_fixture_pass":True,
            "fit_within_300_seconds":total_fit<=300,"inference_p95_within_60ms":warm_p95<60}}
    outcome["pass"]=all(outcome["pass_components"].values())
    return outcome

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    result=independently_check(a.root);a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2,sort_keys=True))

