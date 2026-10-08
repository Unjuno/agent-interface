"""Frozen five-seed rank-capacity online LoRA experiment on local CUDA GPU."""
import base64, copy, gzip, hashlib, io, json, math, platform, statistics, time
import torch
from torch import nn

SEEDS=(3451,3452,3453,3454,3455)
D,H,C=8,16,4
NBASE,NSUPPORT,NTEST=512,16,4096
BASE_STEPS,PER_FEEDBACK=400,8
LR_BASE,LR_ADAPTER=.025,.04
EPOCH=1

def data(n,seed,device):
    g=torch.Generator(device="cpu").manual_seed(seed)
    return torch.randn(n,D,generator=g).to(device)
def labels(x,flip=False):
    a=(x[:,0]>0).long()
    if flip:a=1-a
    return a*2+(x[:,1]>0).long()
class Core(nn.Module):
    def __init__(self):
        super().__init__(); self.enc=nn.Sequential(nn.Linear(D,H),nn.Tanh()); self.head=nn.Linear(H,C)
    def forward(self,x):return self.head(self.enc(x))
class LoRA(nn.Module):
    def __init__(self,core,rank):
        super().__init__(); self.core=core
        for p in core.parameters():p.requires_grad_(False)
        self.a=nn.Parameter(torch.randn(H,rank,device=next(core.parameters()).device)*.04)
        self.b=nn.Parameter(torch.zeros(rank,C,device=next(core.parameters()).device))
        self.rank=rank
    def forward(self,x):
        h=self.core.enc(x); return self.core.head(h)+(h@self.a@self.b)/self.rank
def clone_state(m):return {k:v.detach().clone() for k,v in m.state_dict().items()}
def same_state(m,s):
    q=m.state_dict()
    return list(q)==list(s) and all(q[k].dtype==s[k].dtype and q[k].shape==s[k].shape and torch.equal(q[k],s[k]) for k in s)
def train_base(m,x,y,seed):
    o=torch.optim.AdamW(m.parameters(),lr=LR_BASE); g=torch.Generator(device="cpu").manual_seed(seed+10)
    m.train()
    for _ in range(BASE_STEPS):
        ix=torch.randint(len(x),(32,),generator=g).to(x.device); loss=nn.functional.cross_entropy(m(x[ix]),y[ix])
        o.zero_grad(set_to_none=True);loss.backward();o.step()
def update(m,o,x,y,seen,g):
    m.train(); inds=torch.tensor(seen,dtype=torch.long,device=x.device)
    for _ in range(PER_FEEDBACK):
        j=torch.randint(len(seen),(32,),generator=g).to(x.device); loss=nn.functional.cross_entropy(m(x[inds[j]]),y[inds[j]])
        o.zero_grad(set_to_none=True);loss.backward();o.step()
def eval_rows(m,x,y):
    m.eval()
    with torch.no_grad():p=m(x).argmax(-1)
    return {"correct":int((p==y).sum()),"n":len(y),"expected":y.cpu().tolist(),"predictions":p.cpu().tolist()}
def dispatch(role,epoch,version,base,registry):
    if type(epoch)is not int or epoch!=EPOCH:return "YIELD",None
    if role=="A" and version==0:return "PROPOSE",base
    if role not in registry or type(version)is not int or version!=16:return "YIELD",None
    return "PROPOSE",registry[role]
def pct95(xs):return sorted(xs)[math.ceil(.95*len(xs))-1]
def state_roundtrip_rollback(m,initial):
    b=io.BytesIO();torch.save(clone_state(m),b);learned=clone_state(m);payload=b.getvalue()
    restored=torch.load(io.BytesIO(payload),map_location="cpu",weights_only=True)
    m.load_state_dict(restored);rt=same_state(m,learned)
    ib=io.BytesIO();torch.save(initial,ib);m.load_state_dict(torch.load(io.BytesIO(ib.getvalue()),map_location="cpu",weights_only=True))
    rb=same_state(m,initial)
    return {"roundtrip_exact":rt,"rollback_exact":rb,"initial_sha256":hashlib.sha256(ib.getvalue()).hexdigest(),"learned_sha256":hashlib.sha256(payload).hexdigest(),"learned_bytes":len(payload)}
def one_seed(seed,device):
    torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    xa=data(NBASE,seed+1,device); xb=data(NSUPPORT,seed+2,device)
    ea=data(NTEST,seed+3,device); eb=data(NTEST,seed+4,device)
    ya,yb,eya,eyb=labels(xa),labels(xb,True),labels(ea),labels(eb,True)
    base=Core().to(device);base_before=None
    o=torch.optim.AdamW(base.parameters(),lr=LR_BASE);g=torch.Generator(device="cpu").manual_seed(seed+10)
    base.train()
    for _ in range(BASE_STEPS):
        ix=torch.randint(NBASE,(32,),generator=g).to(device);loss=nn.functional.cross_entropy(base(xa[ix]),ya[ix])
        o.zero_grad(set_to_none=True);loss.backward();o.step()
    base_before=clone_state(base)
    arm={}
    timings={}
    # rank2 online, rank4 online, rank4 batch: paired init per rank.
    for rank,name in ((2,"rank2_online"),(4,"rank4_online"),(4,"rank4_batch")):
        torch.manual_seed(seed+20+rank)
        if device.type=="cuda":torch.cuda.manual_seed_all(seed+20+rank)
        m=LoRA(base,rank).to(device);initial=clone_state(m);opt=torch.optim.AdamW([m.a,m.b],lr=LR_ADAPTER)
        feedback_order=torch.randperm(NSUPPORT,generator=torch.Generator(device="cpu").manual_seed(seed+30)).tolist()
        lat=[];seen=[];rng=torch.Generator(device="cpu").manual_seed(seed+31+rank)
        if name=="rank4_batch":
            seen=feedback_order.copy(); t0=time.perf_counter_ns()
            for _ in range(NSUPPORT*PER_FEEDBACK):
                ix=torch.randint(len(seen),(32,),generator=rng).to(device); ids=torch.tensor(seen,device=device)
                loss=nn.functional.cross_entropy(m(xb[ids[ix]]),yb[ids[ix]]);opt.zero_grad(set_to_none=True);loss.backward();opt.step()
            lat=[(time.perf_counter_ns()-t0)/1e6]
        else:
            for row in feedback_order:
                seen.append(row);t0=time.perf_counter_ns();update(m,opt,xb,yb,seen,rng);lat.append((time.perf_counter_ns()-t0)/1e6)
        timings[name]=lat
        arm[name]=m
        if name=="rank4_online":snap=state_roundtrip_rollback(m,initial)
    registry=arm
    out={}
    for role,model,x,y,version in (("A",base,ea,eya,0),("rank2_online",arm["rank2_online"],eb,eyb,16),("rank4_online",arm["rank4_online"],eb,eyb,16),("rank4_batch",arm["rank4_batch"],eb,eyb,16)):
        route,selected=dispatch(role,EPOCH,version,base,registry)
        if route!="PROPOSE" or selected is not model:raise RuntimeError("valid dispatch did not select frozen model:"+role)
        out[role]=eval_rows(selected,x,y)
    invalid={
      "unknown_role":dispatch("unknown",EPOCH,16,base,registry)[0],
      "stale_epoch":dispatch("rank4_online",EPOCH-1,16,base,registry)[0],
      "wrong_version":dispatch("rank4_online",EPOCH,15,base,registry)[0],
      "missing_adapter":dispatch("missing",EPOCH,16,base,registry)[0],
      "missing_epoch":dispatch("rank4_online",None,16,base,registry)[0]}
    return {"seed":seed,"metrics":out,"feedback_ms":timings,"snapshot":snap,"base_immutable":same_state(base,base_before),"invalid_routes":invalid}
def main():
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    if not torch.cuda.is_available():raise RuntimeError("STOP_GPU_UNAVAILABLE")
    dev=torch.device("cuda:0");torch.cuda.synchronize(dev);torch.cuda.reset_peak_memory_stats(dev)
    rows=[one_seed(s,dev) for s in SEEDS];torch.cuda.synchronize(dev)
    rawobj={"allocation":"needle-lora-3441-rank4-online-multiseed-gpu-v1","environment":{"platform":platform.platform(),"python":platform.python_version(),"torch":torch.__version__,"cuda":torch.version.cuda,"device":torch.cuda.get_device_name(dev),"torch_threads":torch.get_num_threads(),"deterministic":torch.are_deterministic_algorithms_enabled(),"cublas_workspace_config":"4096:8","peak_allocated_bytes":torch.cuda.max_memory_allocated(dev)},"seeds":rows}
    raw=json.dumps(rawobj,sort_keys=True,separators=(",",":")).encode(); blob=gzip.compress(raw,mtime=0)
    print(json.dumps({"sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw),"gzip_b64":base64.b64encode(blob).decode(),"summary":{"seeds":[{"seed":r["seed"],"rank2":r["metrics"]["rank2_online"]["correct"]/NTEST,"rank4_online":r["metrics"]["rank4_online"]["correct"]/NTEST,"rank4_batch":r["metrics"]["rank4_batch"]["correct"]/NTEST} for r in rows]}},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
