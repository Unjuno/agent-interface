"""Paired pilot-09: contract-bound disjoint stratified CORRECT mixture."""
import hashlib
import json
import math
import random
import statistics
import time

import torch
from torch import nn

SEEDS=(3490,3491,3492)
ISSUE_CONTRACT_SHA256="a0b0a504ebe2342e379f2f20bbd7636a0a538740bc5e753210a67a47dae551e7"
LABELS=("CONTINUE","CORRECT","WATCH")
META={"intent":"track_target","scope":"local-servo","epoch":7}
STEPS=700
N_CLASS=1024


def balanced_class(label,n,seed):
    g=torch.Generator().manual_seed(seed)
    if label==0:
        xy=(torch.rand(n,2,generator=g)-.5)*.08
        velocity=(torch.rand(n,2,generator=g)-.5)*.08
        confidence=.72+.28*torch.rand(n,1,generator=g); visible=torch.ones(n,1)
    elif label==1:
        sign=torch.where(torch.rand(n,1,generator=g)>.5,1.,-1.)
        dx=sign*(.15+.80*torch.rand(n,1,generator=g))
        dy=(torch.rand(n,1,generator=g)-.5)*1.6
        xy=torch.cat((dx,dy),1); velocity=(torch.rand(n,2,generator=g)-.5)*.4
        confidence=.72+.28*torch.rand(n,1,generator=g); visible=torch.ones(n,1)
    elif label==2:
        xy=(torch.rand(n,2,generator=g)-.5)*2.
        velocity=(torch.rand(n,2,generator=g)-.5)*.8
        confidence=.72*torch.rand(n,1,generator=g)
        visible=torch.randint(0,2,(n,1),generator=g).float()
    else: raise ValueError("unknown class")
    return torch.cat((xy,velocity,confidence,visible),1)


def shifted_class(label,n,seed,band=None):
    if label!=1: return balanced_class(label,n,seed)
    g=torch.Generator().manual_seed(seed)
    sign=torch.where(torch.rand(n,1,generator=g)>.5,1.,-1.)
    if band is None:
        lo,span=.071,.078
    elif band==0:
        lo,span=.071,.039
    elif band==1:
        lo,span=.111,.038
    else: raise ValueError("unknown band")
    dx=sign*(lo+span*torch.rand(n,1,generator=g))
    dy=(torch.rand(n,1,generator=g)-.5)*.20
    velocity=(torch.rand(n,2,generator=g)-.5)*.10
    confidence=.80+.20*torch.rand(n,1,generator=g)
    visible=torch.ones(n,1)
    return torch.cat((dx,dy,velocity,confidence,visible),1)


def teacher(x):
    dx,dy,vx,vy,confidence,visible=x.unbind(-1)
    watch=(confidence<.72)|(visible<.5)
    settled=(dx.abs()<.06)&(dy.abs()<.06)&((vx.abs()+vy.abs())<.12)
    return torch.where(watch,2,torch.where(settled,0,1)).long()


class Needle(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(6,16),nn.Tanh(),nn.Linear(16,16),nn.Tanh(),nn.Linear(16,3))
    def forward(self,x): return self.net(x)


def proposal(meta,x,model):
    if meta!=META: return None,"YIELD_METADATA"
    if not torch.isfinite(x).all(): return None,"YIELD_NONFINITE"
    dx,dy,vx,vy,confidence,visible=x.tolist()
    if max(abs(dx),abs(dy))>1.25 or max(abs(vx),abs(vy))>1.0 or not 0<=confidence<=1 or visible not in (0.,1.):
        return None,"YIELD_ENVELOPE"
    if (abs(confidence-.72)<.03 or abs(abs(dx)-.06)<.01 or abs(abs(dy)-.06)<.01
            or abs(abs(vx)+abs(vy)-.12)<.02): return None,"YIELD_BOUNDARY"
    with torch.no_grad():
        return LABELS[int(model(x.unsqueeze(0)).argmax(-1).item())],"PROPOSAL"


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def state_record(model):
    state={name:{"shape":list(t.shape),"values":[float(v) for v in t.detach().cpu().reshape(-1)]}
           for name,t in model.state_dict().items()}
    return state,canonical_hash(state)


def training_rows(seed,augmented):
    classes=[balanced_class(c,2048,seed+10+c) for c in range(3)]
    if augmented:
        # Keep 1,024 exact balanced CORRECT control rows and replace only the other half.
        classes[1]=torch.cat((classes[1][:1024],shifted_class(1,512,seed+40,0),shifted_class(1,512,seed+41,1)),0)
    x=torch.cat(classes,0)
    return x,teacher(x)


def minibatch_stream(seed):
    g=torch.Generator().manual_seed(seed+30)
    return [torch.randint(6144,(64,),generator=g) for _ in range(STEPS)]


def train_arm(seed,augmented):
    random.seed(seed); torch.manual_seed(seed)
    train_x,train_y=training_rows(seed,augmented)
    model=Needle(); initial,initial_hash=state_record(model)
    opt=torch.optim.AdamW(model.parameters(),lr=.008)
    batches=minibatch_stream(seed)
    batch_hash=canonical_hash([batch.tolist() for batch in batches])
    train_x_hash=canonical_hash({"shape":list(train_x.shape),"rows":train_x.tolist()})
    train_y_hash=canonical_hash(train_y.tolist())
    model.train(); started=time.perf_counter_ns()
    for ix in batches:
        loss=nn.functional.cross_entropy(model(train_x[ix]),train_y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    train_ms=(time.perf_counter_ns()-started)/1e6
    model.eval(); final,final_hash=state_record(model)
    return model,{"initial_state_sha256":initial_hash,"model_state":final,
                  "model_state_sha256":final_hash,"train_ms":train_ms,
                  "optimizer_steps":STEPS,"train_rows":len(train_x),
                  "correct_near_boundary_rows":1024 if augmented else 0,
                  "train_features_sha256":train_x_hash,"train_labels_sha256":train_y_hash,
                  "minibatch_index_stream_sha256":batch_hash}


def boundary_rows():
    rows=[]
    for i in range(256):
        d=.25+(i%17)*.001
        rows.extend([[d,.2,.01,.02,.719,1.],[d,.2,.01,.02,.721,1.]])
        rows.extend([[.059,0.,.02,.02,.9,1.],[.061,0.,.02,.02,.9,1.]])
        rows.extend([[0.,0.,.059,.06,.9,1.],[0.,0.,.061,.06,.9,1.]])
    return torch.tensor(rows,dtype=torch.float32)


def invalid_inputs():
    return [
      ("stale_epoch",META|{"epoch":8},torch.tensor([.2,.2,0.,0.,.9,1.])),
      ("wrong_scope",META|{"scope":"other"},torch.tensor([.2,.2,0.,0.,.9,1.])),
      ("wrong_intent",{"intent":"other","scope":META["scope"],"epoch":META["epoch"]},torch.tensor([.2,.2,0.,0.,.9,1.])),
      ("out_of_envelope",META,torch.tensor([1.3,0.,0.,0.,.9,1.])),
      ("nonfinite",META,torch.tensor([float("nan"),0.,0.,0.,.9,1.]))]


def rows_for_suite(seed,shifted):
    out=[]
    for cls in range(3):
        gen=shifted_class if shifted else balanced_class
        x=gen(cls,N_CLASS,seed+(100 if shifted else 200)+cls)
        y=teacher(x)
        for features,label in zip(x,y):
            out.append({"x":[float(v) for v in features],"y":int(label)})
    return out


def add_decisions(rows,models):
    for row in rows:
        x=torch.tensor(row["x"],dtype=torch.float32)
        for arm,model in models.items():
            p,reason=proposal(META,x,model)
            row[arm]={"proposal":p,"reason":reason}


def run_seed(seed):
    models={}; arms={}
    for arm,augmented in (("balanced_control",False),("targeted_augmented",True)):
        models[arm],arms[arm]=train_arm(seed,augmented)
    if arms["balanced_control"]["initial_state_sha256"]!=arms["targeted_augmented"]["initial_state_sha256"]:
        raise RuntimeError("paired_initialization_mismatch")
    suites={}
    for name,is_shifted in (("iid_control",False),("near_boundary_shift",True)):
        rows=rows_for_suite(seed,is_shifted); add_decisions(rows,models)
        suites[name]={"rows":rows}
    brows=boundary_rows().tolist(); boundary=[]
    for x in brows:
        rec={"x":[float(v) for v in x],"y":int(teacher(torch.tensor(x).unsqueeze(0))[0])}
        add_decisions([rec],models); boundary.append(rec)
    invalid=[]
    for name,meta,x in invalid_inputs():
        rec={"case":name,"meta":meta,"x":["NaN" if math.isnan(float(v)) else float(v) for v in x]}
        for arm,model in models.items():
            p,reason=proposal(meta,x,model); rec[arm]={"proposal":p,"reason":reason}
        invalid.append(rec)
    latency={}
    probe=balanced_class(1,2000,seed+300)
    for arm,model in models.items():
        timings=[]
        for x in probe:
            start=time.perf_counter_ns(); proposal(META,x,model)
            timings.append((time.perf_counter_ns()-start)/1e6)
        latency[arm]=timings
    return {"seed":seed,"arms":arms,"suites":suites,"boundary":boundary,
            "invalid_controls":invalid,"latency_ms":latency}


def generate_result():
    torch.use_deterministic_algorithms(True); torch.set_num_threads(1)
    return {"allocation":"needle-intent-distill-3458-pilot-09-disjoint-strata",
            "issue":4469,"issue_contract_sha256":ISSUE_CONTRACT_SHA256,
            "training_contract":{"architecture":"6->16->16->3 tanh MLP",
              "optimizer":"AdamW","lr":.008,"steps":STEPS,"batch_size":64,
              "arms":["balanced_control","targeted_augmented"],"device":"CPU"},
            "scope":"synthetic authority-neutral proposals; no execution authority",
            "seeds":[run_seed(seed) for seed in SEEDS]}
