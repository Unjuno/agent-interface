"""Independent row/state auditor; deliberately does not import runner.py."""
import hashlib,json,math,os,pathlib,statistics,sys,torch
from torch import nn

D,H,C,R=8,16,4,2
BASE_N,SUPPORT_N,HELD=512,16,4096
BASE_STEPS,UPDATES,LR0,LR=400,8,.025,.04
MILESTONES={1,2,4,8,12,16}
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def sha(x): return hashlib.sha256(x).hexdigest()
def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
def data(n,s): return torch.randn(n,D,generator=torch.Generator(device="cpu").manual_seed(s))
def labels(x,flip=False):
    a,b=(x[:,0]>0).long(),(x[:,1]>0).long()
    if flip:a=1-a
    return a*2+b
class Core(nn.Module):
    def __init__(self): super().__init__();self.enc=nn.Sequential(nn.Linear(D,H),nn.Tanh());self.head=nn.Linear(H,C)
    def forward(self,x):return self.head(self.enc(x))
class LoRA(nn.Module):
    def __init__(self,core):
        super().__init__();self.core=core
        for p in core.parameters():p.requires_grad_(False)
        self.a=nn.Parameter(torch.randn(H,R)*.04);self.b=nn.Parameter(torch.zeros(R,C))
    def forward(self,x):
        h=self.core.enc(x);return self.core.head(h)+(h@self.a@self.b)/R
def st_json(model):return {k:v.detach().cpu().tolist() for k,v in model.state_dict().items()}
def opt_json(opt,m):
    z={}
    for n,p in (("a",m.a),("b",m.b)):
        s=opt.state[p];z[n]={"step":int(s["step"].item()),"exp_avg":s["exp_avg"].tolist(),"exp_avg_sq":s["exp_avg_sq"].tolist()}
    return z
def exact_reference(seed):
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True);torch.manual_seed(seed)
    xa,xb,ea,eb=[data(n,seed+i) for i,n in enumerate((BASE_N,SUPPORT_N,HELD,HELD),1)]
    ya,yb,eya,eyb=labels(xa),labels(xb,True),labels(ea),labels(eb,True)
    base=Core();o=torch.optim.AdamW(base.parameters(),lr=LR0);g=torch.Generator(device="cpu").manual_seed(seed+10);base.train()
    for _ in range(BASE_STEPS):
        ix=torch.randint(len(xa),(32,),generator=g);loss=nn.functional.cross_entropy(base(xa[ix]),ya[ix]);o.zero_grad(set_to_none=True);loss.backward();o.step()
    basej=st_json(base);m=LoRA(base);op=torch.optim.AdamW([m.a,m.b],lr=LR)
    for p in (m.a,m.b):op.state[p]={"step":torch.tensor(0.),"exp_avg":torch.zeros_like(p),"exp_avg_sq":torch.zeros_like(p)}
    order=torch.randperm(SUPPORT_N,generator=torch.Generator(device="cpu").manual_seed(seed+20)).tolist();rng=torch.Generator(device="cpu").manual_seed(seed+21);seen=[];states=[]
    for k,row in enumerate(order,1):
        seen.append(row)
        for _ in range(UPDATES):
            ix=torch.randint(len(seen),(32,),generator=rng).tolist();ids=torch.tensor([seen[j] for j in ix]);loss=nn.functional.cross_entropy(m(xb[ids]),yb[ids]);op.zero_grad(set_to_none=True);loss.backward();op.step()
        s={"arrival":k,"seen_rows":list(seen),"adapter":{"a":m.a.detach().tolist(),"b":m.b.detach().tolist()},"optimizer":opt_json(op,m)}
        if k in MILESTONES:
            m.eval()
            with torch.no_grad():lg=m(eb);pr=lg.argmax(-1)
            s["heldout"]={"expected":eyb.tolist(),"logits":lg.tolist(),"predictions":pr.tolist()}
        states.append(s)
    base.eval();
    with torch.no_grad(): bl=base(ea);bp=bl.argmax(-1)
    return {"base":basej,"base_sha256":sha(canon(basej)),"order":order,"states":states,"base_heldout":{"expected":eya.tolist(),"logits":bl.tolist(),"predictions":bp.tolist()},"x_heldout_b":eb,"y_heldout_b":eyb}
def validate_artifact(o,seed,version):
    keys={"schema","allocation","seed","version","feedback_cursor","parent_sha256","base_sha256","base","adapter","optimizer","seen_rows","content_sha256"}
    if set(o)!=keys or o["schema"]!="unjuno.online-lora-skill.v1" or o["allocation"]!="needle-online-lora-skill-stream-resume-v1":raise ValueError("schema")
    if o["seed"]!=seed or o["version"]!=version or o["feedback_cursor"]!=version:raise ValueError("version")
    if sha(canon(o["base"]))!=o["base_sha256"]:raise ValueError("base_digest")
    unsigned=dict(o);d=unsigned.pop("content_sha256")
    if sha(canon(unsigned))!=d:raise ValueError("content_digest")
    shape={"enc.0.weight":[16,8],"enc.0.bias":[16],"head.weight":[4,16],"head.bias":[4],"a":[16,2],"b":[2,4]}
    for k,v in (o["base"]|o["adapter"]).items():
        def sh(x):return [len(x),*sh(x[0])] if isinstance(x,list) and x else ([] if x==[] else [])
        if sh(v)!=shape[k]:raise ValueError("shape")
    return True
def predict(base,adapter,x):
    t=lambda obj,k:torch.tensor(obj[k],dtype=torch.float32)
    x=torch.tensor(x,dtype=torch.float32)
    h=torch.tanh(nn.functional.linear(x,t(base,"enc.0.weight"),t(base,"enc.0.bias")))
    y=nn.functional.linear(h,t(base,"head.weight"),t(base,"head.bias"))+h@t(adapter,"a")@t(adapter,"b")/2
    return y.tolist(),y.argmax(-1).tolist()
def main():
    root=pathlib.Path(sys.argv[1]);src=pathlib.Path(__file__).parent;freeze=load(src/"FREEZE.json");errors=[];summary=[]
    for key,name in (("runner_sha256","runner.py"),("preregistration_sha256","PREREGISTRATION.md"),("test_sha256","test_construction.py")):
        if sha((src/name).read_bytes())!=freeze.get(key):errors.append("freeze:"+name)
    for seed in freeze["seeds"]:
        d=root/f"seed-{seed}";ref=load(d/"reference.json");orch=load(d/"orchestration.json");truth=exact_reference(seed)
        if ref["base"]!=truth["base"] or ref["base_sha256"]!=truth["base_sha256"]:errors.append(f"{seed}:base_reproduction")
        if ref["order"]!=truth["order"]:errors.append(f"{seed}:order")
        if ref["states"]!=truth["states"]:errors.append(f"{seed}:reference_reproduction")
        if ref["base_heldout"]!=truth["base_heldout"]:errors.append(f"{seed}:base_rows")
        pids=orch["worker_pids"]
        if len(pids)!=16 or len(set(pids))!=16 or orch["parent_pid"] in pids:errors.append(f"{seed}:fresh_processes")
        prior="0"*64;resume_ms=[];update_ms=[]
        for arrival in range(17):
            pkg=load(d/f"checkpoint-{arrival:02d}.json")
            try:validate_artifact(pkg,seed,arrival)
            except Exception as e:errors.append(f"{seed}:package:{arrival}:{type(e).__name__}");continue
            if arrival and pkg["parent_sha256"]!=prior:errors.append(f"{seed}:chain:{arrival}")
            if pkg["base"]!=truth["base"] or pkg["base_sha256"]!=truth["base_sha256"]:errors.append(f"{seed}:base_identity:{arrival}")
            if arrival and pkg["seen_rows"]!=truth["states"][arrival-1]["seen_rows"]:errors.append(f"{seed}:cursor_rows:{arrival}")
            if arrival:
                st=truth["states"][arrival-1]
                if pkg["adapter"]!=st["adapter"]:errors.append(f"{seed}:adapter_exact:{arrival}")
                if pkg["optimizer"]!=st["optimizer"]:errors.append(f"{seed}:adamw_exact:{arrival}")
                m=load(d/f"worker-{arrival:02d}.json");resume_ms.append(orch["fresh_process_wall_ms"][arrival-1]);update_ms.append(m["update_ms"])
                if m["pid"]!=pids[arrival-1] or m["arrival"]!=arrival or m["input_sha256"]!=prior or m["output_sha256"]!=pkg["content_sha256"]:errors.append(f"{seed}:worker_binding:{arrival}")
                if m["update_ms"]!=orch["worker_metrics"][arrival-1]["update_ms"]:errors.append(f"{seed}:timing_binding:{arrival}")
                if arrival in MILESTONES:
                    h=m.get("heldout",{})
                    if h.get("expected")!=truth["states"][arrival-1]["heldout"]["expected"] or h.get("logits")!=truth["states"][arrival-1]["heldout"]["logits"] or h.get("predictions")!=truth["states"][arrival-1]["heldout"]["predictions"]:errors.append(f"{seed}:heldout_exact:{arrival}")
                    logits,pred=predict(pkg["base"],pkg["adapter"],truth["x_heldout_b"])
                    if logits!=h.get("logits") or pred!=h.get("predictions"):errors.append(f"{seed}:independent_rows:{arrival}")
            prior=pkg["content_sha256"]
        control=load(d/"controls.json")
        expected_controls={"tampered_digest":"YIELD","unknown_schema":"YIELD","bad_base_digest":"YIELD","stale_version":"YIELD","duplicate_stage":"YIELD","skipped_stage":"YIELD"}
        if control.get("controls")!=expected_controls or control.get("valid_final_version")!=16:errors.append(f"{seed}:controls")
        if not update_ms or sorted(update_ms)[math.ceil(.95*len(update_ms))-1]>60:errors.append(f"{seed}:update_p95")
        final=truth["states"][-1]["heldout"];acc=sum(a==b for a,b in zip(final["expected"],final["predictions"]))/HELD
        summary.append({"seed":seed,"B_accuracy":acc,"update_p95_ms":sorted(update_ms)[math.ceil(.95*len(update_ms))-1] if update_ms else None,"fresh_process_p95_ms":sorted(resume_ms)[math.ceil(.95*len(resume_ms))-1] if resume_ms else None})
    disposition="PASS_AUDIT_SCOPED" if not errors else "FAIL_AUDIT"
    out={"disposition":disposition,"errors":errors,"seeds":summary};(root/"audit.json").write_bytes(canon(out));print(json.dumps(out,sort_keys=True,separators=(",",":")))
    if errors:raise SystemExit(1)
if __name__=="__main__":main()
