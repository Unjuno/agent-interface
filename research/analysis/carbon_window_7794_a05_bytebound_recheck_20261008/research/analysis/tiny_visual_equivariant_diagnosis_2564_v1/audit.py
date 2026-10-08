from __future__ import annotations
import argparse,base64,hashlib,json
from pathlib import Path
import numpy as np
import models
from models import cnn_init,conv_forward,cnn_predict,mlp_fit,mlp_predict,model_bytes
from prepare import CONSTRUCTION_SEED,EVAL_CENTERS,evaluation_data,training_data

def readj(path): return json.loads(path.read_text(encoding="utf-8"))
def readjl(path): return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s]
def ref_loss(x,y,m):
    q=conv_forward(x,m)
    q=np.minimum(np.maximum(q,1e-7),1.0)
    nq=np.minimum(np.maximum(1-q,1e-7),1.0)
    return float(-np.mean(y*np.log(q)+(1-y)*np.log(nq),dtype=np.float64))
def ref_gradient(x,y,m):
    pred,(windows,pre,argmax,shape)=conv_forward(x,m,cache=True)
    delta=(pred-y)/float(len(y))
    pooled=np.max(np.maximum(pre,0).reshape(len(x),-1,4),axis=1)
    dense_gradient=np.matmul(pooled.T,delta)
    scalar_gradient=np.asarray(delta.sum(),dtype=np.float32)
    pool_gradient=delta[:,None]*m[2][None,:]
    activation_gradient=np.zeros(shape,dtype=np.float32).reshape(len(x),-1,4)
    activation_gradient[np.arange(len(x))[:,None],argmax,np.arange(4)[None,:]]=pool_gradient
    pre_gradient=activation_gradient.reshape(shape)*(pre>0)
    kernel_gradient=np.einsum("nhwij,nhwf->fij",windows,pre_gradient,optimize=True)
    bias_gradient=pre_gradient.sum(axis=(0,1,2))
    return [kernel_gradient,bias_gradient,dense_gradient,scalar_gradient]
def load_weights(path):
    raw=base64.b64decode(path.read_text(encoding="ascii").strip(),validate=True)
    with np.load(__import__("io").BytesIO(raw),allow_pickle=False) as z:
        return tuple(np.array(z[f"p{i}"]) for i in range(4)),raw
def run(root:Path,source:Path,expected_path:Path,out:Path):
    errors=[]
    expected=readj(expected_path)
    for name,want in expected.items():
        got=hashlib.sha256((source/name).read_bytes()).hexdigest()
        if got!=want: errors.append("source_sha:"+name)
    result=readj(root/"result.json"); rows=readjl(root/"gradient_rows.jsonl")
    seed=CONSTRUCTION_SEED;x,y,_=training_data(seed+1,"treatment"); y=y.astype(np.float32)
    probe=[np.array(v,dtype=np.float32,copy=True) for v in cnn_init(seed+5)]
    probe[1]+=np.float32(.25)
    grads=ref_gradient(x,y,probe)
    if len(rows)!=45: errors.append("gradient_row_count")
    names=("kernel","conv_bias","dense","output_bias"); eps=np.float32(.002)
    for row in rows:
        fam=names.index(row["family"]); param=probe[fam]; idx=int(row["index"]); original=float(param.flat[idx])
        param.flat[idx]=np.float32(original+eps); plus=ref_loss(x,y,probe)
        param.flat[idx]=np.float32(original-eps); minus=ref_loss(x,y,probe)
        param.flat[idx]=np.float32(original)
        numeric=(plus-minus)/(2*float(eps)); analytic=float(np.asarray(grads[fam]).flat[idx])
        if abs(numeric-row["numeric"])>1e-8 or abs(analytic-row["analytic"])>1e-7 or abs(numeric-analytic)>.01:
            errors.append("gradient_mismatch:"+row["family"]+":"+str(idx))
    predictions=readjl(root/"predictions.jsonl")
    fits=result["fits"]; replay_checks=0
    fit_map={(f.get("steps"),f.get("learning_rate")):f for f in fits if f.get("arm")=="treatment" and f.get("status")=="COMPLETE"}
    if len(fit_map)>5: errors.append("unexpected_fit_count")
    for arm in ("control",)+tuple("cnn-%s-%s"%k for k in fit_map):
        if arm=="control":
            model_x,model_y,_=training_data(seed+1,"control")
            models.STEPS=250;models.LR=np.float32(.8)
            model=mlp_fit(model_x.reshape(len(model_x),-1),model_y.astype(np.float32),seed+5)
            wpath=root/"weights/mlp-control.npz.b64"
        else:
            steps,lr=tuple((int(s),float(lr)) for s,lr in [arm[4:].split("-")])[0]
            model_x,model_y,_=training_data(seed+1,"treatment")
            models.STEPS=steps;models.LR=np.float32(lr)
            model=models.cnn_fit(model_x,model_y.astype(np.float32),seed+5)
            wpath=root/"weights"/(arm+".npz.b64")
        raw=model_bytes(model); saved,savedraw=load_weights(wpath)
        if hashlib.sha256(raw).hexdigest()!=hashlib.sha256(savedraw).hexdigest(): errors.append("replayed_weight_hash:"+arm)
        f=next((z for z in fits if z.get("arm")==("control" if arm=="control" else "treatment") and
                (arm=="control" or (z.get("steps")==steps and z.get("learning_rate")==lr))),None)
        if f is None or f["weights_sha256"]!=hashlib.sha256(raw).hexdigest(): errors.append("fit_receipt:"+arm)
        replay_checks+=1
        evals=[("train",*training_data(seed+1,"treatment" if arm!="control" else "control")[:2],
                training_data(seed+1,"treatment" if arm!="control" else "control")[2],(20,15))]
        bx,by,bm=evaluation_data(seed+2,(20,15),"base");evals.append(("base",bx,by,bm,(20,15)))
        evals += [(f"heldout_{i}",*evaluation_data(seed+10+i,c,f"heldout_{i}"),c) for i,c in enumerate(EVAL_CENTERS)]
        for stratum,xx,yy,meta,center in evals:
            probs=mlp_predict(model,xx.reshape(len(xx),-1)) if arm=="control" else cnn_predict(model,xx)
            found={(r["case_id"]):r for r in predictions if r["arm"]==arm and r["stratum"]==stratum}
            if len(found)!=80: errors.append("row_count:"+arm+":"+stratum);continue
            for p,label,mrow in zip(probs,yy,meta):
                got=found.get(mrow["case_id"])
                expected_decision="ACCEPT" if float(p)>=.75 else "YIELD" if float(p)>=.25 else "REJECT"
                if got is None or got["image_sha256"]!=mrow["image_sha256"] or got["label"]!=int(label) or abs(got["probability"]-float(p))>2e-6 or got["decision"]!=expected_decision:
                    errors.append("prediction_mismatch:"+arm+":"+stratum+":"+mrow["case_id"])
                    break
    unique={(r["arm"],r["stratum"],r["case_id"]) for r in predictions}
    if len(unique)!=len(predictions): errors.append("duplicate_prediction_key")
    expected_count=9*80*(1+len(fit_map))
    if len(predictions)!=expected_count: errors.append("prediction_total")
    typed=result["disposition"]
    if typed=="STOP_FINITE_DIFFERENCE_GRADIENT" and result["gradient"]["gate"]: errors.append("disposition_gradient_inconsistent")
    if typed=="PASS_DIAGNOSTIC_CONSTRUCTION_ONLY" and not result["construction_competence_schedules"]: errors.append("disposition_competence_inconsistent")
    audit={"schema":"tiny-visual-equivariant-diagnosis-audit-v1","status":"PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT",
           "errors":errors,"source_files_checked":len(expected),"gradient_scalars_checked":len(rows),
           "model_weight_replays":replay_checks,"prediction_rows_checked":len(predictions),
           "formal_fits":0,"scientific_efficacy_claim":False}
    out.write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return audit
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--source",type=Path,required=True)
    p.add_argument("--expected",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.root,a.source,a.expected,a.out),sort_keys=True,indent=2))

