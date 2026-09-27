from __future__ import annotations

import argparse, base64, hashlib, json, os, platform, time
from pathlib import Path

import numpy as np
from models import cnn_fit, cnn_predict, mlp_fit, mlp_predict, model_bytes
from prepare import ALLOCATION, ARMS, EVAL_CENTERS, FORMAL_SEEDS, training_data, evaluation_data

IMAGE_ID="sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824"

def dump_json(path,obj): path.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
def dump_jsonl(path,rows):
    path.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows),encoding="utf-8",newline="\n")

def fixture():
    rows=[]
    for name,p,receipt,fresh,pos in [("live_positive",.99,True,True,True),("stale_positive",.99,True,False,True),
                                      ("mismatch_positive",.99,False,True,True),("live_negative",.01,True,True,False)]:
        decision="ACCEPT" if p>=.75 else "REJECT" if p<.25 else "YIELD"
        rows.append({"case_id":name,"model_probability":p,"receipt_matches":receipt,"fresh":fresh,"positive":pos,
                     "model_decision":decision,"final_accept":decision=="ACCEPT" and receipt and fresh and pos})
    return rows

def run(out:Path):
    if out.exists() and any(out.iterdir()): raise FileExistsError("output directory must be empty; formal run cannot be retried")
    out.mkdir(parents=True,exist_ok=True); (out/"weights").mkdir()
    preds=[]; trainmeta=[]; evalmeta=[]; receipts=[]; started_all=time.perf_counter(); warm=[]
    for seed in FORMAL_SEEDS:
        fitted={}
        for arm in ARMS:
            x,y,meta=training_data(seed+1,arm); init_seed=seed+5; t=time.perf_counter()
            if arm=="control": model=mlp_fit(x.reshape(len(x),-1),y.astype(np.float32),init_seed)
            else: model=cnn_fit(x,y.astype(np.float32),init_seed)
            elapsed=time.perf_counter()-t; raw=model_bytes(model); sha=hashlib.sha256(raw).hexdigest()
            (out/"weights"/f"{seed}-{arm}.npz.b64").write_text(base64.b64encode(raw).decode("ascii")+"\n",encoding="ascii",newline="\n")
            fitted[arm]=(model,sha)
            for r in meta: trainmeta.append({"seed":seed,"arm":arm,**r})
            receipts.append({"seed":seed,"arm":arm,"initialization_seed":init_seed,"final_weights_sha256":sha,
                "training_inputs_sha256":hashlib.sha256(x.tobytes(order="C")).hexdigest(),"training_rows":len(y),
                "positive_rows":int(y.sum()),"negative_rows":int(len(y)-y.sum()),"steps":250,"learning_rate":0.8,
                "fit_seconds":elapsed,"python":platform.python_version(),"numpy":np.__version__,
                "parameters":sum(p.size for p in model),"openblas_threads":os.environ.get("OPENBLAS_NUM_THREADS")})
        strata=[("base",(20,15),seed+2)]+[(f"heldout_{i}",c,seed+10+i) for i,c in enumerate(EVAL_CENTERS)]
        for name,center,dseed in strata:
            x,y,meta=evaluation_data(dseed,center,name)
            for r in meta: evalmeta.append({"seed":seed,"stratum":name,"center":list(center),**r})
            for arm,(model,sha) in fitted.items():
                xx=x if arm=="treatment" else x.reshape(len(x),-1)
                fn=cnn_predict if arm=="treatment" else mlp_predict
                fn(model,xx) # warmup
                t=time.perf_counter(); probs=fn(model,xx); warm.append((time.perf_counter()-t)/len(x))
                for r,label,p in zip(meta,y.tolist(),probs.tolist()):
                    decision="ACCEPT" if p>=.75 else "YIELD" if p>=.25 else "REJECT"
                    preds.append({"seed":seed,"arm":arm,"stratum":name,"center":list(center),"case_id":r["case_id"],
                        "label":int(label),"image_sha256":r["image_sha256"],"weight_sha256":sha,"probability":float(p),
                        "model_decision":decision,"classification":int(p>=.5)})
    dump_jsonl(out/"training_manifest.jsonl",trainmeta);dump_jsonl(out/"evaluation_manifest.jsonl",evalmeta)
    dump_jsonl(out/"predictions.jsonl",preds);dump_jsonl(out/"training_receipts.jsonl",receipts)
    dump_json(out/"gate_fixture.json",fixture())
    env={"allocation":ALLOCATION,"formal_seeds":FORMAL_SEEDS,"image_id":IMAGE_ID,"python":platform.python_version(),
        "numpy":np.__version__,"platform":platform.platform(),"network_expected":"none","fits":len(receipts),
        "prediction_rows":len(preds),"training_wall_seconds":time.perf_counter()-started_all,
        "warm_inference_p95_ms_per_row":float(np.percentile(np.asarray(warm)*1000,95)),
        "external_model_api_requests":0,"local_model_fits":len(receipts),"gpu_used":False,"host_gui_or_authority":False}
    dump_json(out/"environment.json",env);return env

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.out),indent=2,sort_keys=True))

