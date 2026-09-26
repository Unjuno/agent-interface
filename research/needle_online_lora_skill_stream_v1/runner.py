"""Online LoRA skill stream with an uninterrupted reference and fresh-process resumes."""
import argparse, hashlib, json, math, os, platform, random, subprocess, sys, time
import torch
from torch import nn

ALLOCATION = "needle-online-lora-skill-stream-resume-v1"
SCHEMA = "unjuno.online-lora-skill.v1"
D, H, C, RANK = 8, 16, 4, 2
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, UPDATES_PER_ARRIVAL, LR_BASE, LR_ADAPTER = 400, 8, .025, .04
MILESTONES = {1, 2, 4, 8, 12, 16}

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sha(x): return hashlib.sha256(x).hexdigest()
def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f: f.write(canonical(obj).decode())
def read_json(path):
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))

def labels(x, flip=False):
    a, b = (x[:, 0] > 0).long(), (x[:, 1] > 0).long()
    if flip: a = 1-a
    return a*2+b

class Core(nn.Module):
    def __init__(self):
        super().__init__(); self.enc=nn.Sequential(nn.Linear(D,H),nn.Tanh()); self.head=nn.Linear(H,C)
    def forward(self,x): return self.head(self.enc(x))

class LoRA(nn.Module):
    def __init__(self,core):
        super().__init__(); self.core=core
        for p in core.parameters(): p.requires_grad_(False)
        self.a=nn.Parameter(torch.randn(H,RANK)*.04); self.b=nn.Parameter(torch.zeros(RANK,C))
    def forward(self,x):
        h=self.core.enc(x); return self.core.head(h)+(h@self.a@self.b)/RANK

def to_lists(state): return {k:v.detach().cpu().tolist() for k,v in state.items()}
def set_model(core, adapter, package):
    core.load_state_dict({k:torch.tensor(v,dtype=torch.float32) for k,v in package["base"].items()})
    adapter.load_state_dict({"core."+k:torch.tensor(v,dtype=torch.float32) for k,v in package["base"].items()} | {k:torch.tensor(v,dtype=torch.float32) for k,v in package["adapter"].items()})

def init_optimizer(model):
    opt=torch.optim.AdamW([model.a,model.b],lr=LR_ADAPTER)
    for p in (model.a,model.b):
        opt.state[p]={"step":torch.tensor(0.),"exp_avg":torch.zeros_like(p),"exp_avg_sq":torch.zeros_like(p)}
    return opt

def optimizer_json(opt, model):
    out={}
    for name,p in (("a",model.a),("b",model.b)):
        s=opt.state[p]
        out[name]={"step":int(s["step"].item()),"exp_avg":s["exp_avg"].detach().tolist(),"exp_avg_sq":s["exp_avg_sq"].detach().tolist()}
    return out

def restore_optimizer(opt, model, obj):
    if set(obj)!={"a","b"}: raise ValueError("optimizer_keys")
    for name,p in (("a",model.a),("b",model.b)):
        s=obj[name]
        if set(s)!={"step","exp_avg","exp_avg_sq"}: raise ValueError("optimizer_state_keys")
        avg=torch.tensor(s["exp_avg"],dtype=p.dtype); sq=torch.tensor(s["exp_avg_sq"],dtype=p.dtype)
        if avg.shape!=p.shape or sq.shape!=p.shape or not torch.isfinite(avg).all() or not torch.isfinite(sq).all(): raise ValueError("optimizer_tensor")
        opt.state[p]={"step":torch.tensor(float(s["step"])),"exp_avg":avg,"exp_avg_sq":sq}

def seal(obj):
    obj=dict(obj); obj.pop("content_sha256",None); obj["content_sha256"]=sha(canonical(obj)); return obj

def validate(obj, seed, arrival):
    required={"schema","allocation","seed","version","feedback_cursor","parent_sha256","base_sha256","base","adapter","optimizer","seen_rows","content_sha256"}
    if set(obj)!=required: raise ValueError("package_keys")
    if obj["schema"]!=SCHEMA or obj["allocation"]!=ALLOCATION: raise ValueError("schema")
    if obj["seed"]!=seed or obj["version"]!=arrival or obj["feedback_cursor"]!=arrival: raise ValueError("cursor_or_version")
    if sha(canonical(obj["base"]))!=obj["base_sha256"]: raise ValueError("base_digest")
    digest=obj["content_sha256"]; unsigned=dict(obj); unsigned.pop("content_sha256")
    if sha(canonical(unsigned))!=digest: raise ValueError("content_digest")
    if set(obj["base"])!={"enc.0.weight","enc.0.bias","head.weight","head.bias"}: raise ValueError("base_keys")
    shapes={"enc.0.weight":[H,D],"enc.0.bias":[H],"head.weight":[C,H],"head.bias":[C],"a":[H,RANK],"b":[RANK,C]}
    if set(obj["adapter"])!={"a","b"}: raise ValueError("adapter_keys")
    for k,v in (obj["base"]|obj["adapter"]).items():
        def shape(x): return [len(x),*shape(x[0])] if isinstance(x,list) and x else ([] if x==[] else [])
        if shape(v)!=shapes[k]: raise ValueError("tensor_shape:"+k)
    if len(obj["seen_rows"])!=arrival or len(set(obj["seen_rows"]))!=arrival: raise ValueError("seen_rows")
    return True

def package(seed, arrival, parent, base, model, opt, seen):
    body={"schema":SCHEMA,"allocation":ALLOCATION,"seed":seed,"version":arrival,"feedback_cursor":arrival,"parent_sha256":parent,"base_sha256":sha(canonical(base)),"base":base,"adapter":{"a":model.a.detach().tolist(),"b":model.b.detach().tolist()},"optimizer":optimizer_json(opt,model),"seen_rows":list(seen)}
    return seal(body)

def forward_rows(core, model, x):
    model.eval()
    with torch.no_grad(): logits=model(x); preds=logits.argmax(-1)
    return {"logits":logits.tolist(),"predictions":preds.tolist()}

def create_schedules(seed):
    xb=data(N_SUPPORT,seed+2); order=torch.randperm(N_SUPPORT,generator=torch.Generator(device="cpu").manual_seed(seed+20)).tolist()
    rng=torch.Generator(device="cpu").manual_seed(seed+21); seen=[]; arrivals=[]
    for row in order:
        seen.append(row); batches=[]
        for _ in range(UPDATES_PER_ARRIVAL):
            ix=torch.randint(len(seen),(32,),generator=rng).tolist(); batches.append([seen[j] for j in ix])
        arrivals.append({"row":row,"seen":list(seen),"batches":batches})
    return xb,order,arrivals

def apply_arrival(model,opt,xb,yb,batches):
    model.train(); started=time.perf_counter_ns()
    for ids in batches:
        ix=torch.tensor(ids,dtype=torch.long); loss=nn.functional.cross_entropy(model(xb[ix]),yb[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    return (time.perf_counter_ns()-started)/1e6

def worker(args):
    seed=args.seed; arrival=args.arrival; started=time.perf_counter_ns(); obj=read_json(args.input)
    validate(obj,seed,arrival-1)
    xb,order,schedule=create_schedules(seed); xb=xb; yb=labels(xb,True)
    expected=schedule[arrival-1]
    prior_seen=schedule[arrival-2]["seen"] if arrival>1 else []
    if obj["seen_rows"]!=prior_seen: raise ValueError("prior_seen_rows")
    core=Core(); model=LoRA(core); set_model(core,model,obj); opt=init_optimizer(model); restore_optimizer(opt,model,obj["optimizer"])
    updated=apply_arrival(model,opt,xb,yb,expected["batches"]); pid=os.getpid()
    seen=expected["seen"]; out=package(seed,arrival,obj["content_sha256"],obj["base"],model,opt,seen)
    validate(out,seed,arrival); write_json(args.output,out)
    meta={"seed":seed,"arrival":arrival,"pid":pid,"input_sha256":obj["content_sha256"],"output_sha256":out["content_sha256"],"update_ms":updated,"process_ms":(time.perf_counter_ns()-started)/1e6}
    if arrival in MILESTONES:
        xe=data(N_HELDOUT,seed+4); ye=labels(xe,True); meta["heldout"]={"expected":ye.tolist(),**forward_rows(core,model,xe)}
    write_json(args.meta,meta)

def run_seed(seed,outdir):
    os.makedirs(outdir,exist_ok=True); torch.set_num_threads(1); torch.use_deterministic_algorithms(True); random.seed(seed); torch.manual_seed(seed)
    xa,xb,ea,eb=[data(n,seed+i) for i,n in enumerate((N_BASE,N_SUPPORT,N_HELDOUT,N_HELDOUT),1)]
    ya,yb=labels(xa),labels(xb,True); eya,eyb=labels(ea),labels(eb,True)
    core=Core(); opt_base=torch.optim.AdamW(core.parameters(),lr=LR_BASE); gr=torch.Generator(device="cpu").manual_seed(seed+10)
    core.train()
    for _ in range(BASE_STEPS):
        ix=torch.randint(len(xa),(32,),generator=gr); loss=nn.functional.cross_entropy(core(xa[ix]),ya[ix]);opt_base.zero_grad(set_to_none=True);loss.backward();opt_base.step()
    base=to_lists(core.state_dict()); base_sha=sha(canonical(base)); base_heldout={"expected":eya.tolist(),**forward_rows(core,core,ea)}; model=LoRA(core); initial={k:v.detach().clone() for k,v in model.state_dict().items()}; opt=init_optimizer(model)
    xb,order,schedule=create_schedules(seed); initial_pkg=package(seed,0,"0"*64,base,model,opt,[]); validate(initial_pkg,seed,0); write_json(os.path.join(outdir,"checkpoint-00.json"),initial_pkg)
    # Paired uninterrupted reference and cross-process resumed stream start identically.
    ref_state=[]; ref_curve={}; ref_times=[]; ref_seen=[]
    for arrival,entry in enumerate(schedule,1):
        ref_seen.append(entry["row"]); ref_times.append(apply_arrival(model,opt,xb,yb,entry["batches"]))
        state={"arrival":arrival,"seen_rows":list(ref_seen),"adapter":{"a":model.a.detach().tolist(),"b":model.b.detach().tolist()},"optimizer":optimizer_json(opt,model)}
        if arrival in MILESTONES: state["heldout"]={"expected":eyb.tolist(),**forward_rows(core,model,eb)}
        ref_state.append(state)
    write_json(os.path.join(outdir,"reference.json"),{"seed":seed,"base":base,"base_sha256":base_sha,"order":order,"schedule":schedule,"times_ms":ref_times,"states":ref_state,"base_heldout":base_heldout})
    # Fresh-process resume: every step consumes only the prior sealed JSON package.
    prev=os.path.join(outdir,"checkpoint-00.json"); worker_meta=[]; pids=[]; resume_times=[]
    for arrival in range(1,N_SUPPORT+1):
        dest=os.path.join(outdir,f"checkpoint-{arrival:02d}.json"); meta=os.path.join(outdir,f"worker-{arrival:02d}.json")
        start=time.perf_counter_ns(); proc=subprocess.run([sys.executable,__file__,"--resume-worker","--seed",str(seed),"--arrival",str(arrival),"--input",prev,"--output",dest,"--meta",meta],capture_output=True,text=True)
        elapsed=(time.perf_counter_ns()-start)/1e6
        if proc.returncode: raise RuntimeError(f"worker_{arrival}_exit_{proc.returncode}: {proc.stderr[-1000:]}")
        m=read_json(meta); m["fresh_process_wall_ms"]=elapsed; worker_meta.append(m);pids.append(m["pid"]);resume_times.append(elapsed);prev=dest
    write_json(os.path.join(outdir,"orchestration.json"),{"seed":seed,"parent_pid":os.getpid(),"worker_pids":pids,"worker_metrics":worker_meta,"fresh_process_wall_ms":resume_times,"environment":{"platform":platform.platform(),"python":platform.python_version(),"torch":torch.__version__,"device":"cpu","threads":torch.get_num_threads(),"deterministic":torch.are_deterministic_algorithms_enabled()}})
    # Formal controls are separate-package copies and never mutate the valid stream.
    controls={}
    pkg=read_json(prev)
    cases=(("tampered_digest",lambda z:z.update(content_sha256="0"*64),False),("unknown_schema",lambda z:z.update(schema="future"),True),("bad_base_digest",lambda z:z.update(base_sha256="0"*64),True),("stale_version",lambda z:(z.update(version=15),z.update(feedback_cursor=15)),True),("duplicate_stage",None,None),("skipped_stage",None,None))
    for name,change,reseal in cases:
        probe=json.loads(json.dumps(pkg))
        if change: change(probe)
        if reseal: probe=seal(probe)
        try: validate(probe,seed,16);controls[name]="ACCEPT"
        except Exception: controls[name]="YIELD"
    for name,expected_arrival in (("duplicate_stage",15),("skipped_stage",17)):
        probe=json.loads(json.dumps(pkg)); probe=seal(probe)
        try: validate(probe,seed,expected_arrival);controls[name]="ACCEPT"
        except Exception: controls[name]="YIELD"
    write_json(os.path.join(outdir,"controls.json"),{"seed":seed,"controls":controls,"valid_final_sha256":pkg["content_sha256"],"valid_final_version":pkg["version"]})
    # Metrics are also retained for the in-memory reference at required checkpoints.
    print(json.dumps({"seed":seed,"base_sha256":base_sha,"ref_final_accuracy":sum(a==b for a,b in zip(eyb.tolist(),forward_rows(core,model,eb)["predictions"]))/N_HELDOUT,"workers":len(pids),"distinct_pids":len(set(pids)),"resume_wall_p95_ms":sorted(resume_times)[math.ceil(.95*len(resume_times))-1]},sort_keys=True))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--seed",type=int);ap.add_argument("--output",default="");ap.add_argument("--resume-worker",action="store_true");ap.add_argument("--arrival",type=int);ap.add_argument("--input",default="");ap.add_argument("--meta",default="");a=ap.parse_args()
    if a.resume_worker: worker(a)
    else: run_seed(a.seed,a.output)
if __name__=="__main__":main()
