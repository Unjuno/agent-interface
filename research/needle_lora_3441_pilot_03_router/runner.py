"""Successor allocation: task-keyed skill routing and immutable adapter snapshot."""
import hashlib, io, json, random, statistics, time
import torch
from torch import nn

SEED, D, H, C = 3442, 8, 16, 4
N_SUPPORT, STEPS = 16, 120

def data(n, seed, device):
    return torch.randn(n, D, generator=torch.Generator().manual_seed(seed)).to(device)

def target(x, flip=False):
    b=(x[:,0]>0).long()
    if flip: b=1-b
    return b*2+(x[:,1]>0).long()

class Core(nn.Module):
    def __init__(self):
        super().__init__(); self.enc=nn.Sequential(nn.Linear(D,H),nn.Tanh()); self.head=nn.Linear(H,C)
    def forward(self,x): return self.head(self.enc(x))

class LoRA(nn.Module):
    def __init__(self,core):
        super().__init__(); self.core=core
        for p in core.parameters(): p.requires_grad_(False)
        self.a=nn.Parameter(torch.randn(H,2)*.04); self.b=nn.Parameter(torch.zeros(2,C))
    def forward(self,x):
        h=self.core.enc(x); return self.core.head(h)+(h@self.a@self.b)/2

def fit(model,x,y,steps,lr,seed,device):
    opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=lr)
    g=torch.Generator().manual_seed(seed); model.train(); t=time.perf_counter_ns()
    for _ in range(steps):
        ix=torch.randint(len(x),(32,),generator=g).to(device); loss=nn.functional.cross_entropy(model(x[ix]),y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    if device.type=='cuda': torch.cuda.synchronize(device)
    return (time.perf_counter_ns()-t)/1e6

def acc(model,x,y):
    model.eval()
    with torch.no_grad(): return (model(x).argmax(-1)==y).float().mean().item()

def dispatch(skill,metadata,epoch,base,adapter):
    if metadata.get('epoch') != epoch: return 'YIELD', None
    if skill == 'base': return 'PROPOSE', base
    if skill == 'flip_x' and metadata.get('adapter_version') == 1: return 'PROPOSE', adapter
    return 'YIELD', None

def main():
    random.seed(SEED); torch.manual_seed(SEED)
    dev=torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    if dev.type=='cuda': torch.cuda.manual_seed_all(SEED)
    xa,xb,xs,ea,eb=[data(n,SEED+i,dev) for i,n in enumerate([512,512,N_SUPPORT,4096,4096],1)]
    ya,yb,ys=target(xa),target(xb,True),target(xs,True); eya,eyb=target(ea),target(eb,True)
    base=Core().to(dev); pre_ms=fit(base,xa,ya,400,.025,SEED+10,dev)
    base_state={k:v.detach().clone() for k,v in base.state_dict().items()}
    base_old=acc(base,ea,eya)
    adapter=LoRA(base).to(dev)
    initial=io.BytesIO(); torch.save({k:v.detach().cpu().clone() for k,v in adapter.state_dict().items()},initial)
    initial_bytes=initial.getvalue(); initial_sha=hashlib.sha256(initial_bytes).hexdigest()
    update_ms=fit(adapter,xs,ys,STEPS,.04,SEED+11,dev)
    learned_bytes=io.BytesIO(); torch.save({k:v.detach().cpu().clone() for k,v in adapter.state_dict().items()},learned_bytes)
    learned_payload=learned_bytes.getvalue(); learned_sha=hashlib.sha256(learned_payload).hexdigest()
    results={}
    for skill,x,y,meta in [('base',ea,eya,{'epoch':9}),('flip_x',eb,eyb,{'epoch':9,'adapter_version':1})]:
        decision,model=dispatch(skill,meta,9,base,adapter)
        assert decision=='PROPOSE' and model is not None
        results[skill]=acc(model,x,y)
    global_old,global_new=acc(adapter,ea,eya),acc(adapter,eb,eyb)
    bad={
      'unknown_skill':dispatch('not_registered',{'epoch':9,'adapter_version':1},9,base,adapter)[0],
      'stale_epoch':dispatch('flip_x',{'epoch':8,'adapter_version':1},9,base,adapter)[0],
      'wrong_version':dispatch('flip_x',{'epoch':9,'adapter_version':2},9,base,adapter)[0],
      'wrong_metadata':dispatch('flip_x',{'epoch':9},9,base,adapter)[0],
    }
    assert bad=={k:'YIELD' for k in bad}
    restored=torch.load(io.BytesIO(learned_payload),map_location=dev,weights_only=True)
    adapter.load_state_dict(restored)
    assert hashlib.sha256(learned_payload).hexdigest()==learned_sha
    assert acc(adapter,eb,eyb)==global_new
    rollback=torch.load(io.BytesIO(initial_bytes),map_location=dev,weights_only=True)
    adapter.load_state_dict(rollback)
    rolled_new=acc(adapter,eb,eyb)
    assert hashlib.sha256(initial_bytes).hexdigest()==initial_sha
    assert all(torch.equal(base.state_dict()[k],v) for k,v in base_state.items())
    timings=[]
    for _ in range(5):
        if dev.type=='cuda': torch.cuda.synchronize(dev)
        t=time.perf_counter_ns()
        for _ in range(200): dispatch('flip_x',{'epoch':9,'adapter_version':1},9,base,adapter)
        if dev.type=='cuda': torch.cuda.synchronize(dev)
        timings.append((time.perf_counter_ns()-t)/200e6)
    print(json.dumps({
      'allocation':'needle-lora-3441-pilot-03-skill-router','seed':SEED,'device':{'type':str(dev),'name':torch.cuda.get_device_name(dev) if dev.type=='cuda' else '','torch':torch.__version__,'cuda':torch.version.cuda},
      'metrics':{'pretrain_ms':pre_ms,'update_ms':update_ms,'base_old_accuracy':base_old,'global_adapter_accuracy':{'old':global_old,'new':global_new},'routed_accuracy':results,'rollback_new_skill_accuracy':rolled_new,'router_200_call_block_means_ms':timings,'router_block_mean_p50_ms':statistics.median(timings),'adapter_state_bytes':len(learned_payload),'initial_snapshot_sha256':initial_sha,'learned_snapshot_sha256':learned_sha},
      'invalid_routes':bad,'snapshot_roundtrip_exact':True,'rollback_completed':True,'base_immutable':True,'scope':'synthetic only; dispatcher grants proposal selection only, not action authority'
    },indent=2,sort_keys=True))

if __name__=='__main__': main()
