"""Issue 3851 matched-seed CUDA experiment; only the rank-4 online minibatch RNG stream changes."""
import base64, gzip, hashlib, io, json, math, platform, time
import torch
from torch import nn

SEEDS=(3451,3452,3453,3454,3455)
D,H,C=8,16,4
NBASE,NSUPPORT,NTEST=512,16,4096
BASE_STEPS,PER_FEEDBACK=400,8
LR_BASE,LR_ADAPTER=.025,.04
EPOCH,VERSION=1,16
ROLES=("rank4_legacy_seed35","rank4_shared_seed31")

def data(n,seed,device):
    g=torch.Generator(device="cpu").manual_seed(seed)
    return torch.randn(n,D,generator=g).to(device)

def labels(x,flip=False):
    a=(x[:,0]>0).long()
    if flip:a=1-a
    return a*2+(x[:,1]>0).long()

def pack2(xs):
    vals=[int(x) for x in xs]
    if len(vals)%4 or any(x<0 or x>3 for x in vals):raise ValueError("invalid pack2 input")
    return bytes((vals[i]<<6)|(vals[i+1]<<4)|(vals[i+2]<<2)|vals[i+3] for i in range(0,len(vals),4))

def digest_state(state):
    h=hashlib.sha256()
    for k,v in state.items():
        t=v.detach().to("cpu").contiguous()
        h.update(k.encode());h.update(str(t.dtype).encode());h.update(str(tuple(t.shape)).encode());h.update(t.numpy().tobytes())
    return h.hexdigest()

def digest_tensor(value):
    t=value.detach().to("cpu").contiguous()
    h=hashlib.sha256();h.update(str(t.dtype).encode());h.update(str(tuple(t.shape)).encode());h.update(t.numpy().tobytes())
    return h.hexdigest()

class Core(nn.Module):
    def __init__(self):
        super().__init__();self.enc=nn.Sequential(nn.Linear(D,H),nn.Tanh());self.head=nn.Linear(H,C)
    def forward(self,x):return self.head(self.enc(x))

class LoRA(nn.Module):
    def __init__(self,core,rank=4):
        super().__init__();self.core=core
        for p in core.parameters():p.requires_grad_(False)
        dev=next(core.parameters()).device
        self.a=nn.Parameter(torch.randn(H,rank,device=dev)*.04)
        self.b=nn.Parameter(torch.zeros(rank,C,device=dev));self.rank=rank
    def forward(self,x):
        h=self.core.enc(x);return self.core.head(h)+(h@self.a@self.b)/self.rank

def clone_state(m):return {k:v.detach().clone() for k,v in m.state_dict().items()}
def same_state(m,state):
    now=m.state_dict()
    return list(now)==list(state) and all(now[k].dtype==state[k].dtype and now[k].shape==state[k].shape and torch.equal(now[k],state[k]) for k in state)

def train_base(m,x,y,seed):
    opt=torch.optim.AdamW(m.parameters(),lr=LR_BASE)
    rng=torch.Generator(device="cpu").manual_seed(seed+10)
    m.train()
    for _ in range(BASE_STEPS):
        ix=torch.randint(len(x),(32,),generator=rng).to(x.device)
        loss=nn.functional.cross_entropy(m(x[ix]),y[ix])
        opt.zero_grad(set_to_none=True);loss.backward();opt.step()

def dispatch(role,epoch,version,registry):
    if type(epoch)is not int or epoch!=EPOCH:return "YIELD",None
    if role=="A" and type(version)is int and version==0 and "A" in registry:return "PROPOSE",registry["A"]
    if role not in ROLES or type(version)is not int or version!=VERSION:return "YIELD",None
    if role not in registry:return "YIELD",None
    return "PROPOSE",registry[role]

def predict(role,model,registry,x,y):
    route_version=0 if role=="A" else VERSION
    decision,chosen=dispatch(role,EPOCH,route_version,registry)
    if decision!="PROPOSE" or chosen is not model:raise RuntimeError("valid_route_mismatch:"+role)
    chosen.eval()
    with torch.no_grad():pred=chosen(x).argmax(-1).to("cpu").tolist()
    exp=y.to("cpu").tolist();packed=pack2(pred);correct=sum(a==b for a,b in zip(exp,pred))
    return {"decision":decision,"requested_role":role,"selected_adapter":role,"epoch":EPOCH,"version":route_version,
        "correct":correct,"n":len(exp),"accuracy":correct/len(exp),
        "predicted_b64":base64.b64encode(packed).decode(),"predicted_sha256":hashlib.sha256(packed).hexdigest()}

def stream_schedule(order,seed,offset):
    rng=torch.Generator(device="cpu").manual_seed(seed+offset)
    seen=[];schedule=[]
    for row in order:
        seen.append(row)
        for _ in range(PER_FEEDBACK):
            j=torch.randint(len(seen),(32,),generator=rng).tolist()
            schedule.append([seen[k] for k in j])
    flat=bytes(v for batch in schedule for v in batch)
    return schedule,hashlib.sha256(flat).hexdigest()

def update_one(model,opt,x,y,seen_rows,batch_rows):
    ids=torch.tensor(seen_rows,dtype=torch.long,device=x.device)
    bix=torch.tensor(batch_rows,dtype=torch.long,device=x.device)
    loss=nn.functional.cross_entropy(model(x[ids[bix]]),y[ids[bix]])
    opt.zero_grad(set_to_none=True);loss.backward();opt.step()

def one_seed(seed,index):
    device=torch.device("cuda:0")
    torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    xa=data(NBASE,seed+1,device);xb=data(NSUPPORT,seed+2,device)
    ea=data(NTEST,seed+3,device);eb=data(NTEST,seed+4,device)
    ya,yb,eya,eyb=labels(xa),labels(xb,True),labels(ea),labels(eb,True)
    base=Core().to(device);train_base(base,xa,ya,seed);base_before=clone_state(base)
    base_initial_sha=digest_state(base_before)
    # Match #3807 rank-4 adapter initialization exactly (CPU and CUDA seeds).
    torch.manual_seed(seed+24);torch.cuda.manual_seed_all(seed+24)
    template=LoRA(base,4).to(device);initial=clone_state(template)
    initial_sha=digest_state(initial)
    order=torch.randperm(NSUPPORT,generator=torch.Generator(device="cpu").manual_seed(seed+30)).tolist()
    arm_specs=[("rank4_legacy_seed35",35),("rank4_shared_seed31",31)]
    if index%2:arm_specs.reverse()
    arms={};arm_order=[]
    for role,offset in arm_specs:
        torch.manual_seed(seed+24);torch.cuda.manual_seed_all(seed+24)
        torch.cuda.synchronize();started=time.perf_counter_ns();model=LoRA(base,4).to(device);model.load_state_dict(initial)
        torch.cuda.synchronize();adapter_setup_ms=(time.perf_counter_ns()-started)/1e6
        initial_state_exact=same_state(model,initial)
        initial_state=clone_state(model)
        torch.cuda.synchronize();opt_started=time.perf_counter_ns();opt=torch.optim.AdamW([model.a,model.b],lr=LR_ADAPTER)
        torch.cuda.synchronize();optimizer_setup_ms=(time.perf_counter_ns()-opt_started)/1e6
        schedule,schedule_sha256=stream_schedule(order,seed,offset)
        seen=[];curves=[];timings=[]
        for count,row in enumerate(order,start=1):
            seen.append(row);model.train();torch.cuda.synchronize();t0=time.perf_counter_ns()
            for step in range(PER_FEEDBACK):
                update_one(model,opt,xb,yb,seen,schedule[(count-1)*PER_FEEDBACK+step])
            torch.cuda.synchronize();timings.append((time.perf_counter_ns()-t0)/1e6)
            route=predict(role,model,{role:model},eb,eyb)
            packed=base64.b64decode(route["predicted_b64"],validate=True)
            curves.append({"feedback_seen":count,"metrics":route,
                "predicted_sha256":hashlib.sha256(packed).hexdigest()})
        arms[role]={"model":model,"initial_state":initial_state,"initial_state_exact":initial_state_exact,"initial_sha256":initial_sha,
            "adapter_setup_ms":adapter_setup_ms,"optimizer_setup_ms":optimizer_setup_ms,
            "sampler_schedule_sha256":schedule_sha256,"feedback_ms":timings,"curve":curves}
        arm_order.append(role)
    registry={r:arms[r]["model"] for r in ROLES}
    # Retain full per-row predictions at each feedback milestone; final curve point is final metric.
    registry["A"]=base
    final={r:predict(r,registry[r],registry,eb,eyb) for r in ROLES}
    base_route={"role":"A","epoch":EPOCH,"version":0,"decision":"PROPOSE"}
    base_metric=predict("A",base,registry,ea,eya)
    base_route.update(base_metric)
    # Exact full-state serialization round trip and rollback on the shared-stream intervention.
    target=registry["rank4_shared_seed31"];learned=clone_state(target);initial_target=arms["rank4_shared_seed31"]["initial_state"]
    initial_target={k:v.detach().clone() for k,v in initial_target.items()}
    buf=io.BytesIO();torch.save(learned,buf);serialized=buf.getvalue()
    restored=torch.load(io.BytesIO(serialized),map_location="cpu",weights_only=True)
    target.load_state_dict(restored);roundtrip=same_state(target,learned)
    target.load_state_dict(initial);rollback=same_state(target,initial)
    invalid={"unknown_role":dispatch("unknown",EPOCH,VERSION,registry)[0],
      "stale_epoch":dispatch(ROLES[0],EPOCH-1,VERSION,registry)[0],
      "wrong_version":dispatch(ROLES[0],EPOCH,VERSION-1,registry)[0],
      "missing_adapter":dispatch(ROLES[0],EPOCH,VERSION,{})[0],
      "missing_epoch":dispatch(ROLES[0],None,VERSION,registry)[0]}
    return {"seed":seed,"arm_order":arm_order,"feedback_order":order,
      "base_A":base_route,"base_initial_sha256":base_initial_sha,"base_immutable":same_state(base,base_before),
      "data_sha256":{"base_x":digest_tensor(xa),"base_y":digest_tensor(ya),"support_x":digest_tensor(xb),
        "support_y":digest_tensor(yb),"heldout_A_x":digest_tensor(ea),"heldout_A_y":digest_tensor(eya),
        "heldout_B_x":digest_tensor(eb),"heldout_B_y":digest_tensor(eyb)},
      "expected_B_labels_b64":base64.b64encode(pack2(eyb.tolist())).decode(),
      "expected_B_labels_sha256":hashlib.sha256(pack2(eyb.tolist())).hexdigest(),
      "initial_adapter_sha256":initial_sha,"final":final,
      "arms":{r:{k:v for k,v in arms[r].items() if k not in ("model","initial_state")} for r in ROLES},
      "snapshot":{"roundtrip_exact":roundtrip,"rollback_exact":rollback,
        "initial_sha256":digest_state(initial_target),"learned_sha256":digest_state(learned),"serialized_sha256":hashlib.sha256(serialized).hexdigest(),"bytes":len(serialized)},
      "invalid_routes":invalid}

def main():
    if not torch.cuda.is_available():raise RuntimeError("STOP_GPU_UNAVAILABLE")
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    device=torch.device("cuda:0");torch.cuda.synchronize(device);torch.cuda.reset_peak_memory_stats(device)
    records=[one_seed(seed,i) for i,seed in enumerate(SEEDS)]
    torch.cuda.synchronize(device)
    out={"allocation":"needle-lora-3441-rank4-minibatch-seed-paired-v1",
      "seeds":list(SEEDS),"environment":{"platform":platform.platform(),"python":platform.python_version(),
      "torch":torch.__version__,"cuda":torch.version.cuda,"device":torch.cuda.get_device_name(device),
      "threads":torch.get_num_threads(),"deterministic":torch.are_deterministic_algorithms_enabled(),
      "tf32":False,"cublas_workspace_config":__import__("os").environ.get("CUBLAS_WORKSPACE_CONFIG"),
      "peak_allocated_bytes":torch.cuda.max_memory_allocated(device)},
      "frozen_design":{"base_rows":NBASE,"support_rows":NSUPPORT,"heldout_rows":NTEST,
      "base_steps":BASE_STEPS,"updates_per_arrival":PER_FEEDBACK,"total_updates":NSUPPORT*PER_FEEDBACK,
      "arms":list(ROLES),"seeds":list(SEEDS)},"records":records}
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    print(json.dumps({"result_sha256":hashlib.sha256(raw).hexdigest(),"result_bytes":len(raw),
      "result_gzip_b64":base64.b64encode(gzip.compress(raw,mtime=0)).decode()},sort_keys=True))

if __name__=="__main__":main()

