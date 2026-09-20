"""Frozen rank-4 online half-learning-rate rescue experiment; local CUDA only."""
import base64,gzip,hashlib,io,json,math,platform,statistics,time
import torch
from torch import nn

SEEDS=(3461,3462,3463,3464,3465)
D,H,C=8,16,4
NBASE,NSUPPORT,NTEST=512,16,4096
BASE_STEPS,STEPS_PER_ARRIVAL=400,8
LR_BASE,LR_CONTROL,LR_INTERVENTION=.025,.04,.02
EPOCH=16

def data(n,seed):
    g=torch.Generator(device="cpu").manual_seed(seed)
    return torch.randn(n,D,generator=g)
def labels(x,flip=False):
    a=(x[:,0]>0).long()
    if flip:a=1-a
    return a*2+(x[:,1]>0).long()
class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc=nn.Sequential(nn.Linear(D,H),nn.Tanh())
        self.head=nn.Linear(H,C)
    def forward(self,x):return self.head(self.enc(x))
class LoRA(nn.Module):
    def __init__(self,core,rank):
        super().__init__()
        self.core=core
        for p in core.parameters():p.requires_grad_(False)
        dev=next(core.parameters()).device
        self.a=nn.Parameter(torch.randn(H,rank,device=dev)*.04)
        self.b=nn.Parameter(torch.zeros(rank,C,device=dev))
        self.rank=rank
    def forward(self,x):
        h=self.core.enc(x)
        return self.core.head(h)+(h@self.a@self.b)/self.rank
def clone_state(m):return {k:v.detach().clone() for k,v in m.state_dict().items()}
def state_equal(m,s):
    q=m.state_dict()
    return list(q)==list(s) and all(q[k].dtype==s[k].dtype and q[k].shape==s[k].shape and torch.equal(q[k],s[k]) for k in s)
def sync(dev):
    if dev.type=="cuda":torch.cuda.synchronize(dev)
def base_train(model,x,y,seed,dev):
    opt=torch.optim.AdamW(model.parameters(),lr=LR_BASE)
    g=torch.Generator(device="cpu").manual_seed(seed+10)
    model.train()
    for _ in range(BASE_STEPS):
        ix=torch.randint(NBASE,(32,),generator=g).to(dev)
        loss=nn.functional.cross_entropy(model(x[ix]),y[ix])
        opt.zero_grad(set_to_none=True);loss.backward();opt.step()
def make_schedule(seed):
    order=torch.randperm(NSUPPORT,generator=torch.Generator(device="cpu").manual_seed(seed+30)).tolist()
    g=torch.Generator(device="cpu").manual_seed(seed+31)
    schedule=[]
    for count in range(1,NSUPPORT+1):
        local=torch.randint(count,(STEPS_PER_ARRIVAL,32),generator=g).tolist()
        schedule.append([[order[j] for j in batch] for batch in local])
    return order,schedule
def dispatch(role,epoch,expected_epoch,adapter_id,version,expected_version,base,registry):
    if type(epoch)is not int or epoch!=expected_epoch:return "YIELD",None
    if role=="A":
        return ("PROPOSE",base) if adapter_id=="base" and version==0 else ("YIELD",None)
    expected={"B_R2_ONLINE":"rank2","B_R4_ONLINE_04":"rank4_04",
              "B_R4_ONLINE_02":"rank4_02","B_R4_BATCH_04":"rank4_batch"}
    if role not in expected or adapter_id!=expected[role] or type(version)is not int or version!=expected_version:
        return "YIELD",None
    model=registry.get(role)
    return ("PROPOSE",model) if model is not None else ("YIELD",None)
def train_arrival(model,opt,x,y,batches,dev):
    model.train()
    for row_ids in batches:
        ix=torch.tensor(row_ids,dtype=torch.long,device=dev)
        loss=nn.functional.cross_entropy(model(x[ix]),y[ix])
        opt.zero_grad(set_to_none=True);loss.backward();opt.step()
def eval_predictions(model,x,dev):
    model.eval()
    with torch.no_grad():return model(x).argmax(-1).detach().cpu().tolist()
def metric(pred,expected):
    correct=sum(int(a==b) for a,b in zip(pred,expected))
    return {"correct":correct,"n":len(expected),"accuracy":correct/len(expected),"predictions":pred}
def setup_adapter(base,rank,seed,dev):
    torch.manual_seed(seed)
    if dev.type=="cuda":torch.cuda.manual_seed_all(seed)
    sync(dev);t=time.perf_counter_ns()
    m=LoRA(base,rank).to(dev)
    sync(dev)
    return m,(time.perf_counter_ns()-t)/1e6
def setup_optimizer(model,lr,dev):
    sync(dev);t=time.perf_counter_ns()
    opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=lr)
    sync(dev)
    return opt,(time.perf_counter_ns()-t)/1e6
def snapshot_gate(model,initial):
    learned=clone_state(model)
    bio=io.BytesIO();torch.save(learned,bio);payload=bio.getvalue()
    loaded=torch.load(io.BytesIO(payload),map_location="cpu",weights_only=True)
    model.load_state_dict(loaded)
    roundtrip=state_equal(model,learned)
    initbio=io.BytesIO();torch.save(initial,initbio)
    model.load_state_dict(torch.load(io.BytesIO(initbio.getvalue()),map_location="cpu",weights_only=True))
    rollback=state_equal(model,initial)
    return {"roundtrip_exact":roundtrip,"rollback_exact":rollback,
            "initial_sha256":hashlib.sha256(initbio.getvalue()).hexdigest(),
            "learned_sha256":hashlib.sha256(payload).hexdigest(),"learned_bytes":len(payload)}
def one_seed(seed,dev):
    torch.manual_seed(seed)
    if dev.type=="cuda":torch.cuda.manual_seed_all(seed)
    xbase=data(NBASE,seed+1).to(dev);xsupport=data(NSUPPORT,seed+2).to(dev)
    xa=data(NTEST,seed+3).to(dev);xb=data(NTEST,seed+4).to(dev)
    ybase=labels(data(NBASE,seed+1)).to(dev)
    ysupport=labels(data(NSUPPORT,seed+2),True).to(dev)
    y_a=labels(data(NTEST,seed+3)).tolist()
    y_b=labels(data(NTEST,seed+4),True).tolist()
    base=Core().to(dev);base_train(base,xbase,ybase,seed,dev);base_before=clone_state(base)

    # One rank-4 template is copied tensor-for-tensor to both online LR arms and batch reference.
    r4_template,template_ms=setup_adapter(base,4,seed+24,dev)
    r4_initial=clone_state(r4_template)
    r2,r2_setup=setup_adapter(base,2,seed+22,dev)
    r4_04,r4_04_setup=setup_adapter(base,4,seed+24,dev)
    r4_02,r4_02_setup=setup_adapter(base,4,seed+24,dev)
    r4_batch,r4_batch_setup=setup_adapter(base,4,seed+24,dev)
    init_equal=(state_equal(r4_04,r4_initial) and state_equal(r4_02,r4_initial)
                and state_equal(r4_batch,r4_initial)
                and all(torch.equal(r4_04.state_dict()[k],r4_02.state_dict()[k]) for k in r4_04.state_dict()))
    setups={"rank2_online":r2_setup,"rank4_online_04":r4_04_setup,
            "rank4_online_02":r4_02_setup,"rank4_batch_04":r4_batch_setup,
            "rank4_template":template_ms}
    optimizers={}
    for name,model,lr in (("rank2_online",r2,LR_CONTROL),("rank4_online_04",r4_04,LR_CONTROL),
                          ("rank4_online_02",r4_02,LR_INTERVENTION),("rank4_batch_04",r4_batch,LR_CONTROL)):
        optimizers[name],setups[name+"_optimizer"]=setup_optimizer(model,lr,dev)

    order,schedule=make_schedule(seed)
    models={"rank2_online":r2,"rank4_online_04":r4_04,"rank4_online_02":r4_02}
    curves={k:[] for k in models};timings={k:[] for k in models}
    for count in range(1,NSUPPORT+1):
        for name,model in models.items():
            sync(dev);t=time.perf_counter_ns()
            train_arrival(model,optimizers[name],xsupport,ysupport,schedule[count-1],dev)
            sync(dev);timings[name].append((time.perf_counter_ns()-t)/1e6)
            route,selected=dispatch({"rank2_online":"B_R2_ONLINE","rank4_online_04":"B_R4_ONLINE_04",
                "rank4_online_02":"B_R4_ONLINE_02"}[name],count,count,
                {"rank2_online":"rank2","rank4_online_04":"rank4_04","rank4_online_02":"rank4_02"}[name],
                count,count,base,{ "B_R2_ONLINE":r2,"B_R4_ONLINE_04":r4_04,"B_R4_ONLINE_02":r4_02})
            if route!="PROPOSE" or selected is not model:raise RuntimeError("curve dispatch mismatch "+name)
            pred=eval_predictions(selected,xb,dev)
            curves[name].append({"feedback_count":count,"route":"PROPOSE","role":name,
                                 "adapter_version":count,**metric(pred,y_b)})
    # Matched rank-4 batch reference receives all feedback before exactly 128 updates.
    t0=time.perf_counter_ns();r4_batch.train()
    g=torch.Generator(device="cpu").manual_seed(seed+32)
    for _ in range(NSUPPORT*STEPS_PER_ARRIVAL):
        ix=torch.randint(NSUPPORT,(32,),generator=g).to(dev)
        loss=nn.functional.cross_entropy(r4_batch(xsupport[ix]),ysupport[ix])
        optimizers["rank4_batch_04"].zero_grad(set_to_none=True);loss.backward();optimizers["rank4_batch_04"].step()
    sync(dev);batch_ms=(time.perf_counter_ns()-t0)/1e6

    registry={"B_R2_ONLINE":r2,"B_R4_ONLINE_04":r4_04,"B_R4_ONLINE_02":r4_02,"B_R4_BATCH_04":r4_batch}
    final={}
    for role,version,adapter_id,model,x,expected in (
        ("A",0,"base",base,xa,y_a),("B_R2_ONLINE",16,"rank2",r2,xb,y_b),
        ("B_R4_ONLINE_04",16,"rank4_04",r4_04,xb,y_b),("B_R4_ONLINE_02",16,"rank4_02",r4_02,xb,y_b),
        ("B_R4_BATCH_04",16,"rank4_batch",r4_batch,xb,y_b)):
        route,selected=dispatch(role,16,16,adapter_id,version,version,base,registry)
        if route!="PROPOSE" or selected is not model:raise RuntimeError("final dispatch mismatch "+role)
        final[role]={"route":route,"adapter_id":adapter_id,"adapter_version":version,**metric(eval_predictions(selected,x,dev),expected),"expected":expected}
    invalid={
      "unknown_role":dispatch("B_UNKNOWN",16,16,"rank4_04",16,16,base,registry)[0],
      "stale_epoch":dispatch("B_R4_ONLINE_02",15,16,"rank4_02",16,16,base,registry)[0],
      "wrong_version":dispatch("B_R4_ONLINE_02",16,16,"rank4_02",15,16,base,registry)[0],
      "missing_adapter":dispatch("B_R4_ONLINE_02",16,16,"rank4_02",16,16,base,{})[0],
      "missing_epoch":dispatch("B_R4_ONLINE_02",None,16,"rank4_02",16,16,base,registry)[0]}
    snap=snapshot_gate(r4_02,r4_initial)
    return {"seed":seed,"expected_A":y_a,"expected_B":y_b,"final":final,"curves":curves,
            "feedback_ms":timings,"batch_128_updates_ms":batch_ms,"setup_ms":setups,
            "rank4_initial_states_identical":init_equal,"rank4_intervention_snapshot":snap,
            "base_immutable":state_equal(base,base_before),"invalid_routes":invalid,
            "support_order":order}
def main():
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    if not torch.cuda.is_available():raise RuntimeError("STOP_GPU_UNAVAILABLE")
    dev=torch.device("cuda:0");torch.cuda.synchronize(dev);torch.cuda.reset_peak_memory_stats(dev)
    seeds=[one_seed(s,dev) for s in SEEDS];torch.cuda.synchronize(dev)
    payload={"allocation":"needle-lora-rank4-online-lr-half-multiseed-v1",
      "environment":{"platform":platform.platform(),"python":platform.python_version(),"torch":torch.__version__,
        "cuda":torch.version.cuda,"device":torch.cuda.get_device_name(dev),"torch_threads":torch.get_num_threads(),
        "deterministic":torch.are_deterministic_algorithms_enabled(),"cublas_workspace_config":"4096:8",
        "peak_allocated_bytes":torch.cuda.max_memory_allocated(dev)},
      "seeds":seeds}
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    print(json.dumps({"sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw),
      "gzip_b64":base64.b64encode(gzip.compress(raw,mtime=0)).decode()},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
