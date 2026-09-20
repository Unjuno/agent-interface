import copy, json, random, statistics, time
import torch
from torch import nn

SEED, D, H, C = 3441, 8, 16, 4
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

def acc(m,x,y):
    m.eval()
    with torch.no_grad(): return (m(x).argmax(-1)==y).float().mean().item()

def latency(m,x):
    vals=[]; m.eval()
    for _ in range(5):
        if x.device.type=='cuda': torch.cuda.synchronize(x.device)
        t=time.perf_counter_ns()
        for _ in range(200):
            with torch.no_grad(): m(x[:1])
            if x.device.type=='cuda': torch.cuda.synchronize(x.device)
        vals.append((time.perf_counter_ns()-t)/200e6)
    return {'p50_ms':statistics.median(vals),'p95_ms':max(vals),'repeats_ms':vals}

def route(meta,intent,scope,epoch):
    return 'PROPOSE' if (meta['intent'],meta['scope'],meta['epoch'])==(intent,scope,epoch) else 'YIELD'

def main():
    random.seed(SEED); torch.manual_seed(SEED)
    dev=torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    if dev.type=='cuda': torch.cuda.manual_seed_all(SEED)
    mem={'status':'not_cuda','diagnostic':None}
    if dev.type=='cuda':
        try: torch.cuda.reset_peak_memory_stats(dev); mem['status']='available'
        except RuntimeError as e: mem={'status':'unavailable','diagnostic':f'{type(e).__name__}: {e}'}
    xa,xb,xs,ea,eb=[data(n,SEED+i,dev) for i,(n) in enumerate([(512),(512),(N_SUPPORT),(4096),(4096)],1)]
    ya,yb,ys=target(xa),target(xb,True),target(xs,True); eya,eyb=target(ea),target(eb,True)
    base=Core().to(dev); pre_ms=fit(base,xa,ya,400,.025,SEED+10,dev)
    frozen={k:v.detach().clone() for k,v in base.state_dict().items()}; base_a,base_b=acc(base,ea,eya),acc(base,eb,eyb)
    lora=LoRA(base).to(dev); lora_ms=fit(lora,xs,ys,STEPS,.04,SEED+11,dev); la,lb=acc(lora,ea,eya),acc(lora,eb,eyb)
    full=Core().to(dev); full.load_state_dict(copy.deepcopy(frozen)); full_ms=fit(full,xs,ys,STEPS,.01,SEED+11,dev); fa,fb=acc(full,ea,eya),acc(full,eb,eyb)
    meta={'intent':'flip_x','scope':'four-way-local-choice','epoch':7}
    gates={'match':route(meta,'flip_x','four-way-local-choice',7),'stale':route(meta,'flip_x','four-way-local-choice',8),'wrong_intent':route(meta,'base','four-way-local-choice',7),'wrong_scope':route(meta,'flip_x','unbounded',7)}
    assert gates=={'match':'PROPOSE','stale':'YIELD','wrong_intent':'YIELD','wrong_scope':'YIELD'}
    assert all(torch.equal(base.state_dict()[k],v) for k,v in frozen.items())
    try: peak=torch.cuda.max_memory_allocated(dev) if mem['status']=='available' else None
    except RuntimeError as e: peak=None; mem={'status':'unavailable','diagnostic':f'{type(e).__name__}: {e}'}
    print(json.dumps({'allocation':'needle-lora-3441-pilot-02','decision':'FAIL_OLD_SKILL_PRESERVATION','scope':'synthetic four-way proposal; no vision/GUI/action authority','seed':SEED,'device':{'type':str(dev),'name':torch.cuda.get_device_name(dev) if dev.type=='cuda' else '','torch':torch.__version__,'cuda':torch.version.cuda},'shape':{'features':D,'hidden':H,'classes':C,'support':N_SUPPORT,'steps':STEPS,'rank':2},'metrics':{'pretrain_ms':pre_ms,'base':{'old':base_a,'new_before':base_b},'lora':{'update_ms':lora_ms,'trainable':sum(p.numel() for p in lora.parameters() if p.requires_grad),'old':la,'new':lb,'latency':latency(lora,eb)},'full':{'update_ms':full_ms,'trainable':sum(p.numel() for p in full.parameters()),'old':fa,'new':fb,'latency':latency(full,eb)},'cuda_peak_bytes':peak,'cuda_memory_status':mem},'skill_gate':gates,'base_immutable':True},indent=2,sort_keys=True))

if __name__=='__main__': main()
