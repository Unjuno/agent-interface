#!/usr/bin/env python3
import argparse, hashlib, json, math, os, platform, resource, statistics, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

TASK='LOCAL-SYSTEM1-LATENCY-AWARE-EARLY-EXIT-20260917-001'
INPUT_DIM=64
NUM_EXEC=6
NUM_CLASSES=7
YIELD_CLASS=6
WIDTH=512
DEPTH=4
TRAIN_N=8192
ORD_N=2048
STRESS_N=2048
EPOCHS=8
BATCH=256
LR=2e-3
AUX_WEIGHT=0.25
LAM_BASE=0.0
LAM_FAST=0.15
HALT_THRESHOLD=0.5
CONF_THRESHOLD=0.65
TEACHER_MARGIN=0.35
COSTS=torch.tensor([0.25,0.50,0.75,1.0],dtype=torch.float32)
FORMAL_SEEDS=[8891701,8891702,8891703,8891704]
WARMUP=128
TIMING_N=1024


def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

class Teacher:
    def __init__(self):
        g=np.random.default_rng(889001)
        self.w1=(g.normal(size=(INPUT_DIM,96))/math.sqrt(INPUT_DIM)).astype(np.float32)
        self.b1=(g.normal(scale=.2,size=(96,))).astype(np.float32)
        self.w2=(g.normal(size=(96,NUM_EXEC))/math.sqrt(96)).astype(np.float32)
        self.lin=(g.normal(size=(INPUT_DIM,NUM_EXEC))/math.sqrt(INPUT_DIM)).astype(np.float32)
    def labels(self,x):
        h=np.tanh(x@self.w1+self.b1)
        s=h@self.w2 + 0.35*(x@self.lin)
        order=np.argsort(s,axis=1)
        top=order[:,-1]
        margin=s[np.arange(len(s)),order[:,-1]]-s[np.arange(len(s)),order[:,-2]]
        y=top.astype(np.int64)
        y[margin<TEACHER_MARGIN]=YIELD_CLASS
        return y

TEACHER=Teacher()

def make_data(seed,n,stress=False):
    g=np.random.default_rng(seed)
    x=g.normal(size=(n,INPUT_DIM)).astype(np.float32)
    if stress:
        x[:,:16]*=1.35
        x[:,:8]+=0.35
        x[:,16:24]*=.70
    y=TEACHER.labels(x)
    return x,y

class EarlyExitNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks=nn.ModuleList()
        self.exits=nn.ModuleList()
        self.gates=nn.ModuleList()
        d=INPUT_DIM
        for i in range(DEPTH):
            self.blocks.append(nn.Sequential(nn.Linear(d,WIDTH),nn.GELU()))
            self.exits.append(nn.Linear(WIDTH,NUM_CLASSES))
            if i<DEPTH-1: self.gates.append(nn.Linear(WIDTH,1))
            d=WIDTH
    def forward_all(self,x):
        logits=[]; hazards=[]
        h=x
        for i,b in enumerate(self.blocks):
            h=b(h)
            logits.append(self.exits[i](h))
            if i<DEPTH-1: hazards.append(torch.sigmoid(self.gates[i](h)).squeeze(-1))
        rem=torch.ones_like(hazards[0])
        qs=[]
        for hz in hazards:
            q=rem*hz; qs.append(q); rem=rem*(1-hz)
        qs.append(rem)
        q=torch.stack(qs,dim=1)
        return logits,q,hazards
    @torch.inference_mode()
    def predict_one(self,x):
        h=x
        depth=DEPTH
        for i,b in enumerate(self.blocks):
            h=b(h)
            logits=self.exits[i](h)
            if i<DEPTH-1:
                halt=float(torch.sigmoid(self.gates[i](h)).item())
                if halt>=HALT_THRESHOLD:
                    depth=i+1; break
            else:
                depth=DEPTH
        probs=torch.softmax(logits,dim=-1)
        conf=float(probs.max().item())
        pred=int(probs.argmax().item())
        if conf<CONF_THRESHOLD: pred=YIELD_CLASS
        return pred,depth,conf

def loss_fn(model,x,y,lam):
    logits,q,_=model.forward_all(x)
    ce=torch.stack([F.cross_entropy(z,y,reduction='none') for z in logits],dim=1)
    expected=(q*ce).sum(1).mean()
    aux=ce.mean()
    comp=(q*COSTS.to(q.device)).sum(1).mean()
    return expected + AUX_WEIGHT*aux + lam*comp, expected.detach(), aux.detach(), comp.detach()

def train_model(seed,lam,init_state,xtrain,ytrain):
    torch.manual_seed(seed)
    model=EarlyExitNet(); model.load_state_dict(init_state)
    opt=torch.optim.AdamW(model.parameters(),lr=LR,weight_decay=1e-4)
    xt=torch.from_numpy(xtrain); yt=torch.from_numpy(ytrain)
    g=torch.Generator().manual_seed(seed+100000)
    t0=time.perf_counter_ns()
    for epoch in range(EPOCHS):
        perm=torch.randperm(TRAIN_N,generator=g)
        for start in range(0,TRAIN_N,BATCH):
            idx=perm[start:start+BATCH]
            loss,_,_,_=loss_fn(model,xt[idx],yt[idx],lam)
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    ms=(time.perf_counter_ns()-t0)/1e6
    return model,ms

def eval_set(model,x,y):
    preds=np.empty(len(x),dtype=np.int16); depths=np.empty(len(x),dtype=np.int8); conf=np.empty(len(x),dtype=np.float32)
    tx=torch.from_numpy(x)
    for i in range(len(x)):
        p,d,c=model.predict_one(tx[i:i+1]); preds[i]=p; depths[i]=d; conf[i]=c
    return preds,depths,conf

def latency(model,x):
    tx=torch.from_numpy(x)
    for i in range(WARMUP): model.predict_one(tx[i%len(x):i%len(x)+1])
    vals=np.empty(TIMING_N,dtype=np.float64)
    for i in range(TIMING_N):
        j=i%len(x); t0=time.perf_counter_ns(); model.predict_one(tx[j:j+1]); vals[i]=(time.perf_counter_ns()-t0)/1e6
    return vals

def pct(a,p): return float(np.percentile(a,p,method='linear'))

def summarize(seed,arm,lam,model,train_ms,xo,yo,xs,ys):
    po,do,co=eval_set(model,xo,yo); ps,ds,cs=eval_set(model,xs,ys)
    lats=latency(model,xo)
    def metrics(y,p,d):
        ty=(y==YIELD_CLASS); unsafe=int(np.sum(ty & (p!=YIELD_CLASS)))
        return {
            'n':int(len(y)),'accuracy':float(np.mean(y==p)),'teacher_yield_n':int(ty.sum()),
            'teacher_yield_to_exec':unsafe,'teacher_yield_to_exec_rate':float(unsafe/max(1,int(ty.sum()))),
            'predicted_yield_n':int(np.sum(p==YIELD_CLASS)),
            'exit_counts':[int(np.sum(d==k)) for k in range(1,DEPTH+1)],
            'mean_depth':float(np.mean(d)),'mean_normalized_compute':float(np.mean(d)/DEPTH)
        }
    state_bytes=sum(v.numel()*v.element_size() for v in model.state_dict().values())
    params=sum(p.numel() for p in model.parameters())
    repx=torch.from_numpy(xo[:1]); a=model.predict_one(repx); b=model.predict_one(repx)
    rep_hash=hashlib.sha256(json.dumps([a,b],sort_keys=True).encode()).hexdigest()
    return {
      'seed':seed,'arm':arm,'lambda':lam,'params':params,'model_bytes':state_bytes,'train_ms':train_ms,
      'ordinary':metrics(yo,po,do),'stress':metrics(ys,ps,ds),
      'latency_ms':{'p50':pct(lats,50),'p95':pct(lats,95),'p99':pct(lats,99),'max':float(lats.max()),'mean':float(lats.mean()),'n':TIMING_N,'decisions_per_s':float(1000.0/lats.mean())},
      'repeat_hash':rep_hash,
      '_raw':{'po':po,'do':do,'co':co,'ps':ps,'ds':ds,'cs':cs,'lats':lats}
    }

def decision(rows):
    by={r['seed']:{} for r in rows}
    for r in rows: by[r['seed']][r['arm']]=r
    reductions=[]; ord_losses=[]; stress_losses=[]; faster=0; comp_better=0; violations=[]
    for s,p in sorted(by.items()):
        b=p['ACCURACY_ONLY']; c=p['LATENCY_AWARE']
        red=1-c['latency_ms']['p95']/b['latency_ms']['p95']; reductions.append(red)
        if c['latency_ms']['p95']<b['latency_ms']['p95']: faster+=1
        if c['ordinary']['mean_normalized_compute']<b['ordinary']['mean_normalized_compute']: comp_better+=1
        ord_losses.append(b['ordinary']['accuracy']-c['ordinary']['accuracy'])
        stress_losses.append(b['stress']['accuracy']-c['stress']['accuracy'])
        if c['ordinary']['accuracy']<.90: violations.append(f'{s}:ordinary_accuracy')
        if c['stress']['accuracy']<.80: violations.append(f'{s}:stress_accuracy')
        if c['ordinary']['teacher_yield_to_exec_rate']>b['ordinary']['teacher_yield_to_exec_rate']+.005: violations.append(f'{s}:yield_safety')
        if c['ordinary']['predicted_yield_n']==0: violations.append(f'{s}:yield_unreachable')
    medred=float(np.median(reductions)); medol=float(np.median(ord_losses)); medsl=float(np.median(stress_losses))
    gates={'median_p95_reduction':medred,'faster_pairs':faster,'median_ordinary_loss_pp':medol*100,'median_stress_loss_pp':medsl*100,'compute_better_pairs':comp_better,'violations':violations}
    if not violations and medred>=.20 and faster>=3 and medol<=.015 and medsl<=.025 and comp_better>=3:
        disp='PASS_LATENCY_AWARE_EARLY_EXIT_SCOPED'
    elif comp_better>=3 and medred<.20:
        disp='NO_MEASURED_LATENCY_EFFECT'
    elif comp_better>=3 or medred>0:
        disp='HOLD_LATENCY_OBJECTIVE_TRADEOFF_NOT_CLOSED'
    else:
        disp='REJECT_LATENCY_OBJECTIVE'
    return disp,gates

def environment():
    return {'python':sys.version,'platform':platform.platform(),'torch':torch.__version__,'numpy':np.__version__,
            'torch_num_threads':torch.get_num_threads(),'env_threads':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    if args.mode=='construction':
        torch.manual_seed(1); m=EarlyExitNet(); x=torch.zeros(4,INPUT_DIM); y=torch.tensor([0,1,2,6]); loss,*_=loss_fn(m,x,y,LAM_FAST); loss.backward()
        print(json.dumps({'construction':'PASS_MECHANICS','params':sum(p.numel() for p in m.parameters()),'finite_loss':bool(torch.isfinite(loss)),'heads':DEPTH,'classes':NUM_CLASSES},sort_keys=True)); return
    rows=[]; raw={}
    for seed in FORMAL_SEEDS:
        xtr,ytr=make_data(seed,TRAIN_N,False); xo,yo=make_data(seed+10000,ORD_N,False); xs,ys=make_data(seed+20000,STRESS_N,True)
        torch.manual_seed(seed+50000); init=EarlyExitNet().state_dict()
        init={k:v.clone() for k,v in init.items()}
        for arm,lam in [('ACCURACY_ONLY',LAM_BASE),('LATENCY_AWARE',LAM_FAST)]:
            model,tms=train_model(seed,lam,init,xtr,ytr)
            r=summarize(seed,arm,lam,model,tms,xo,yo,xs,ys); raw[(seed,arm)]=r.pop('_raw'); rows.append(r)
    disp,gates=decision(rows)
    result={'task':TASK,'formal_invocations':1,'formal_reruns':0,'decision':disp,'gates':gates,'config':{
       'input_dim':INPUT_DIM,'classes':NUM_CLASSES,'yield_class':YIELD_CLASS,'width':WIDTH,'depth':DEPTH,'train_n':TRAIN_N,'ordinary_n':ORD_N,'stress_n':STRESS_N,'epochs':EPOCHS,'batch':BATCH,'lr':LR,'aux_weight':AUX_WEIGHT,'lambda_base':LAM_BASE,'lambda_fast':LAM_FAST,'halt_threshold':HALT_THRESHOLD,'confidence_threshold':CONF_THRESHOLD,'teacher_margin':TEACHER_MARGIN,'warmup':WARMUP,'timing_n':TIMING_N,'seeds':FORMAL_SEEDS},'environment':environment(),'rows':rows,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    npz={}
    for (seed,arm),d in raw.items():
      pre=f'{seed}_{arm}'
      for k,v in d.items(): npz[f'{pre}_{k}']=v
    np.savez_compressed(out/'EVIDENCE.npz',**npz)
    print(json.dumps({'decision':disp,'result':str(out/'RESULT.json'),'evidence':str(out/'EVIDENCE.npz')},sort_keys=True))

if __name__=='__main__': main()
