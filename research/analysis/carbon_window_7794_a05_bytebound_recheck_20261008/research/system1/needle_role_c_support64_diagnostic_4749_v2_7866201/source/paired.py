"""One-shot paired diagnostic wrapper around byte-verified public-main runner."""
import hashlib, importlib.util, json, os, random
from pathlib import Path
import torch

SEED=int(os.environ["NEEDLE_SEED"]); OUT=Path(os.environ["NEEDLE_OUTPUT"])
spec=importlib.util.spec_from_file_location("public_runner","/src/upstream_runner.py")
u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
assert SEED==7866201 and OUT.is_dir() and not any(OUT.iterdir()),"STOP_ALLOCATION_OR_OUTPUT"
torch.set_num_threads(1); torch.use_deterministic_algorithms(True); random.seed(SEED); torch.manual_seed(SEED)
xa=u.data(u.N_BASE,SEED+1); xb=u.data(u.N_SUPPORT,SEED+2); xc64=u.data(64,SEED+3)
xc16=u.data(16,SEED+3)
assert xc64.shape==(64,u.D) and xc16.shape==(16,u.D) and xc64.dtype==xc16.dtype
assert torch.equal(xc64[:16],xc16) and bytes(xc64[:16].contiguous().view(torch.uint8).tolist())==bytes(xc16.contiguous().view(torch.uint8).tolist()),"STOP_SUPPORT_PREFIX"
ea,eb,ec=[u.data(u.N_HELDOUT,SEED+i) for i in (4,5,6)]
base=u.Core(); u.train(base,xa,u.labels(xa,"A"),list(base.parameters()),u.BASE_STEPS,u.LR_BASE,SEED+10)
base_before={k:v.clone() for k,v in base.state_dict().items()}
template=u.LoRA(base); initial={k:v.clone() for k,v in template.state_dict().items()}
bmodel=u.LoRA(base); bmodel.load_state_dict(initial); u.train(bmodel,xb,u.labels(xb,"B"),[bmodel.a,bmodel.b],u.ADAPTER_STEPS,u.LR_ADAPTER,SEED+11)
arms={}
for arm,rows in (("control16",xc64[:16]),("treatment64",xc64)):
    cm=u.LoRA(base); cm.load_state_dict(initial); u.train(cm,rows,u.labels(rows,"C"),[cm.a,cm.b],u.ADAPTER_STEPS,u.LR_ADAPTER,SEED+12)
    models={"A":base,"B":bmodel,"C":cm}; roles={}
    for role,x in (("A",ea),("B",eb),("C",ec)):
        with torch.no_grad(): roles[role]={"state":u.tensor_map(models[role]),"pred":models[role](x).argmax(-1).tolist(),"expected":u.labels(x,role).tolist(),"inputs":x.tolist()}
    arms[arm]={"roles":roles,"base_immutable":all(torch.equal(v,base_before[k]) for k,v in base.state_dict().items())}
assert arms["control16"]["roles"]["A"]==arms["treatment64"]["roles"]["A"]
assert arms["control16"]["roles"]["B"]==arms["treatment64"]["roles"]["B"]
accuracy={a:{r:sum(x==y for x,y in zip(v["pred"],v["expected"]))/len(v["expected"]) for r,v in z["roles"].items()} for a,z in arms.items()}
result={"allocation":"needle-role-c-support64-diagnostic-4749-v2-seed7866201","issue":4848,"seed":SEED,"source_git_blob_sha1":"ecd3a0414178f38535406573314793a40b353878","support_prefix":{"exact_bytes":True,"dtype":str(xc64.dtype),"shape64":list(xc64.shape),"shape16":list(xc16.shape),"independent_regeneration_seed":SEED+3},"accuracy":accuracy,"delta_C":accuracy["treatment64"]["C"]-accuracy["control16"]["C"],"A_B_exactly_unchanged":True,"base_immutable":all(x["base_immutable"] for x in arms.values()),"updates":{"base":u.BASE_STEPS,"B":u.ADAPTER_STEPS,"C_each_arm":u.ADAPTER_STEPS},"runtime":{"torch":torch.__version__,"threads":torch.get_num_threads(),"device":"cpu"}}
def dump(name,obj): (OUT/name).write_bytes(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode())
dump("result.json",result)
for arm,z in arms.items(): dump(arm+".json",{"seed":SEED,"arm":arm,"roles":z["roles"],"base_immutable":z["base_immutable"]})
print(json.dumps(result,sort_keys=True),flush=True)

