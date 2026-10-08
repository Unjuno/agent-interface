"""Hybrid deterministic margin gate + learned Needle interior proposal successor."""
import io, json, random, statistics, time
import torch
from torch import nn

SEED=3460
LABELS={0:'CONTINUE',1:'CORRECT',2:'WATCH'}
N_TRAIN_PER_CLASS,N_TEST_PER_CLASS=2048,1024
META={'intent':'track_target','scope':'local-servo','epoch':7}

def balanced_class(label,n,seed):
    g=torch.Generator().manual_seed(seed)
    if label==0:
        xy=(torch.rand(n,2,generator=g)-.5)*.08
        velocity=(torch.rand(n,2,generator=g)-.5)*.08
        confidence=.72+.28*torch.rand(n,1,generator=g); visible=torch.ones(n,1)
    elif label==1:
        sign=torch.where(torch.rand(n,1,generator=g)>.5,1.,-1.)
        dx=sign*(.15+.80*torch.rand(n,1,generator=g)); dy=(torch.rand(n,1,generator=g)-.5)*1.6
        xy=torch.cat([dx,dy],1); velocity=(torch.rand(n,2,generator=g)-.5)*.4
        confidence=.72+.28*torch.rand(n,1,generator=g); visible=torch.ones(n,1)
    else:
        xy=(torch.rand(n,2,generator=g)-.5)*2.; velocity=(torch.rand(n,2,generator=g)-.5)*.8
        confidence=.72*torch.rand(n,1,generator=g); visible=torch.randint(0,2,(n,1),generator=g).float()
    return torch.cat([xy,velocity,confidence,visible],1)

def oracle(x):
    dx,dy,vx,vy,confidence,visible=x.unbind(-1)
    watch=(confidence<.72)|(visible<.5)
    settled=(dx.abs()<.06)&(dy.abs()<.06)&((vx.abs()+vy.abs())<.12)
    return torch.where(watch,2,torch.where(settled,0,1)).long()

class Needle(nn.Module):
    def __init__(self):
        super().__init__(); self.net=nn.Sequential(nn.Linear(6,16),nn.Tanh(),nn.Linear(16,16),nn.Tanh(),nn.Linear(16,3))
    def forward(self,x): return self.net(x)

def hybrid(meta,x,model):
    if meta!=META or not torch.isfinite(x).all(): return 'YIELD'
    dx,dy,vx,vy,confidence,visible=x.tolist()
    if max(abs(dx),abs(dy))>1.25 or max(abs(vx),abs(vy))>1.0 or not 0<=confidence<=1 or visible not in (0.,1.): return 'YIELD'
    if (abs(confidence-.72)<.03 or abs(abs(dx)-.06)<.01 or abs(abs(dy)-.06)<.01
        or abs(abs(vx)+abs(vy)-.12)<.02): return 'YIELD'
    with torch.no_grad(): return LABELS[int(model(x.unsqueeze(0)).argmax(-1).item())]

def boundary_set():
    rows=[]
    for i in range(256):
        d=.25+(i%17)*.001
        rows.extend([[d,.2,.01,.02,.719,1.],[d,.2,.01,.02,.721,1.]])
        rows.extend([[.059,0.,.02,.02,.9,1.],[.061,0.,.02,.02,.9,1.]])
        rows.extend([[0.,0.,.059,.06,.9,1.],[0.,0.,.061,.06,.9,1.]])
    x=torch.tensor(rows,dtype=torch.float32); return x,oracle(x)

def measure(fn,rows):
    vals=[]
    for row in rows:
        t=time.perf_counter_ns(); fn(row); vals.append((time.perf_counter_ns()-t)/1e6)
    s=sorted(vals)
    return {'p50_ms':statistics.median(s),'p95_ms':s[int(.95*(len(s)-1))],'p99_ms':s[int(.99*(len(s)-1))],'n':len(s)}

def main():
    random.seed(SEED); torch.manual_seed(SEED)
    train_x=torch.cat([balanced_class(c,N_TRAIN_PER_CLASS,SEED+10+c) for c in range(3)]); train_y=oracle(train_x)
    test_x=torch.cat([balanced_class(c,N_TEST_PER_CLASS,SEED+20+c) for c in range(3)]); test_y=oracle(test_x)
    model=Needle(); opt=torch.optim.AdamW(model.parameters(),lr=.008); g=torch.Generator().manual_seed(SEED+30)
    model.train(); start=time.perf_counter_ns()
    for _ in range(700):
        ix=torch.randint(len(train_x),(64,),generator=g); loss=nn.functional.cross_entropy(model(train_x[ix]),train_y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    train_ms=(time.perf_counter_ns()-start)/1e6; model.eval()
    accepted=[]; rejected=[]; pred=[]
    for x,y in zip(test_x,test_y):
        out=hybrid(META,x,model)
        if out=='YIELD': rejected.append((x,y))
        else: accepted.append((x,y)); pred.append({'CONTINUE':0,'CORRECT':1,'WATCH':2}[out])
    accepted_y=torch.stack([y for _,y in accepted]); pred_t=torch.tensor(pred)
    per_class={LABELS[c]:{'n':int(((accepted_y==c)).sum()),'correct':int(((accepted_y==c)&(pred_t==c)).sum()),'recall':float(((accepted_y==c)&(pred_t==c)).sum()/max(1,(accepted_y==c).sum()))} for c in range(3)}
    false_correct=int(((pred_t==1)&(accepted_y!=1)).sum())
    bx,by=boundary_set(); b_out=[hybrid(META,x,model) for x in bx]
    invalid={'stale':hybrid({**META,'epoch':6},test_x[0],model),'unknown_intent':hybrid({**META,'intent':'other'},test_x[0],model),'outside':hybrid(META,torch.tensor([1.5,0.,0.,0.,.9,1.]),model),'nonfinite':hybrid(META,torch.tensor([float('nan'),0.,0.,0.,.9,1.]),model)}
    weights=io.BytesIO(); torch.save(model.state_dict(),weights)
    def path(x): return hybrid(META,x,model)
    print(json.dumps({'allocation':'needle-intent-distill-3458-pilot-03-hybrid','seed':SEED,
      'dataset':{'test_per_class':N_TEST_PER_CLASS,'boundary_cases':len(bx)},
      'model':{'parameters':sum(p.numel() for p in model.parameters()),'state_bytes':len(weights.getvalue()),'train_ms':train_ms},
      'metrics':{'accepted':len(accepted),'coverage':len(accepted)/len(test_x),'coverage_by_class':{LABELS[c]:per_class[LABELS[c]]['n']/N_TEST_PER_CLASS for c in range(3)},'accepted_accuracy':float((pred_t==accepted_y).float().mean()),'accepted_per_class':per_class,'false_CORRECT_proposals':false_correct,'boundary_yield':sum(x=='YIELD' for x in b_out),'boundary_total':len(b_out),'hybrid_cpu_latency':measure(path,test_x[:2000])},
      'invalid_routes':invalid,'all_invalid_yield':all(v=='YIELD' for v in invalid.values()),'scope':'synthetic proposal only; boundary/stale yield; no action authority'},indent=2,sort_keys=True))

if __name__=='__main__': main()
