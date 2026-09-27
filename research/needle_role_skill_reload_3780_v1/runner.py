"""Train a small role graph, export a data-only skill, and load it in clean processes."""
import base64, copy, hashlib, json, os, platform, random, sys, time
import torch
from torch import nn

SEED = int(os.environ["NEEDLE_SEED"])
OUT = os.environ["NEEDLE_OUTPUT"]
D, H, C, RANK = 8, 16, 4, 2
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, ADAPTER_STEPS = 400, 120
LR_BASE, LR_ADAPTER = 0.025, 0.04
SCHEMA = "unjuno.role-skill.numeric-json.v1"

def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))

def labels(x, role):
    a, b = (x[:, 0] > 0).long(), (x[:, 1] > 0).long()
    if role == "B": a = 1-a
    if role == "C": b = 1-b
    return a * 2 + b

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

def train(model,x,y,params,steps,lr,seed):
    opt=torch.optim.AdamW(params,lr=lr); rng=torch.Generator(device="cpu").manual_seed(seed); model.train()
    for _ in range(steps):
        ix=torch.randint(len(x),(32,),generator=rng); loss=nn.functional.cross_entropy(model(x[ix]),y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()

def tensor_map(model):
    return {k:v.detach().cpu().tolist() for k,v in model.state_dict().items()}

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def main():
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True); random.seed(SEED); torch.manual_seed(SEED)
    xa,xb,xc,ea,eb,ec=[data(n,SEED+i) for i,n in enumerate((N_BASE,N_SUPPORT,N_SUPPORT,N_HELDOUT,N_HELDOUT,N_HELDOUT),1)]
    base=Core(); train(base,xa,labels(xa,"A"),list(base.parameters()),BASE_STEPS,LR_BASE,SEED+10)
    before={k:v.clone() for k,v in base.state_dict().items()}
    template=LoRA(base); initial={k:v.clone() for k,v in template.state_dict().items()}
    adapters={}
    for role,x,offset in (("B",xb,11),("C",xc,12)):
        m=LoRA(base); m.load_state_dict(initial); train(m,x,labels(x,role),[m.a,m.b],ADAPTER_STEPS,LR_ADAPTER,SEED+offset); adapters[role]=m
    models={"A":base,**adapters}; roles={}
    for role,x in (("A",ea),("B",eb),("C",ec)):
        with torch.no_grad(): roles[role]={"state":tensor_map(models[role]),"pred":models[role](x).argmax(-1).tolist(),"expected":labels(x,role).tolist(),"inputs":x.tolist()}
    artifact={"schema":SCHEMA,"generation":SEED,"architecture":{"input":D,"hidden":H,"classes":C,"rank":RANK,"roles":["A","B","C"]},"graph":{"nodes":[{"id":r,"version":r+"-v1"} for r in ("A","B","C")],"edges":[["A","B"],["B","C"]],"scope":"synthetic-fixture-v1"},"provenance":{"allocation":"needle-role-skill-cross-process-reload-v1","predecessor_issue":3780,"seed":SEED,"family":"synthetic-role-adapter-v1"},"tensors":{r:v["state"] for r,v in roles.items()}}
    artifact["payload_sha256"]=digest({k:v for k,v in artifact.items() if k!="payload_sha256"})
    for name,content in (("skill.json",artifact),("expected.json",{"seed":SEED,"roles":roles,"base_immutable":all(torch.equal(v,before[k]) for k,v in base.state_dict().items())})):
        with open(os.path.join(OUT,name),"w",encoding="utf-8") as f: json.dump(content,f,sort_keys=True,separators=(",",":"),allow_nan=False)
    print(json.dumps({"seed":SEED,"artifact_sha256":artifact["payload_sha256"],"artifact_bytes":os.path.getsize(os.path.join(OUT,"skill.json")),"environment":{"platform":platform.platform(),"python":platform.python_version(),"torch":torch.__version__,"device":"cpu","threads":torch.get_num_threads()}},sort_keys=True))

if __name__=="__main__": main()
