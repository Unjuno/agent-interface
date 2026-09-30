"""Independent raw-only score/pair audit; no runner or wrapper imports."""
import json,sys,torch
root=sys.argv[1]; seed=7866401
def load(n): return json.load(open(root+"/"+n,encoding="utf-8"))
def stop(x): raise SystemExit("FAIL_RAW_AUDIT:"+x)
r=load("result.json")
if r.get("seed")!=seed or r.get("issue")!=4853 or r.get("upstream_runner_git_blob_sha1")!="ecd3a0414178f38535406573314793a40b353878": stop("identity")
g=torch.Generator(device="cpu").manual_seed(seed+3); x64=torch.randn(64,8,generator=g)
h=torch.Generator(device="cpu").manual_seed(seed+3); x16=torch.randn(16,8,generator=h)
if not torch.equal(x64[:16],x16) or r.get("prefix_exact") is not True: stop("prefix")
files={a:load(a+".json") for a in ("control16","treatment64")}
for arm,obj in files.items():
    if obj.get("seed")!=seed or obj.get("arm")!=arm or obj.get("base_immutable") is not True or set(obj["roles"])!={"A","B","C"}: stop(arm+"_metadata")
    for role,z in obj["roles"].items():
        if any(len(z[k])!=4096 for k in ("pred","expected","inputs")): stop(arm+role+"_length")
        x=torch.tensor(z["inputs"],dtype=torch.float32)
        def t(k): return torch.tensor(z["state"][k],dtype=torch.float32)
        if role=="A": y=torch.nn.functional.linear(torch.tanh(torch.nn.functional.linear(x,t("enc.0.weight"),t("enc.0.bias"))),t("head.weight"),t("head.bias"))
        else:
            hh=torch.tanh(torch.nn.functional.linear(x,t("core.enc.0.weight"),t("core.enc.0.bias")))
            y=torch.nn.functional.linear(hh,t("core.head.weight"),t("core.head.bias"))+(hh@t("a")@t("b"))/2
        pred=y.argmax(-1).tolist()
        if pred!=z["pred"]: stop(arm+role+"_prediction")
        a,b=x[:,0]>0,x[:,1]>0
        if role=="B": a=~a
        if role=="C": b=~b
        gold=(a.long()*2+b.long()).tolist()
        if gold!=z["expected"]: stop(arm+role+"_labels")
        acc=sum(i==j for i,j in zip(pred,gold))/4096
        if abs(acc-r["accuracy"][arm][role])>1e-15: stop(arm+role+"_accuracy")
for role in ("A","B"):
    if files["control16"]["roles"][role]!=files["treatment64"]["roles"][role]: stop(role+"_pairing")
delta=r["accuracy"]["treatment64"]["C"]-r["accuracy"]["control16"]["C"]
if abs(delta-r["delta_C"])>1e-15: stop("delta")
print(json.dumps({"disposition":"PASS_RAW_AUDIT","errors":[],"seed":seed,"reconstructed_cells":6,"prefix_exact":True,"A_B_exact":True,"delta_C":delta},sort_keys=True))

