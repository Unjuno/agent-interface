#!/usr/bin/env python3
import os
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[k]='1'
import argparse, hashlib, json, math, platform, resource, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

TASK='LOCAL-SYSTEM1-DIRECT-TTC-20260917-001'
DEPTH=4; CHUNK=16; WIDTH=256
ACTIONS=6; CONTINUE_LOCAL=6; YIELD=7; CLASSES=8
TRAIN_N=8192; EVAL_N=4096; EPOCHS=8; BATCH=256; LR=2e-3
EXEC_CONF=0.90
ORD_NOISE=0.8; ORD_SIGNAL=8.0; ORD_YIELD=0.15; ORD_DIFF=[0.40,0.30,0.18,0.12]
STR_NOISE=1.0; STR_SIGNAL=7.0; STR_YIELD=0.20; STR_DIFF=[0.25,0.25,0.25,0.25]
PROTO_SEED=905001
FORMAL_SEEDS=[9051701,9051702,9051703,9051704]
WARMUP=256; TIMING_N=4096

_rng=np.random.default_rng(PROTO_SEED)
PROTOS=_rng.normal(size=(ACTIONS,CHUNK)).astype(np.float32)
PROTOS/=np.linalg.norm(PROTOS,axis=1,keepdims=True)

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def pct(a,p): return float(np.percentile(a,p,method='linear'))

def make_data(seed,n,stress=False):
    g=np.random.default_rng(seed)
    noise=STR_NOISE if stress else ORD_NOISE
    amp=STR_SIGNAL if stress else ORD_SIGNAL
    yprob=STR_YIELD if stress else ORD_YIELD
    dprob=np.asarray(STR_DIFF if stress else ORD_DIFF,dtype=np.float64)
    x=g.normal(scale=noise,size=(n,DEPTH,CHUNK)).astype(np.float32)
    final=np.empty(n,dtype=np.int64); difficulty=np.empty(n,dtype=np.int64)
    for i in range(n):
        if g.random()<yprob:
            final[i]=YIELD; difficulty[i]=DEPTH
        else:
            d=int(g.choice(np.arange(1,DEPTH+1),p=dprob)); c=int(g.integers(ACTIONS))
            x[i,d-1]+=amp*PROTOS[c]
            final[i]=c; difficulty[i]=d
    targets=np.full((n,DEPTH),CONTINUE_LOCAL,dtype=np.int64)
    for d in range(1,DEPTH+1):
        if d==DEPTH:
            targets[:,d-1]=final
        else:
            ready=(final!=YIELD)&(difficulty<=d)
            targets[ready,d-1]=final[ready]
    return x,final,difficulty,targets

class TTCNet(nn.Module):
    def __init__(self):
        super().__init__(); self.blocks=nn.ModuleList(); self.heads=nn.ModuleList()
        for d in range(DEPTH):
            inp=CHUNK+(WIDTH if d else 0)
            self.blocks.append(nn.Sequential(nn.Linear(inp,WIDTH),nn.GELU(),nn.Linear(WIDTH,WIDTH),nn.GELU()))
            self.heads.append(nn.Linear(WIDTH,CLASSES))
    def forward_all(self,x):
        h=None; zs=[]
        for d in range(DEPTH):
            inp=x[:,d] if h is None else torch.cat([h,x[:,d]],dim=1)
            h=self.blocks[d](inp); zs.append(self.heads[d](h))
        return zs
    @torch.inference_mode()
    def predict_full(self,x):
        h=None; z=None
        for d in range(DEPTH):
            inp=x[:,d] if h is None else torch.cat([h,x[:,d]],dim=1)
            h=self.blocks[d](inp); z=self.heads[d](h)
        p=int(z.argmax(dim=1).item())
        return (YIELD if p==CONTINUE_LOCAL else p),DEPTH
    @torch.inference_mode()
    def predict_ttc(self,x):
        h=None
        for d in range(DEPTH):
            inp=x[:,d] if h is None else torch.cat([h,x[:,d]],dim=1)
            h=self.blocks[d](inp); z=self.heads[d](h)
            probs=torch.softmax(z,dim=1); p=int(probs.argmax(dim=1).item()); conf=float(probs.max().item())
            if d<DEPTH-1:
                if p<ACTIONS and conf>=EXEC_CONF:
                    return p,d+1
                continue
            return (YIELD if p==CONTINUE_LOCAL else p),DEPTH
        raise AssertionError('unreachable')

def train(seed):
    x,y,d,t=make_data(seed,TRAIN_N,False)
    torch.manual_seed(seed+100000)
    model=TTCNet()
    opt=torch.optim.AdamW(model.parameters(),lr=LR,weight_decay=1e-4)
    X=torch.from_numpy(x); T=torch.from_numpy(t)
    g=torch.Generator().manual_seed(seed+200000)
    t0=time.perf_counter_ns()
    model.train()
    for _ in range(EPOCHS):
        perm=torch.randperm(TRAIN_N,generator=g)
        for s in range(0,TRAIN_N,BATCH):
            ix=perm[s:s+BATCH]; zs=model.forward_all(X[ix])
            loss=sum(F.cross_entropy(z,T[ix,j]) for j,z in enumerate(zs))/DEPTH
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    train_ms=(time.perf_counter_ns()-t0)/1e6
    return model,train_ms

def eval_mode(model,x,y,difficulty,mode):
    fn=model.predict_full if mode=='FULL_DEPTH' else model.predict_ttc
    X=torch.from_numpy(x); preds=np.empty(len(x),np.int16); depths=np.empty(len(x),np.int8)
    for i in range(len(x)):
        p,d=fn(X[i:i+1]); preds[i]=p; depths[i]=d
    teacher_yield=(y==YIELD)
    required=np.where(teacher_yield,DEPTH,difficulty)
    premature_exec=(depths<required)&(preds<ACTIONS)
    premature_yield=(depths<required)&(preds==YIELD)
    return {
        'accuracy':float(np.mean(preds==y)),
        'teacher_yield_n':int(teacher_yield.sum()),
        'teacher_yield_to_exec':int(np.sum(teacher_yield&(preds<ACTIONS))),
        'teacher_yield_to_exec_rate':float(np.sum(teacher_yield&(preds<ACTIONS))/max(1,int(teacher_yield.sum()))),
        'premature_exec':int(premature_exec.sum()),
        'premature_exec_rate':float(premature_exec.mean()),
        'premature_yield':int(premature_yield.sum()),
        'exit_counts':[int(np.sum(depths==k)) for k in range(1,DEPTH+1)],
        'mean_depth':float(depths.mean()),
        'mean_normalized_compute':float(depths.mean()/DEPTH),
        '_preds':preds,'_depths':depths,
    }

def time_mode(model,x,mode):
    fn=model.predict_full if mode=='FULL_DEPTH' else model.predict_ttc
    X=torch.from_numpy(x)
    for i in range(WARMUP): fn(X[i%len(X):i%len(X)+1])
    vals=np.empty(TIMING_N,dtype=np.float64)
    for i in range(TIMING_N):
        j=i%len(X); t0=time.perf_counter_ns(); fn(X[j:j+1]); vals[i]=(time.perf_counter_ns()-t0)/1e6
    return vals

def summarize_seed(seed,model,train_ms):
    xo,yo,do,_=make_data(seed+10000,EVAL_N,False)
    xs,ys,ds,_=make_data(seed+20000,EVAL_N,True)
    evals={}
    raw={}
    for setname,x,y,d in [('ordinary',xo,yo,do),('stress',xs,ys,ds)]:
        for mode in ['FULL_DEPTH','DIRECT_TTC']:
            m=eval_mode(model,x,y,d,mode); raw[f'{setname}_{mode}_preds']=m.pop('_preds'); raw[f'{setname}_{mode}_depths']=m.pop('_depths')
            evals[(setname,mode)]=m
        fp=raw[f'{setname}_FULL_DEPTH_preds']; ap=raw[f'{setname}_DIRECT_TTC_preds']
        evals[(setname,'DIRECT_TTC')]['agreement_with_full']=float(np.mean(fp==ap))
    order=['DIRECT_TTC','FULL_DEPTH'] if seed%2 else ['FULL_DEPTH','DIRECT_TTC']
    timing={}
    for mode in order:
        vals=time_mode(model,xo,mode); raw[f'lat_{mode}']=vals
        timing[mode]={'n':TIMING_N,'p50':pct(vals,50),'p95':pct(vals,95),'p99':pct(vals,99),'max':float(vals.max()),'mean':float(vals.mean()),'decisions_per_s':float(1000.0/vals.mean())}
    params=sum(p.numel() for p in model.parameters()); model_bytes=sum(v.numel()*v.element_size() for v in model.state_dict().values())
    rep=torch.from_numpy(xo[:1]); a=model.predict_ttc(rep); b=model.predict_ttc(rep); c=model.predict_full(rep); d=model.predict_full(rep)
    return {
        'seed':seed,'train_ms':train_ms,'params':params,'model_bytes':model_bytes,'timing_order':order,
        'ordinary':{'FULL_DEPTH':evals[('ordinary','FULL_DEPTH')],'DIRECT_TTC':evals[('ordinary','DIRECT_TTC')]},
        'stress':{'FULL_DEPTH':evals[('stress','FULL_DEPTH')],'DIRECT_TTC':evals[('stress','DIRECT_TTC')]},
        'timing_ms':timing,
        'repeat_hash':sha256_bytes(json.dumps([a,b,c,d],sort_keys=True).encode()),
        '_raw':raw,
    }

def decide(rows):
    violations=[]; mean_red=[]; p50_red=[]; faster=0; p95_reg=[]
    for r in rows:
        s=r['seed']; o=r['ordinary']; st=r['stress']; tf=r['timing_ms']['FULL_DEPTH']; ta=r['timing_ms']['DIRECT_TTC']
        for setname,m,amin in [('ordinary',o,.98),('stress',st,.94)]:
            if m['FULL_DEPTH']['accuracy']<amin: violations.append(f'{s}:{setname}:full_accuracy')
            if m['DIRECT_TTC']['accuracy']<amin: violations.append(f'{s}:{setname}:ttc_accuracy')
            agree_min=.99 if setname=='ordinary' else .98
            if m['DIRECT_TTC']['agreement_with_full']<agree_min: violations.append(f'{s}:{setname}:agreement')
            delta=m['DIRECT_TTC']['teacher_yield_to_exec_rate']-m['FULL_DEPTH']['teacher_yield_to_exec_rate']
            if delta>.0025+1e-12: violations.append(f'{s}:{setname}:yield_exec_delta')
            if m['DIRECT_TTC']['premature_yield']!=0: violations.append(f'{s}:{setname}:premature_yield')
        if o['DIRECT_TTC']['premature_exec']!=0: violations.append(f'{s}:ordinary:premature_exec')
        if st['DIRECT_TTC']['premature_exec_rate']>.001+1e-12: violations.append(f'{s}:stress:premature_exec')
        if o['DIRECT_TTC']['mean_normalized_compute']>.70: violations.append(f'{s}:ordinary:compute')
        if st['DIRECT_TTC']['mean_normalized_compute']>.80: violations.append(f'{s}:stress:compute')
        used=sum(1 for c in o['DIRECT_TTC']['exit_counts'] if c>0)
        if used<3: violations.append(f'{s}:exit_diversity')
        mr=1-ta['mean']/tf['mean']; pr=1-ta['p50']/tf['p50']; rr=ta['p95']/tf['p95']-1
        mean_red.append(mr); p50_red.append(pr); p95_reg.append(rr)
        if ta['mean']<tf['mean']: faster+=1
        if rr>.10: violations.append(f'{s}:p95_regression')
    med_mean=float(np.median(mean_red)); med_p50=float(np.median(p50_red))
    competence=not any(('full_accuracy' in v) for v in violations)
    correctness=not any(any(k in v for k in ['ttc_accuracy','agreement','yield_exec_delta','premature_yield','premature_exec']) for v in violations)
    speed_ok=med_mean>=.25 and med_p50>=.25 and faster>=3
    compute_ok=not any(('compute' in v or 'exit_diversity' in v) for v in violations)
    if competence and correctness and speed_ok and compute_ok and not any('p95_regression' in v for v in violations): dec='PASS_DIRECT_TTC_SCOPED'
    elif not competence: dec='HOLD_COMPETENCE_NOT_CLOSED'
    elif not correctness: dec='HOLD_TTC_SAFETY_OR_TRANSFER'
    elif compute_ok and not speed_ok: dec='NO_REALIZED_TTC_SPEEDUP'
    else: dec='HOLD_TTC_SAFETY_OR_TRANSFER'
    return dec,{'median_mean_latency_reduction':med_mean,'median_p50_latency_reduction':med_p50,'adaptive_mean_faster_pairs':faster,'p95_regressions':p95_reg,'violations':violations}

def environment():
    return {'python':sys.version,'platform':platform.platform(),'torch':torch.__version__,'numpy':np.__version__,'torch_num_threads':torch.get_num_threads(),'cpu_count':os.cpu_count(),'thread_env':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    if a.mode=='construction':
        x,y,d,t=make_data(9059001,32,False); m=TTCNet(); zs=m.forward_all(torch.from_numpy(x)); loss=sum(F.cross_entropy(z,torch.from_numpy(t[:,j])) for j,z in enumerate(zs))/DEPTH; loss.backward()
        assert t[(d>1)&(y!=YIELD),0].tolist().count(CONTINUE_LOCAL)>=0
        print(json.dumps({'construction':'PASS','params':sum(p.numel() for p in m.parameters()),'finite_loss':bool(torch.isfinite(loss)),'external_vocab':list(range(ACTIONS))+[YIELD],'internal_continue':CONTINUE_LOCAL},sort_keys=True)); return
    rows=[]; archive={}
    for seed in FORMAL_SEEDS:
        model,train_ms=train(seed); r=summarize_seed(seed,model,train_ms); raw=r.pop('_raw'); rows.append(r)
        for k,v in raw.items(): archive[f'{seed}_{k}']=v
        (out/f'CASE_{seed}.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    dec,gates=decide(rows)
    result={'task':TASK,'formal_invocations':1,'formal_reruns':0,'decision':dec,'gates':gates,'config':{
        'depth':DEPTH,'chunk':CHUNK,'width':WIDTH,'actions':ACTIONS,'continue_local':CONTINUE_LOCAL,'yield':YIELD,'train_n':TRAIN_N,'eval_n':EVAL_N,'epochs':EPOCHS,'batch':BATCH,'lr':LR,'exec_conf':EXEC_CONF,
        'ordinary':{'noise':ORD_NOISE,'signal':ORD_SIGNAL,'yield_prob':ORD_YIELD,'difficulty':ORD_DIFF},'stress':{'noise':STR_NOISE,'signal':STR_SIGNAL,'yield_prob':STR_YIELD,'difficulty':STR_DIFF},'prototype_seed':PROTO_SEED,'formal_seeds':FORMAL_SEEDS,'warmup':WARMUP,'timing_n':TIMING_N},
        'environment':environment(),'rows':rows,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    np.savez_compressed(out/'EVIDENCE.npz',**archive)
    print(json.dumps({'decision':dec,'result':str(out/'RESULT.json'),'evidence':str(out/'EVIDENCE.npz')},sort_keys=True))
if __name__=='__main__': main()
