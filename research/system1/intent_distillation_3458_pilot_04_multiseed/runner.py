"""Three-seed confirmatory run of the frozen hybrid Needle margin mechanism."""
import io, json, random, statistics, time
import torch
from torch import nn

SEEDS=(3461,3462,3463)
LABELS={0:'CONTINUE',1:'CORRECT',2:'WATCH'}
N_TRAIN_PER_CLASS,N_TEST_PER_CLASS=2048,1024
META={'intent':'track_target','scope':'local-servo','epoch':7}

def balanced_class(label,n,seed):
    g=torch.Generator().manual_seed(seed)
    if label==0:
        xy=(torch.rand(n,2,generator=g)-.5)*.08; velocity=(torch.rand(n,2,generator=g)-.5)*.08
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
    with torch.no_grad(): return ('CONTINUE','CORRECT','WATCH')[int(model(x.unsqueeze(0)).argmax(-1).item())]

def boundary_set():
    rows=[]
    for i in range(256):
        d=.25+(i%17)*.001
        rows.extend([[d,.2,.01,.02,.719,1.],[d,.2,.01,.02,.721,1.]])
        rows.extend([[.059,0.,.02,.02,.9,1.],[.061,0.,.02,.02,.9,1.]])
        rows.extend([[0.,0.,.059,.06,.9,1.],[0.,0.,.061,.06,.9,1.]])
    x=torch.tensor(rows,dtype=torch.float32); return x

def percentile_ms(fn,rows):
    vals=[]
    for row in rows:
        t=time.perf_counter_ns(); fn(row); vals.append((time.perf_counter_ns()-t)/1e6)
    vals.sort(); return {'p50':statistics.median(vals),'p95':vals[int(.95*(len(vals)-1))],'p99':vals[int(.99*(len(vals)-1))],'n':len(vals)}

def run(seed):
    random.seed(seed); torch.manual_seed(seed)
    train_x=torch.cat([balanced_class(c,N_TRAIN_PER_CLASS,seed+10+c) for c in range(3)]); train_y=oracle(train_x)
    test_x=torch.cat([balanced_class(c,N_TEST_PER_CLASS,seed+20+c) for c in range(3)]); test_y=oracle(test_x)
    model=Needle(); opt=torch.optim.AdamW(model.parameters(),lr=.008); g=torch.Generator().manual_seed(seed+30)
    model.train(); start=time.perf_counter_ns()
    for _ in range(700):
        ix=torch.randint(len(train_x),(64,),generator=g); loss=nn.functional.cross_entropy(model(train_x[ix]),train_y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    train_ms=(time.perf_counter_ns()-start)/1e6; model.eval()
    accepted=[]; pred=[]
    for x,y in zip(test_x,test_y):
        out=hybrid(META,x,model)
        if out!='YIELD':
            accepted.append(y); pred.append({'CONTINUE':0,'CORRECT':1,'WATCH':2}[out])
    accepted_y=torch.stack(accepted); p=torch.tensor(pred)
    by_class={('CONTINUE','CORRECT','WATCH')[c]:{'accepted':int((accepted_y==c).sum()),'coverage':float((accepted_y==c).sum()/N_TEST_PER_CLASS),'recall':float(((accepted_y==c)&(p==c)).sum()/max(1,(accepted_y==c).sum()))} for c in range(3)}
    false_correct=int(((p==1)&(accepted_y!=1)).sum())
    boundaries=boundary_set(); b_yields=sum(hybrid(META,x,model)=='YIELD' for x in boundaries)
    state=io.BytesIO(); torch.save(model.state_dict(),state)
    return {'seed':seed,'train_ms':train_ms,'accepted':len(accepted),'coverage':len(accepted)/len(test_x),'accepted_accuracy':float((p==accepted_y).float().mean()),'per_class':by_class,'false_CORRECT':false_correct,'boundary_yield':b_yields,'boundary_total':len(boundaries),'state_bytes':len(state.getvalue()),'cpu_latency_ms':percentile_ms(lambda x:hybrid(META,x,model),test_x[:2000])}

def main():
    results=[run(s) for s in SEEDS]
    print(json.dumps({'allocation':'needle-intent-distill-3458-pilot-04-multiseed','seeds':list(SEEDS),'runs':results,'all_boundary_yield':all(r['boundary_yield']==r['boundary_total'] for r in results),'scope':'synthetic hybrid proposal only; no action authority'},indent=2,sort_keys=True))

if __name__=='__main__': main()
