from __future__ import annotations
import hashlib, json, math, sys, tempfile
from pathlib import Path
import numpy as np

ALLOCATION="tiny-visual-extent-init-sensitivity-4817-20260928-01"
DATA_SEED=89100471
INIT_SEED=58100472
THRESHOLD=0.75
CENTERS=((20,15),(8,8),(32,8),(8,22),(32,22))
HELD=((14,8),(26,8),(14,22),(26,22),(8,15),(20,25),(32,15),(20,8))
def digest(b): return hashlib.sha256(b).hexdigest()
def tiles(n,seed,centers,positive_size=9,negative_center=(4,4),negative_size=5,balanced=True):
    rng=np.random.default_rng(seed); x=rng.normal(0,.03,(n,1,30,40)).astype(np.float32); y=np.zeros(n,np.float32)
    for i in range(n):
        pos=(i%2==0) if balanced else True; y[i]=float(pos)
        if pos: cx,cy=centers[(i//2)%len(centers)]; size=positive_size
        else: cx,cy=negative_center; size=negative_size
        half=size//2; x[i,0,cy-half:cy+half+1,cx-half:cx+half+1]+=.8
    return x,y
def build_inputs():
    train=tiles(160,DATA_SEED,CENTERS); base=tiles(80,DATA_SEED+2,((20,15),))
    held={str(c):tiles(80,DATA_SEED+10+i,(c,)) for i,c in enumerate(HELD)}
    out={"train_x":train[0],"train_y":train[1],"base_x":base[0],"base_y":base[1]}
    for i,k in enumerate(sorted(held)): out[f"held_{i}_x"],out[f"held_{i}_y"]=held[k]
    return out
def init(seed,extent):
    rng=np.random.default_rng(seed); k=rng.normal(0,.04,(4,1,3,3)).astype(np.float32); b=np.zeros(4,np.float32)
    d=np.zeros(8 if extent else 4,np.float32); d[:4]=rng.normal(0,.04,4).astype(np.float32)
    return k,b,d,np.float32(0)
def direct_logits(x,kernel,bias,dense,output_bias,extent):
    n,_,height,width=x.shape; result=[]
    for batch in range(n):
        maxima=np.zeros(4,np.float64); sums=np.zeros(4,np.float64); count=(height-2)*(width-2)
        for row in range(height-2):
            for col in range(width-2):
                for channel in range(4):
                    z=float(bias[channel])
                    for dy in range(3):
                        for dx in range(3): z+=float(x[batch,0,row+dy,col+dx])*float(kernel[channel,0,dy,dx])
                    a=max(0.0,z); maxima[channel]=max(maxima[channel],a); sums[channel]+=a
        pool=np.concatenate((maxima,sums/count)) if extent else maxima
        result.append(float(pool@dense.astype(np.float64)+float(output_bias)))
    return np.asarray(result)
def metrics(logits,labels):
    p=1/(1+np.exp(-np.clip(np.asarray(logits,dtype=np.float64),-30,30))); y=np.asarray(labels)
    return {"accuracy_at_0_5":float(np.mean((p>=.5)==y)),
        "positive_accept":float(np.mean(p[y==1]>=THRESHOLD)),
        "negative_false_accept":float(np.mean(p[y==0]>=THRESHOLD)),
        "positive_mean_probability":float(np.mean(p[y==1])),"negative_mean_probability":float(np.mean(p[y==0])),
        "rows":int(len(y))}
def verify(result):
    result=Path(result); errors=[]
    rb=(result/"RAW.json").read_bytes(); raw=json.loads(rb.decode("utf-8"))
    for fn,key in (("INPUTS.npz","input_sha256"),("WEIGHTS.npz","weights_sha256"),("INITIAL_WEIGHTS.npz","initial_weights_sha256")):
        if not (result/fn).is_file() or digest((result/fn).read_bytes())!=raw.get(key): errors.append("hash:"+fn)
    if raw.get("schema")!="tiny-visual-extent-readout-cuda-v1": errors.append("schema")
    if raw.get("allocation")!=ALLOCATION or raw.get("data_seed")!=DATA_SEED or raw.get("init_seed")!=INIT_SEED: errors.append("identity_or_seed")
    if raw.get("steps")!=1000 or raw.get("learning_rate")!=.2 or raw.get("threshold")!=THRESHOLD: errors.append("protocol")
    ft=raw.get("fit_seconds",{})
    if set(ft)!={"max_only","max_mean"} or any(not math.isfinite(float(v)) or float(v)<0 for v in ft.values()): errors.append("fit_seconds")
    if raw.get("formal_fits")!=0 or raw.get("construction_fits")!=2: errors.append("fit_counts")
    fd=raw.get("finite_difference_probe",{})
    if not fd.get("pass") or fd.get("count")!=49 or fd.get("max_symmetric_relative_error",1)>=1e-4: errors.append("finite_difference")
    env=raw.get("environment",{})
    if env.get("cublas_workspace_config")!=":4096:8" or env.get("deterministic") is not True or "RTX 3080" not in env.get("gpu",""): errors.append("environment")
    with np.load(result/"INPUTS.npz",allow_pickle=False) as data, np.load(result/"WEIGHTS.npz",allow_pickle=False) as weights, np.load(result/"INITIAL_WEIGHTS.npz",allow_pickle=False) as initial:
        expected=build_inputs()
        if set(data.files)!=set(expected): errors.append("input_keys")
        else:
            if any(not np.array_equal(data[k],expected[k]) for k in expected): errors.append("input_regeneration")
            if data["train_x"].shape!=(160,1,30,40) or data["base_x"].shape!=(80,1,30,40): errors.append("input_shape")
        arm_names=("max_only","max_mean"); names=("kernel","bias","dense","output_bias")
        if set(weights.files)!={f"{a}_{n}" for a in arm_names for n in names}: errors.append("weight_keys")
        if set(initial.files)!={f"{a}_{n}" for a in arm_names for n in names}: errors.append("initial_keys")
        if not errors:
            for key in ("kernel","bias","output_bias"):
                if not np.array_equal(initial[f"max_only_{key}"],initial[f"max_mean_{key}"]): errors.append("paired_initial:"+key)
            if not np.array_equal(initial["max_only_dense"],initial["max_mean_dense"][:4]) or np.any(initial["max_mean_dense"][4:]!=0): errors.append("paired_dense_init")
            categories={"train":(data["train_x"],data["train_y"]),"base":(data["base_x"],data["base_y"])}
            for i in range(8): categories[f"held_{i}"]=(data[f"held_{i}_x"],data[f"held_{i}_y"])
            all_metrics={}
            for arm,extent in (("max_only",False),("max_mean",True)):
                all_metrics[arm]={}
                model=tuple(weights[f"{arm}_{n}"] for n in names)
                for cat,(x,y) in categories.items():
                    got=direct_logits(x,*model,extent); saved=np.asarray(raw["logits"][arm][cat],dtype=np.float64)
                    if saved.shape!=got.shape or not np.allclose(saved,got,rtol=1e-6,atol=1e-6): errors.append("logits:"+arm+":"+cat)
                    all_metrics[arm][cat]=metrics(got,y)
            cand=all_metrics["max_mean"]; base=all_metrics["max_only"]
            held_pos=[cand[f"held_{i}"]["positive_accept"] for i in range(8)]
            held_neg=[cand[f"held_{i}"]["negative_false_accept"] for i in range(8)]
            competence=(cand["train"]["accuracy_at_0_5"]>=.95 and cand["base"]["accuracy_at_0_5"]>=.95 and float(np.mean(held_pos))>=.90 and float(np.mean(held_neg))<=.01)
            discrim=float(np.mean([base[f"held_{i}"]["positive_accept"] for i in range(8)]))<.70
            decision="STOP_PROVENANCE_OR_AUDIT" if errors else ("STOP_NO_CONSTRUCTION_COMPETENCE" if not competence else ("HOLD_READOUT_NOT_DISCRIMINATING" if not discrim else "PASS_EXTENT_READOUT_CONSTRUCTION_SCOPED"))
    if errors: decision="STOP_PROVENANCE_OR_AUDIT"
    out={"schema":"extent-init-sensitivity-audit-v1","decision":decision,"integrity_pass":not errors,"errors":errors,
        "construction_metrics":all_metrics if not errors else None,"held_positive_accept_mean":float(np.mean(held_pos)) if not errors else None,
        "held_positive_accept_by_center":held_pos if not errors else None,"held_negative_false_accept_mean":float(np.mean(held_neg)) if not errors else None}
    return out
def main(path):
    result=Path(path); got=verify(result); (result/"AUDIT.json").write_text(json.dumps(got,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(got,sort_keys=True)); return 0 if got["integrity_pass"] else 2
if __name__=="__main__": raise SystemExit(main(sys.argv[1]))
