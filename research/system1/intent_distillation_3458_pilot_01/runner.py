"""Synthetic intent-bounded Needle distillation pilot for Issue #3458."""
import io, json, random, statistics, time
import torch
from torch import nn

SEED=3458
N_TRAIN,N_TEST=8192,4096
LABELS={0:'CONTINUE',1:'CORRECT',2:'WATCH'}

def make_states(n,seed):
    g=torch.Generator().manual_seed(seed)
    xy=torch.randn(n,2,generator=g)*0.62
    velocity=torch.randn(n,2,generator=g)*0.32
    confidence=torch.rand(n,1,generator=g)
    visible=torch.randint(0,2,(n,1),generator=g).float()
    return torch.cat([xy,velocity,confidence,visible],dim=1)

def oracle(x):
    dx,dy,vx,vy,confidence,visible=x.unbind(-1)
    watch=(confidence<0.72)|(visible<0.5)
    settled=(dx.abs()<0.06)&(dy.abs()<0.06)&((vx.abs()+vy.abs())<0.12)
    return torch.where(watch,2,torch.where(settled,0,1)).long()

class Needle(nn.Module):
    def __init__(self):
        super().__init__(); self.net=nn.Sequential(nn.Linear(6,16),nn.Tanh(),nn.Linear(16,16),nn.Tanh(),nn.Linear(16,3))
    def forward(self,x): return self.net(x)

def gate(metadata,expected_intent,expected_scope,epoch,x):
    if (metadata.get('intent')!=expected_intent or metadata.get('scope')!=expected_scope
        or metadata.get('epoch')!=epoch or not torch.isfinite(x).all()): return 'YIELD'
    dx,dy,vx,vy,confidence,visible=x.tolist()
    if max(abs(dx),abs(dy))>1.25 or max(abs(vx),abs(vy))>1.0 or not 0<=confidence<=1 or visible not in (0.0,1.0): return 'YIELD'
    return 'ALLOW_LOCAL_PROPOSAL'

def predict_rule(x): return oracle(x).item()

def measure(fn,rows):
    values=[]
    for row in rows:
        t=time.perf_counter_ns(); fn(row); values.append((time.perf_counter_ns()-t)/1e6)
    s=sorted(values)
    return {'p50_ms':statistics.median(s),'p95_ms':s[int(.95*(len(s)-1))],'p99_ms':s[int(.99*(len(s)-1))],'n':len(s)}

def main():
    random.seed(SEED); torch.manual_seed(SEED)
    train_x=make_states(N_TRAIN,SEED+1); train_y=oracle(train_x)
    test_x=make_states(N_TEST,SEED+2); test_y=oracle(test_x)
    model=Needle(); opt=torch.optim.AdamW(model.parameters(),lr=0.008)
    g=torch.Generator().manual_seed(SEED+3)
    model.train(); started=time.perf_counter_ns()
    for _ in range(700):
        ix=torch.randint(len(train_x),(64,),generator=g); logits=model(train_x[ix]); loss=nn.functional.cross_entropy(logits,train_y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    train_ms=(time.perf_counter_ns()-started)/1e6
    model.eval()
    with torch.no_grad(): pred=model(test_x).argmax(-1)
    correct=int((pred==test_y).sum()); accuracy=correct/len(test_y)
    by_class={LABELS[i]:{'n':int((test_y==i).sum()),'correct':int(((pred==i)&(test_y==i)).sum())} for i in LABELS}
    rule_latency=measure(lambda x:predict_rule(x),test_x[:2000])
    needle_latency=measure(lambda x:int(model(x.unsqueeze(0)).argmax(-1).item()),test_x[:2000])
    gates={
      'exact':gate({'intent':'track_target','scope':'local-servo','epoch':5},'track_target','local-servo',5,test_x[0]),
      'stale':gate({'intent':'track_target','scope':'local-servo','epoch':4},'track_target','local-servo',5,test_x[0]),
      'wrong_intent':gate({'intent':'new_goal','scope':'local-servo','epoch':5},'track_target','local-servo',5,test_x[0]),
      'wrong_scope':gate({'intent':'track_target','scope':'global','epoch':5},'track_target','local-servo',5,test_x[0]),
      'unknown_state':gate({'intent':'track_target','scope':'local-servo','epoch':5},'track_target','local-servo',5,torch.tensor([2.,0.,0.,0.,.9,1.])),
      'nonfinite':gate({'intent':'track_target','scope':'local-servo','epoch':5},'track_target','local-servo',5,torch.tensor([float('nan'),0.,0.,0.,.9,1.])),
    }
    weights=io.BytesIO(); torch.save(model.state_dict(),weights)
    proposed_correct=int(((pred==1)&(test_y==1)).sum()); false_corrections=int(((pred==1)&(test_y!=1)).sum())
    print(json.dumps({'allocation':'needle-intent-distill-3458-pilot-01','seed':SEED,
      'dataset':{'train':N_TRAIN,'test':N_TEST,'features':['dx','dy','vx','vy','confidence','visible']},
      'teacher':'fixed deterministic state-to-CONTINUE/CORRECT/WATCH rule; not Astra labels',
      'model':{'parameters':sum(p.numel() for p in model.parameters()),'state_bytes':len(weights.getvalue()),'hidden':[16,16]},
      'metrics':{'train_ms':train_ms,'accuracy':accuracy,'correct':correct,'by_class':by_class,'false_CORRECT_proposals':false_corrections,'true_CORRECT_proposals':proposed_correct,'rule_cpu_latency':rule_latency,'needle_cpu_latency':needle_latency},
      'authority_gate':gates,'authority_gate_all_invalid_yield':all(v=='YIELD' for k,v in gates.items() if k!='exact'),'scope':'synthetic state proposals only; no action authority'},indent=2,sort_keys=True))

if __name__=='__main__': main()
