from __future__ import annotations
import argparse, base64, hashlib, json, os, platform, time
from pathlib import Path
import numpy as np
import models
from models import cnn_init, conv_forward, cnn_predict, mlp_fit, mlp_predict, model_bytes
from prepare import CONSTRUCTION_SEED, EVAL_CENTERS, evaluation_data, training_data

IMAGE_ID = "sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824"
SCHEDULE = [(250,0.8),(1000,0.8),(4000,0.8),(1000,0.2),(4000,0.2)]

def loss(x,y,m):
    p=conv_forward(x,m)
    return float(-np.mean(y*np.log(np.clip(p,1e-7,1))+(1-y)*np.log(np.clip(1-p,1e-7,1)),dtype=np.float64))

def analytic_grad(x,y,m):
    p,(windows,pre,argmax,shape)=conv_forward(x,m,cache=True)
    dz=(p-y)/len(y)
    pooled=np.max(np.maximum(pre,0).reshape(len(x),-1,4),axis=1)
    gdense=pooled.T@dz
    gout=np.asarray(dz.sum(),dtype=np.float32)
    dpool=dz[:,None]*m[2][None,:]
    dact=np.zeros(shape,np.float32).reshape(len(x),-1,4)
    dact[np.arange(len(x))[:,None],argmax,np.arange(4)[None,:]]=dpool
    dpre=dact.reshape(shape)*(pre>0)
    gkernel=np.einsum("nhwij,nhwf->fij",windows,dpre,optimize=True)
    gbias=dpre.sum(axis=(0,1,2))
    return [gkernel,gbias,gdense,gout]

def gradient_check(x,y):
    init=cnn_init(CONSTRUCTION_SEED+5)
    m=[np.array(v,dtype=np.float32,copy=True) for v in init]
    m[1] += np.float32(.25)
    grads=analytic_grad(x,y,m)
    rows=[]; eps=np.float32(.002)
    names=("kernel","conv_bias","dense","output_bias")
    for family,(param,grad) in enumerate(zip(m,grads)):
        for i in range(param.size):
            old=float(param.flat[i])
            param.flat[i]=np.float32(old+eps); plus=loss(x,y,m)
            param.flat[i]=np.float32(old-eps); minus=loss(x,y,m)
            param.flat[i]=np.float32(old)
            numeric=(plus-minus)/(2*float(eps)); analytic=float(np.asarray(grad).flat[i])
            rows.append({"family":names[family],"index":i,"analytic":analytic,"numeric":numeric,
                         "abs_error":abs(analytic-numeric)})
    return rows

def decision(p):
    return "ACCEPT" if p>=.75 else "YIELD" if p>=.25 else "REJECT"

def score_rows(probs,y,meta,seed,arm,stratum,center):
    return [{"seed":seed,"arm":arm,"stratum":stratum,"center":list(center),
             "case_id":r["case_id"],"label":int(label),"image_sha256":r["image_sha256"],
             "probability":float(p),"decision":decision(float(p))}
            for p,label,r in zip(probs,y,meta)]

def summarize(rows):
    pos=[r for r in rows if r["label"]==1]; neg=[r for r in rows if r["label"]==0]
    return {"rows":len(rows),"positive_accept":sum(r["decision"]=="ACCEPT" for r in pos),
            "positive_total":len(pos),"negative_accept":sum(r["decision"]=="ACCEPT" for r in neg),
            "negative_total":len(neg),"positive_accept_rate":sum(r["decision"]=="ACCEPT" for r in pos)/len(pos),
            "negative_accept_rate":sum(r["decision"]=="ACCEPT" for r in neg)/len(neg),
            "positive_probability_median":float(np.median([r["probability"] for r in pos])),
            "negative_probability_median":float(np.median([r["probability"] for r in neg]))}

def run(out:Path):
    if out.exists() and any(out.iterdir()): raise FileExistsError("fresh output directory required")
    out.mkdir(parents=True,exist_ok=True); (out/"weights").mkdir()
    started=time.perf_counter(); seed=CONSTRUCTION_SEED
    x,y,trainmeta=training_data(seed+1,"treatment")
    control_x,control_y,control_meta=training_data(seed+1,"control")
    assert np.array_equal(y,control_y) and np.array_equal(x[1::2],control_x[1::2])
    grads=gradient_check(x,y.astype(np.float32))
    (out/"gradient_rows.jsonl").write_text("".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in grads),encoding="utf-8")
    gradient_max=max(r["abs_error"] for r in grads)
    fits=[]; predictions=[]
    base_x,base_y,base_meta=evaluation_data(seed+2,(20,15),"base")
    evals=[("train",x,y,trainmeta,(20,15)),("base",base_x,base_y,base_meta,(20,15))]
    evals += [(f"heldout_{i}",*evaluation_data(seed+10+i,c,f"heldout_{i}"),c) for i,c in enumerate(EVAL_CENTERS)]
    model_sha={}
    # Paired MLP reference under the parent schedule.
    models.STEPS=250; models.LR=np.float32(.8)
    t=time.perf_counter(); mm=mlp_fit(control_x.reshape(len(control_x),-1),control_y.astype(np.float32),seed+5)
    fits.append({"arm":"control","steps":250,"learning_rate":.8,"fit_seconds":time.perf_counter()-t,
                 "parameters":sum(a.size for a in mm),"weights_sha256":hashlib.sha256(model_bytes(mm)).hexdigest()})
    for name,xx,yy,meta,center in evals:
        pp=mlp_predict(mm,xx.reshape(len(xx),-1))
        predictions += score_rows(pp,yy,meta,seed,"control",name,center)
    model_sha["control"]=model_bytes(mm)
    for steps,lr in SCHEDULE:
        if time.perf_counter()-started >= 210:
            fits.append({"arm":"treatment","steps":steps,"learning_rate":lr,"status":"NOT_RUN_TIME_BUDGET"})
            break
        models.STEPS=steps; models.LR=np.float32(lr)
        t=time.perf_counter(); cm=models.cnn_fit(x,y.astype(np.float32),seed+5); elapsed=time.perf_counter()-t
        raw=model_bytes(cm); key=f"cnn-{steps}-{lr}"
        fits.append({"arm":"treatment","steps":steps,"learning_rate":lr,"fit_seconds":elapsed,
                     "parameters":sum(a.size for a in cm),"weights_sha256":hashlib.sha256(raw).hexdigest(),"status":"COMPLETE"})
        model_sha[key]=raw
        (out/"weights"/(key+".npz.b64")).write_text(base64.b64encode(raw).decode("ascii")+"\n",encoding="ascii")
        for name,xx,yy,meta,center in evals:
            pp=cnn_predict(cm,xx)
            predictions += score_rows(pp,yy,meta,seed,key,name,center)
        if time.perf_counter()-started >= 210:
            break
    (out/"weights"/"mlp-control.npz.b64").write_text(base64.b64encode(model_sha["control"]).decode("ascii")+"\n",encoding="ascii")
    (out/"predictions.jsonl").write_text("".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in predictions),encoding="utf-8")
    grouped={}
    for r in predictions: grouped.setdefault(r["arm"]+"/"+r["stratum"],[]).append(r)
    summaries={k:summarize(v) for k,v in sorted(grouped.items())}
    completed=[f for f in fits if f["arm"]=="treatment" and f.get("status")=="COMPLETE"]
    competent=[f for f in completed if summaries[f"cnn-{f['steps']}-{f['learning_rate']}/train"]["positive_accept_rate"]>=.95
               and summaries[f"cnn-{f['steps']}-{f['learning_rate']}/train"]["negative_accept"]==0
               and summaries[f"cnn-{f['steps']}-{f['learning_rate']}/base"]["positive_accept_rate"]>=.95
               and summaries[f"cnn-{f['steps']}-{f['learning_rate']}/base"]["negative_accept"]==0]
    gradpass=len(grads)==45 and gradient_max<=.01 and all(np.isfinite(r["numeric"]) and np.isfinite(r["analytic"]) for r in grads)
    if not gradpass: disposition="STOP_FINITE_DIFFERENCE_GRADIENT"
    elif competent: disposition="PASS_DIAGNOSTIC_CONSTRUCTION_ONLY"
    elif len(completed)<len(SCHEDULE): disposition="STOP_CONSTRUCTION_TIME_BUDGET"
    else: disposition="STOP_CONSTRUCTION_COMPETENCE_NOT_REACHED"
    env={"allocation":"tiny-visual-equivariant-diagnosis-2564-20260927-01","construction_seed":seed,
         "image_id":IMAGE_ID,"python":platform.python_version(),"numpy":np.__version__,
         "platform":platform.platform(),"network_expected":"none","gpu_used":False,
         "external_model_api_requests":0,"os_gui_or_input":False,"openblas_threads":os.environ.get("OPENBLAS_NUM_THREADS"),
         "elapsed_seconds":time.perf_counter()-started}
    result={"schema":"tiny-visual-equivariant-diagnosis-4817-v1","disposition":disposition,
            "gradient":{"parameter_scalars":len(grads),"max_absolute_error":gradient_max,"gate":gradpass},
            "construction_competence_schedules":[{"steps":f["steps"],"learning_rate":f["learning_rate"]} for f in competent],
            "fits":fits,"stratum_summaries":summaries,"heldout_is_descriptive_only":True,"environment":env}
    (out/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (out/"environment.json").write_text(json.dumps(env,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--out",type=Path,required=True); a=p.parse_args()
    print(json.dumps(run(a.out),sort_keys=True,indent=2))

