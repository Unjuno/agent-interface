"""Three fresh-seed paired support-count replication; frozen before allocation."""
import importlib.util,json,os,random
from pathlib import Path
import torch
from prefix_contract import verify_prefix

SEEDS=(7867401,7867601,7867801)
OUT=Path(os.environ["NEEDLE_OUTPUT"])
os.environ["NEEDLE_SEED"]=str(SEEDS[0])
os.environ["NEEDLE_OUTPUT"]=str(OUT)
spec=importlib.util.spec_from_file_location("public_runner","/src/upstream_runner.py")
u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
assert tuple(map(int,os.environ["NEEDLE_SEEDS"].split(",")))==SEEDS
assert OUT.is_dir() and not any(OUT.iterdir()),"STOP_ALLOCATION_OR_OUTPUT"
torch.set_num_threads(1); torch.use_deterministic_algorithms(True)

def one(seed):
    random.seed(seed); torch.manual_seed(seed)
    xa=u.data(u.N_BASE,seed+1); xb=u.data(u.N_SUPPORT,seed+2); xc64,xc16=verify_prefix(u,seed)
    assert torch.equal(xc64[:16],xc16)
    ea,eb,ec=[u.data(u.N_HELDOUT,seed+i) for i in (4,5,6)]
    base=u.Core(); u.train(base,xa,u.labels(xa,"A"),list(base.parameters()),u.BASE_STEPS,u.LR_BASE,seed+10)
    before={k:v.clone() for k,v in base.state_dict().items()}
    template=u.LoRA(base); initial={k:v.clone() for k,v in template.state_dict().items()}
    bmodel=u.LoRA(base); bmodel.load_state_dict(initial); u.train(bmodel,xb,u.labels(xb,"B"),[bmodel.a,bmodel.b],u.ADAPTER_STEPS,u.LR_ADAPTER,seed+11)
    arms={}
    for arm,rows in (("control16",xc64[:16]),("treatment64",xc64)):
        cm=u.LoRA(base); cm.load_state_dict(initial); u.train(cm,rows,u.labels(rows,"C"),[cm.a,cm.b],u.ADAPTER_STEPS,u.LR_ADAPTER,seed+12)
        roles={}
        for role,x,model in (("A",ea,base),("B",eb,bmodel),("C",ec,cm)):
            with torch.no_grad(): roles[role]={"state":u.tensor_map(model),"pred":model(x).argmax(-1).tolist(),"expected":u.labels(x,role).tolist(),"inputs":x.tolist()}
        arms[arm]={"roles":roles,"base_immutable":all(torch.equal(v,base.state_dict()[k]) for k,v in before.items())}
    same={r:arms["control16"]["roles"][r]==arms["treatment64"]["roles"][r] for r in ("A","B")}
    acc={a:{r:sum(p==q for p,q in zip(z["pred"],z["expected"]))/len(z["expected"]) for r,z in val["roles"].items()} for a,val in arms.items()}
    return {"seed":seed,"allocation":"needle-role-c-support64-replication-4884-v1","upstream_runner_git_blob_sha1":"ecd3a0414178f38535406573314793a40b353878","prefix_exact":True,"accuracy":acc,"delta_C":acc["treatment64"]["C"]-acc["control16"]["C"],"A_B_exactly_unchanged":all(same.values()),"base_immutable":all(v["base_immutable"] for v in arms.values()),"updates":{"base":u.BASE_STEPS,"B":u.ADAPTER_STEPS,"C_each_arm":u.ADAPTER_STEPS},"arms":arms}

results=[one(seed) for seed in SEEDS]
summary={"allocation":"needle-role-c-support64-replication-4884-v1","issue":4884,"seeds":list(SEEDS),"results":[{k:v for k,v in x.items() if k!="arms"} for x in results],"deltas_C":[x["delta_C"] for x in results],"positive_count":sum(x["delta_C"]>0 for x in results),"median_delta_C":sorted(x["delta_C"] for x in results)[1],"A_B_invariant_all":all(x["A_B_exactly_unchanged"] for x in results),"prefix_exact_all":all(x["prefix_exact"] for x in results),"base_immutable_all":all(x["base_immutable"] for x in results),"runtime":{"torch":torch.__version__,"threads":torch.get_num_threads(),"device":"cpu"}}
for x in results:
    d=OUT/str(x["seed"]); d.mkdir()
    (d/"result.json").write_text(json.dumps({k:v for k,v in x.items() if k!="arms"},sort_keys=True,separators=(",",":"),allow_nan=False),encoding="utf-8")
    for arm,val in x["arms"].items(): (d/(arm+".json")).write_text(json.dumps({"seed":x["seed"],"arm":arm,"roles":val["roles"],"base_immutable":val["base_immutable"]},sort_keys=True,separators=(",",":"),allow_nan=False),encoding="utf-8")
(OUT/"summary.json").write_text(json.dumps(summary,sort_keys=True,separators=(",",":"),allow_nan=False),encoding="utf-8")
print(json.dumps(summary,sort_keys=True),flush=True)
