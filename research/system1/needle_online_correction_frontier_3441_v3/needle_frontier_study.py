import argparse, itertools, json, time
import torch
from torch import nn

SEEDS=(67117,67229,67341); N=256; ARRIVALS=32; WIDTH=16

class Net(nn.Module):
    def __init__(self):
        super().__init__(); self.l1=nn.Linear(8,WIDTH); self.l2=nn.Linear(WIDTH,4)
    def forward(self,x): return self.l2(torch.tanh(self.l1(x)))

class Candidate(nn.Module):
    def __init__(self,base,seed):
        super().__init__(); self.base=base; self.a=nn.Parameter(torch.empty(4,2)); self.b=nn.Parameter(torch.zeros(2,WIDTH))
        g=torch.Generator().manual_seed(seed); self.a.data.copy_(torch.randn((4,2),generator=g)*0.02)
        for p in self.base.parameters(): p.requires_grad_(False)
    def forward(self,x):
        h=torch.tanh(self.base.l1(x)); return self.base.l2(h)+(h@self.b.T@self.a.T)*0.25

def datasets(seed):
    g=torch.Generator().manual_seed(seed+190001)
    def heldout():
        x=torch.rand((N,8),generator=g); x[:N//2,0]=0.; x[N//2:,0]=1.
        return x[torch.randperm(N,generator=g)]
    xa=heldout(); xb=heldout(); ya=xa[:,0].long(); yb=1-xb[:,0].long()
    # Binary task feature, continuous nuisance features: unique fixed support rows.
    support=[]
    for _ in range(ARRIVALS):
        batch=torch.rand((8,8),generator=g);batch[:4,0]=0.;batch[4:,0]=1.
        support.append(batch[torch.randperm(8,generator=g)])
    support=torch.stack(support);sy=1-support[:,:,0].long()
    return xa,ya,xb,yb,support,sy

def guard(model,x,scope,epoch):
    if scope!="B" or epoch!=11: return {"decision":"YIELD","logits":None}
    with torch.no_grad(): return {"decision":"PROPOSE","logits":model(x).tolist()}

def copy_state(module): return {k:v.detach().clone() for k,v in module.state_dict().items()}
def state_lists(sd): return {k:v.tolist() for k,v in sd.items()}
def tensor_from(d): return {k:torch.tensor(v,dtype=torch.float32) for k,v in d.items()}

def run():
    torch.set_num_threads(1); results=[]
    for seed in SEEDS:
        xa,ya,xb,yb,sx,sy=datasets(seed); torch.manual_seed(seed+1); base=Net(); opt=torch.optim.AdamW(base.parameters(),lr=0.03)
        base_t=time.perf_counter_ns()
        for step in range(400):
            i=(step*17+seed)%N; opt.zero_grad(set_to_none=True); loss=nn.functional.cross_entropy(base(xa[i:i+1]),ya[i:i+1]); loss.backward(); opt.step()
        base_ms=(time.perf_counter_ns()-base_t)/1e6; frozen=copy_state(base)
        model=Candidate(base,seed+2); before=copy_state(base); candidate_opt=torch.optim.AdamW([model.a,model.b],lr=0.04)
        snapshots=[]; curve=[]; update_ms=[]
        def eval_at(step):
            with torch.no_grad():
                pa=model(xa);pb=model(xb);la=int((pa.argmax(-1)==ya).sum());lb=int((pb.argmax(-1)==yb).sum());ca=float(nn.functional.cross_entropy(pa,ya));cb=float(nn.functional.cross_entropy(pb,yb))
            curve.append({"step":step,"a_correct":la,"b_correct":lb,"ce_a":ca,"ce_b":cb,"n":N})
            snapshots.append({"a":model.a.detach().tolist(),"b":model.b.detach().tolist()})
        eval_at(0)
        for j in range(ARRIVALS):
            t=time.perf_counter_ns();candidate_opt.zero_grad(set_to_none=True);loss=nn.functional.cross_entropy(model(sx[j]),sy[j]);loss.backward();candidate_opt.step();update_ms.append((time.perf_counter_ns()-t)/1e6);eval_at(j+1)
        with torch.no_grad():
            final_a=model(xa).tolist();final_b=model(xb).tolist();base_a=base(xa).tolist()
        controls=[guard(model,xb[0],"B",11),guard(model,xb[0],"other",11),guard(model,xb[0],"B",10)]
        results.append({"seed":seed,"base_train_ms":base_ms,"x_a":xa.tolist(),"y_a":ya.tolist(),"x_b":xb.tolist(),"y_b":yb.tolist(),"support_x":sx.tolist(),"support_y":sy.tolist(),"curve":curve,"snapshots":snapshots,"update_ms":update_ms,"base_initial":state_lists(before),"base_final":state_lists(copy_state(base)),"base_logits_a":base_a,"candidate_final_logits_a":final_a,"candidate_final_logits_b":final_b,"controls":controls})
    return {"schema":"needle-online-correction-frontier-v2","torch":torch.__version__,"threads":torch.get_num_threads(),"runs":results}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output");args=p.parse_args();doc=run();raw=json.dumps(doc,separators=(",",":"))
    if args.output: open(args.output,"w",encoding="utf-8").write(raw+"\n")
    else: print(raw)

