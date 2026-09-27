"""Paired rank-4 online LoRA comparison: legacy vs shared minibatch RNG."""
import base64, gzip, hashlib, io, json, math, os, platform, statistics, time
import torch
from torch import nn

SEEDS=(3451,3452,3453,3454,3455)
D,H,C=8,16,4
NBASE,NSUPPORT,NTEST=512,16,4096
BASE_STEPS,PER_FEEDBACK=400,8
LR_BASE,LR_ADAPTER=.025,.04
ORDER={3451:("legacy","shared"),3452:("shared","legacy"),3453:("legacy","shared"),3454:("shared","legacy"),3455:("legacy","shared")}
ALLOCATION="needle-lora-3441-rank4-minibatch-rng-paired-v1"

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
    def __init__(self,core,rank=4):
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
def task_b_labels_cpu(seed,n):
    x=data(n,seed+4,torch.device("cpu"));return labels(x,True)
def dispatch(role,epoch,version,registry):
    if type(epoch)is not int or epoch!=1:return "YIELD",None
    if role not in registry or type(version)is not int or version!=16:return "YIELD",None
    return "PROPOSE",registry[role]
def state_roundtrip_rollback(m,initial):
    b=io.BytesIO();torch.save(clone_state(m),b);learned=clone_state(m);payload=b.getvalue()
    restored=torch.load(io.BytesIO(payload),map_location="cpu",weights_only=True)
    m.load_state_dict(restored);rt=same_state(m,learned)
    ib=io.BytesIO();torch.save(initial,ib);m.load_state_dict(torch.load(io.BytesIO(ib.getvalue()),map_location="cpu",weights_only=True))
    rb=same_state(m,initial)
    return {"roundtrip_exact":rt,"rollback_exact":rb,"initial_sha256":hashlib.sha256(ib.getvalue()).hexdigest(),"learned_sha256":hashlib.sha256(payload).hexdigest(),"learned_bytes":len(payload)}
def train_arm(name,seed,base,xb,yb,feedback_order,initial,device,heldout_x,heldout_y):
    m=LoRA(base,4).to(device);m.load_state_dict(initial)
    initial_copy=clone_state(m)
    opt=torch.optim.AdamW([m.a,m.b],lr=LR_ADAPTER)
    # The sole intervention: frozen CPU generator seed (legacy +35 / shared +31).
    generator_seed=seed+(35 if name=="legacy" else 31)
    g=torch.Generator(device="cpu").manual_seed(generator_seed)
    seen=[]; timings=[]; curves=[]; all_predictions=[]
    for arrival,row in enumerate(feedback_order,1):
        seen.append(row); inds=torch.tensor(seen,dtype=torch.long,device=device)
        if name=="shared": batch_rows=torch.randint(arrival,(PER_FEEDBACK,32),generator=g)
        t0=time.perf_counter_ns()
        m.train()
        for step in range(PER_FEEDBACK):
            if name=="legacy": j=torch.randint(len(seen),(32,),generator=g)
            else: j=batch_rows[step,:arrival]
            j=j.to(device)
            loss=nn.functional.cross_entropy(m(xb[inds[j]]),yb[inds[j]])
            opt.zero_grad(set_to_none=True);loss.backward();opt.step()
        torch.cuda.synchronize(device);timings.append((time.perf_counter_ns()-t0)/1e6)
        # Retain full held-out predictions at every feedback arrival.
        m.eval()
        with torch.no_grad(): pred=m(heldout_x).argmax(-1)
        expected=heldout_y
        correct=int((pred==expected).sum())
        all_predictions.append({"arrival":arrival,"expected":expected.cpu().tolist(),"predictions":pred.cpu().tolist(),"correct":correct,"n":NTEST})
        curves.append({"feedback_seen":arrival,"correct":correct,"n":NTEST,"accuracy":correct/NTEST})
    snap=state_roundtrip_rollback(m,initial_copy)
    return m,timings,curves,all_predictions,snap,hashlib.sha256(torch.cat([initial_copy["a"].flatten(),initial_copy["b"].flatten()]).cpu().numpy().tobytes()).hexdigest()

def one_seed(seed,device):
    torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    xa=data(NBASE,seed+1,device);xb=data(NSUPPORT,seed+2,device)
    ea=data(NTEST,seed+3,device);eb=data(NTEST,seed+4,device)
    ya,yb,eya,eyb=labels(xa),labels(xb,True),labels(ea),labels(eb,True)
    base=Core().to(device);train_base(base,xa,ya,seed);base_before=clone_state(base)
    torch.manual_seed(seed+24);torch.cuda.manual_seed_all(seed+24)
    initial_model=LoRA(base,4).to(device);initial=clone_state(initial_model)
    feedback_order=torch.randperm(NSUPPORT,generator=torch.Generator(device="cpu").manual_seed(seed+30)).tolist()
    arms={};metrics={};timings={};curves={};predictions={};snapshots={};start_hashes={}
    for name in ORDER[seed]:
        model,lat,curve,preds,snap,start_hash=train_arm(name,seed,base,xb,yb,feedback_order,initial,device,eb,eyb)
        arms[name]=model;timings[name]=lat;curves[name]=curve;predictions[name]=preds;snapshots[name]=snap
        start_hashes[name]=start_hash
    for role,model,x,y,version in (("A",base,ea,eya,0),("legacy",arms["legacy"],eb,eyb,16),("shared",arms["shared"],eb,eyb,16)):
        if role=="A":
            model.eval()
            with torch.no_grad():p=model(x).argmax(-1)
            ev={"correct":int((p==y).sum()),"n":len(y),"expected":y.cpu().tolist(),"predictions":p.cpu().tolist()}
        else: ev=eval_rows(model,x,y)
        route,selected=dispatch(role,1,version,{"legacy":arms["legacy"],"shared":arms["shared"]}) if role!="A" else ("PROPOSE",base)
        if route!="PROPOSE" or selected is not model:raise RuntimeError("valid dispatch mismatch:"+role)
        metrics[role]=dict(ev,decision=route,requested_role=role,epoch=1,version=version,selected_adapter=role)
    expected_b=task_b_labels_cpu(seed,NTEST).tolist()
    metrics["legacy"]["expected_b"]=expected_b
    metrics["shared"]["expected_b"]=expected_b
    invalid={"unknown_role":dispatch("unknown",1,16,arms)[0],"stale_epoch":dispatch("legacy",0,16,arms)[0],"wrong_version":dispatch("legacy",1,15,arms)[0],"missing_adapter":dispatch("missing",1,16,arms)[0]}
    for n in ("legacy","shared"):
        metrics[n]["curve"]=curves[n];metrics[n]["predictions_by_arrival"]=predictions[n]
    return {"seed":seed,"feedback_order":feedback_order,"metrics":metrics,"timing_ms":timings,"snapshots":snapshots,"base_immutable":same_state(base,base_before),"identical_adapter_starts":start_hashes["legacy"]==start_hashes["shared"],"initial_adapter_sha256":start_hashes,"invalid_routes":invalid}
def main():
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") not in (":4096:8",":16:8"):raise RuntimeError("STOP_CUBLAS_WORKSPACE_CONFIG")
    if not torch.cuda.is_available():raise RuntimeError("STOP_GPU_UNAVAILABLE")
    dev=torch.device("cuda:0");torch.cuda.synchronize(dev);torch.cuda.reset_peak_memory_stats(dev)
    rows=[one_seed(s,dev) for s in SEEDS];torch.cuda.synchronize(dev)
    rawobj={"allocation":ALLOCATION,"environment":{"platform":platform.platform(),"python":platform.python_version(),"torch":torch.__version__,"cuda":torch.version.cuda,"device":torch.cuda.get_device_name(dev),"torch_threads":torch.get_num_threads(),"deterministic":torch.are_deterministic_algorithms_enabled(),"cublas_workspace_config":os.environ["CUBLAS_WORKSPACE_CONFIG"],"peak_allocated_bytes":torch.cuda.max_memory_allocated(dev)},"seeds":rows}
    raw=json.dumps(rawobj,sort_keys=True,separators=(",",":")).encode();blob=gzip.compress(raw,mtime=0)
    print(json.dumps({"sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw),"gzip_b64":base64.b64encode(blob).decode(),"summary":{"seeds":[{"seed":r["seed"],"legacy":r["metrics"]["legacy"]["correct"]/NTEST,"shared":r["metrics"]["shared"]["correct"]/NTEST} for r in rows]}},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
