"""Independent raw-only reconstruction of every role cell for all seeds."""
import json,sys,torch
root=sys.argv[1]; seeds=(7867401,7867601,7867801)
def load(p):
    with open(root+"/"+p,encoding="utf-8") as f:return json.load(f)
def stop(x): raise SystemExit("FAIL_RAW_AUDIT:"+x)
summary=load("summary.json")
if summary.get("issue")!=4884 or summary.get("allocation")!="needle-role-c-support64-replication-4884-v1" or tuple(summary.get("seeds",()))!=seeds: stop("seed_identity")
all_deltas=[]; cells=0
for seed in seeds:
    base=f"{seed}/"; result=load(base+"result.json")
    if result.get("seed")!=seed or result.get("allocation")!="needle-role-c-support64-replication-4884-v1" or result.get("upstream_runner_git_blob_sha1")!="ecd3a0414178f38535406573314793a40b353878": stop(f"{seed}:identity")
    g=torch.Generator(device="cpu").manual_seed(seed+3); x64=torch.randn(64,8,generator=g)
    h=torch.Generator(device="cpu").manual_seed(seed+3); x16=torch.randn(16,8,generator=h)
    if not torch.equal(x64[:16],x16) or result.get("prefix_exact") is not True: stop(f"{seed}:prefix")
    files={a:load(base+a+".json") for a in ("control16","treatment64")}
    for arm,obj in files.items():
        if obj.get("seed")!=seed or obj.get("arm")!=arm or obj.get("base_immutable") is not True or set(obj.get("roles",{}))!={"A","B","C"}: stop(f"{seed}:{arm}:metadata")
        for role,z in obj["roles"].items():
            if any(len(z[k])!=4096 for k in ("pred","expected","inputs")): stop(f"{seed}:{arm}:{role}:length")
            x=torch.tensor(z["inputs"],dtype=torch.float32)
            def t(k):return torch.tensor(z["state"][k],dtype=torch.float32)
            if role=="A": y=torch.nn.functional.linear(torch.tanh(torch.nn.functional.linear(x,t("enc.0.weight"),t("enc.0.bias"))),t("head.weight"),t("head.bias"))
            else:
                hh=torch.tanh(torch.nn.functional.linear(x,t("core.enc.0.weight"),t("core.enc.0.bias")))
                y=torch.nn.functional.linear(hh,t("core.head.weight"),t("core.head.bias"))+(hh@t("a")@t("b"))/2
            pred=y.argmax(-1).tolist()
            if pred!=z["pred"]: stop(f"{seed}:{arm}:{role}:prediction")
            a,b=x[:,0]>0,x[:,1]>0
            if role=="B": a=~a
            if role=="C": b=~b
            gold=(a.long()*2+b.long()).tolist()
            if gold!=z["expected"]: stop(f"{seed}:{arm}:{role}:labels")
            acc=sum(p==q for p,q in zip(pred,gold))/4096
            if abs(acc-result["accuracy"][arm][role])>1e-15: stop(f"{seed}:{arm}:{role}:accuracy")
            cells+=1
    for role in ("A","B"):
        if files["control16"]["roles"][role]!=files["treatment64"]["roles"][role]:stop(f"{seed}:{role}:pairing")
    delta=result["accuracy"]["treatment64"]["C"]-result["accuracy"]["control16"]["C"]
    if abs(delta-result["delta_C"])>1e-15:stop(f"{seed}:delta")
    all_deltas.append(delta)
if summary.get("deltas_C")!=all_deltas or summary.get("positive_count")!=sum(x>0 for x in all_deltas):stop("summary_reconstruction")
print(json.dumps({"disposition":"PASS_RAW_AUDIT","errors":[],"seeds":list(seeds),"reconstructed_cells":cells,"prefix_exact":True,"A_B_exact":True,"deltas_C":all_deltas,"positive_count":sum(x>0 for x in all_deltas)},sort_keys=True))
