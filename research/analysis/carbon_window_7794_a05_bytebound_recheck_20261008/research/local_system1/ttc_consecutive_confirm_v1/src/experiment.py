#!/usr/bin/env python3
import os
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[k]='1'
import argparse, hashlib, json, platform, resource, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

TASK='LOCAL-SYSTEM1-TTC-CONSECUTIVE-CONFIRM-20260917-001'
PARENT_GIT_BLOB='00b9653972c2c0594f8db6bb1cf56ad0f3dd9183'
DEPTH=4; CHUNK=16; WIDTH=256
ACTIONS=6; CONTINUE_LOCAL=6; YIELD=7; CLASSES=8
TRAIN_N=8192; EVAL_N=4096; EPOCHS=8; BATCH=256; LR=2e-3
EXEC_CONF=0.90
ORD_NOISE=0.8; ORD_SIGNAL=8.0; ORD_YIELD=0.15; ORD_DIFF=[0.40,0.30,0.18,0.12]
STR_NOISE=1.0; STR_SIGNAL=7.0; STR_YIELD=0.20; STR_DIFF=[0.25,0.25,0.25,0.25]
PROTO_SEED=905001
FORMAL_SEEDS=[9101701,9101702,9101703,9101704]
WARMUP=256; TIMING_N=4096

_rng=np.random.default_rng(PROTO_SEED)
PROTOS=_rng.normal(size=(ACTIONS,CHUNK)).astype(np.float32)
PROTOS/=np.linalg.norm(PROTOS,axis=1,keepdims=True)

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(a,p): return float(np.percentile(a,p,method='linear'))

def make_data(seed,n,stress=False):
    g=np.random.default_rng(seed)
    noise=STR_NOISE if stress else ORD_NOISE; amp=STR_SIGNAL if stress else ORD_SIGNAL
    yprob=STR_YIELD if stress else ORD_YIELD; dprob=np.asarray(STR_DIFF if stress else ORD_DIFF,dtype=np.float64)
    x=g.normal(scale=noise,size=(n,DEPTH,CHUNK)).astype(np.float32)
    final=np.empty(n,dtype=np.int64); difficulty=np.empty(n,dtype=np.int64)
    for i in range(n):
        if g.random()<yprob: final[i]=YIELD; difficulty[i]=DEPTH
        else:
            d=int(g.choice(np.arange(1,DEPTH+1),p=dprob)); c=int(g.integers(ACTIONS))
            x[i,d-1]+=amp*PROTOS[c]; final[i]=c; difficulty[i]=d
    targets=np.full((n,DEPTH),CONTINUE_LOCAL,dtype=np.int64)
    for d in range(1,DEPTH+1):
        if d==DEPTH: targets[:,d-1]=final
        else:
            ready=(final!=YIELD)&(difficulty<=d); targets[ready,d-1]=final[ready]
    return x,final,difficulty,targets

class TTCNet(nn.Module):
    def __init__(self):
        super().__init__(); self.blocks=nn.ModuleList(); self.heads=nn.ModuleList()
        for d in range(DEPTH):
            inp=CHUNK+(WIDTH if d else 0)
            self.blocks.append(nn.Sequential(nn.Linear(inp,WIDTH),nn.GELU(),nn.Linear(WIDTH,WIDTH),nn.GELU()))
            self.heads.append(nn.Linear(WIDTH,CLASSES))
    def _stage(self,h,x,d):
        inp=x[:,d] if h is None else torch.cat([h,x[:,d]],dim=1)
        h=self.blocks[d](inp); return h,self.heads[d](h)
    def forward_all(self,x):
        h=None; zs=[]
        for d in range(DEPTH): h,z=self._stage(h,x,d); zs.append(z)
        return zs
    @torch.inference_mode()
    def predict_full(self,x):
        h=None; z=None
        for d in range(DEPTH): h,z=self._stage(h,x,d)
        p=int(z.argmax(dim=1).item()); return (YIELD if p==CONTINUE_LOCAL else p),DEPTH
    @torch.inference_mode()
    def predict_direct(self,x):
        h=None
        for d in range(DEPTH):
            h,z=self._stage(h,x,d); probs=torch.softmax(z,dim=1); p=int(probs.argmax(dim=1).item()); conf=float(probs.max().item())
            if d<DEPTH-1:
                if p<ACTIONS and conf>=EXEC_CONF: return p,d+1
                continue
            return (YIELD if p==CONTINUE_LOCAL else p),DEPTH
        raise AssertionError
    @torch.inference_mode()
    def predict_confirm(self,x):
        h=None; prev=None
        for d in range(DEPTH):
            h,z=self._stage(h,x,d); probs=torch.softmax(z,dim=1); p=int(probs.argmax(dim=1).item()); conf=float(probs.max().item())
            if d<DEPTH-1:
                cur=p if (p<ACTIONS and conf>=EXEC_CONF) else None
                if cur is not None and prev==cur: return cur,d+1
                prev=cur
                continue
            return (YIELD if p==CONTINUE_LOCAL else p),DEPTH
        raise AssertionError

def train(seed):
    x,y,d,t=make_data(seed,TRAIN_N,False)
    torch.manual_seed(seed+100000); model=TTCNet(); opt=torch.optim.AdamW(model.parameters(),lr=LR,weight_decay=1e-4)
    X=torch.from_numpy(x); T=torch.from_numpy(t); g=torch.Generator().manual_seed(seed+200000)
    t0=time.perf_counter_ns(); model.train()
    for _ in range(EPOCHS):
        perm=torch.randperm(TRAIN_N,generator=g)
        for s in range(0,TRAIN_N,BATCH):
            ix=perm[s:s+BATCH]; zs=model.forward_all(X[ix]); loss=sum(F.cross_entropy(z,T[ix,j]) for j,z in enumerate(zs))/DEPTH
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    return model,(time.perf_counter_ns()-t0)/1e6

def eval_mode(model,x,y,difficulty,mode):
    fn={'FULL_DEPTH':model.predict_full,'DIRECT_TTC':model.predict_direct,'CONSECUTIVE_CONFIRM':model.predict_confirm}[mode]
    X=torch.from_numpy(x); preds=np.empty(len(x),np.int16); depths=np.empty(len(x),np.int8)
    for i in range(len(x)): preds[i],depths[i]=fn(X[i:i+1])
    teacher_yield=(y==YIELD); required=np.where(teacher_yield,DEPTH,difficulty)
    premature_exec=(depths<required)&(preds<ACTIONS); premature_yield=(depths<required)&(preds==YIELD)
    return {'accuracy':float(np.mean(preds==y)),'teacher_yield_n':int(teacher_yield.sum()),
      'teacher_yield_to_exec':int(np.sum(teacher_yield&(preds<ACTIONS))),
      'teacher_yield_to_exec_rate':float(np.sum(teacher_yield&(preds<ACTIONS))/max(1,int(teacher_yield.sum()))),
      'premature_exec':int(premature_exec.sum()),'premature_exec_rate':float(premature_exec.mean()),
      'premature_yield':int(premature_yield.sum()),'exit_counts':[int(np.sum(depths==k)) for k in range(1,DEPTH+1)],
      'mean_depth':float(depths.mean()),'mean_normalized_compute':float(depths.mean()/DEPTH),'_preds':preds,'_depths':depths}

def time_mode(model,x,mode):
    fn={'FULL_DEPTH':model.predict_full,'DIRECT_TTC':model.predict_direct,'CONSECUTIVE_CONFIRM':model.predict_confirm}[mode]
    X=torch.from_numpy(x)
    for i in range(WARMUP): fn(X[i%len(X):i%len(X)+1])
    vals=np.empty(TIMING_N,dtype=np.float64)
    for i in range(TIMING_N):
        j=i%len(X); t0=time.perf_counter_ns(); fn(X[j:j+1]); vals[i]=(time.perf_counter_ns()-t0)/1e6
    return vals

def summarize(seed,model,train_ms):
    xo,yo,do,_=make_data(seed+10000,EVAL_N,False); xs,ys,ds,_=make_data(seed+20000,EVAL_N,True)
    sets={}; raw={}
    for sn,x,y,d in [('ordinary',xo,yo,do),('stress',xs,ys,ds)]:
        sets[sn]={}; raw[f'{sn}_y']=y; raw[f'{sn}_difficulty']=d
        for mode in ['FULL_DEPTH','DIRECT_TTC','CONSECUTIVE_CONFIRM']:
            m=eval_mode(model,x,y,d,mode); raw[f'{sn}_{mode}_preds']=m.pop('_preds'); raw[f'{sn}_{mode}_depths']=m.pop('_depths'); sets[sn][mode]=m
        fp=raw[f'{sn}_FULL_DEPTH_preds']
        for mode in ['DIRECT_TTC','CONSECUTIVE_CONFIRM']:
            sets[sn][mode]['agreement_with_full']=float(np.mean(fp==raw[f'{sn}_{mode}_preds']))
    order=['DIRECT_TTC','CONSECUTIVE_CONFIRM','FULL_DEPTH'] if seed%2 else ['FULL_DEPTH','CONSECUTIVE_CONFIRM','DIRECT_TTC']
    timing={}
    for mode in order:
        vals=time_mode(model,xo,mode); raw[f'lat_{mode}']=vals
        timing[mode]={'n':TIMING_N,'p50':pct(vals,50),'p95':pct(vals,95),'p99':pct(vals,99),'max':float(vals.max()),'mean':float(vals.mean()),'decisions_per_s':float(1000/vals.mean())}
    rep=torch.from_numpy(xo[:1]); rh=[]
    for fn in [model.predict_direct,model.predict_confirm,model.predict_full]: rh += [fn(rep),fn(rep)]
    return {'seed':seed,'train_ms':train_ms,'ordinary':sets['ordinary'],'stress':sets['stress'],'timing_order':order,'timing_ms':timing,
      'params':sum(p.numel() for p in model.parameters()),'model_bytes':sum(v.numel()*v.element_size() for v in model.state_dict().values()),
      'repeat_hash':sha256_bytes(json.dumps(rh,sort_keys=True).encode()),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'_raw':raw}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['construction','case'],required=True); ap.add_argument('--seed',type=int); ap.add_argument('--out',required=True); a=ap.parse_args()
    torch.set_num_threads(1); torch.set_num_interop_threads(1); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    if a.mode=='construction':
        seq=[(2,.95),(2,.96),(3,.99),(3,.99)]
        prev=None; exit_depth=None
        for d,(p,c) in enumerate(seq,1):
            if d<DEPTH:
                cur=p if p<ACTIONS and c>=EXEC_CONF else None
                if cur is not None and prev==cur: exit_depth=d; break
                prev=cur
        assert exit_depth==2
        print(json.dumps({'construction':'PASS','candidate_earliest_exit_depth':exit_depth,'formal_seed_used':False},sort_keys=True)); return
    if a.seed not in FORMAL_SEEDS: raise SystemExit('invalid frozen seed')
    marker=out/'INVOKED.json'; case=out/'CASE.json'
    if marker.exists() or case.exists(): raise SystemExit('same-ID rerun forbidden')
    marker.write_text(json.dumps({'seed':a.seed,'invocation':1},sort_keys=True)+'\n')
    model,tms=train(a.seed); r=summarize(a.seed,model,tms); raw=r.pop('_raw')
    case.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); np.savez_compressed(out/'CASE_EVIDENCE.npz',**raw)
    print(json.dumps({'seed':a.seed,'case_sha256':sha256_file(case)},sort_keys=True))
if __name__=='__main__': main()
