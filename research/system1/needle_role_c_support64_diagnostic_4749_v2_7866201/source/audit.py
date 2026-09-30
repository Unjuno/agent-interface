"""Independent raw-only audit; imports neither experiment wrapper nor upstream trainer."""
import hashlib,json,sys
import torch
root=sys.argv[1]
def load(n): return json.load(open(root+"/"+n,encoding="utf-8"))
def fail(s): raise SystemExit("FAIL_RAW_AUDIT:"+s)
seed=7866201
r=load("result.json")
if r.get("seed")!=seed or r.get("issue")!=4848 or r.get("source_git_blob_sha1")!="ecd3a0414178f38535406573314793a40b353878": fail("identity")
g=torch.Generator(device="cpu").manual_seed(seed+3); x64=torch.randn(64,8,generator=g)
h=torch.Generator(device="cpu").manual_seed(seed+3); x16=torch.randn(16,8,generator=h)
if not torch.equal(x64[:16],x16) or r["support_prefix"].get("exact_bytes") is not True: fail("support_prefix")
files={a:load(a+".json") for a in ("control16","treatment64")}
for arm,obj in files.items():
    if obj.get("seed")!=seed or obj.get("arm")!=arm or obj.get("base_immutable") is not True: fail(arm+"_metadata")
    if set(obj["roles"])!={"A","B","C"}: fail(arm+"_roles")
    for role,z in obj["roles"].items():
        if len(z["pred"])!=4096 or len(z["expected"])!=4096 or len(z["inputs"])!=4096: fail(arm+role+"_length")
        xx=torch.tensor(z["inputs"],dtype=torch.float32)
        def t(k): return torch.tensor(z["state"][k],dtype=torch.float32)
        if role=="A":
            y=torch.nn.functional.linear(torch.tanh(torch.nn.functional.linear(xx,t("enc.0.weight"),t("enc.0.bias"))),t("head.weight"),t("head.bias"))
        else:
            hh=torch.tanh(torch.nn.functional.linear(xx,t("core.enc.0.weight"),t("core.enc.0.bias")))
            y=torch.nn.functional.linear(hh,t("core.head.weight"),t("core.head.bias"))+(hh@t("a")@t("b"))/2
        pred=y.argmax(-1).tolist()
        if pred!=z["pred"]: fail(arm+role+"_prediction_reconstruction")
        a,b=xx[:,0]>0,xx[:,1]>0
        if role=="B": a=~a
        if role=="C": b=~b
        gold=(a.long()*2+b.long()).tolist()
        if gold!=z["expected"]: fail(arm+role+"_label_reconstruction")
        if abs(sum(i==j for i,j in zip(pred,gold))/4096-r["accuracy"][arm][role])>1e-15: fail(arm+role+"_accuracy")
for role in ("A","B"):
    if files["control16"]["roles"][role]!=files["treatment64"]["roles"][role]: fail(role+"_paired_invariance")
delta=r["accuracy"]["treatment64"]["C"]-r["accuracy"]["control16"]["C"]
if abs(delta-r["delta_C"])>1e-15: fail("delta")
print(json.dumps({"disposition":"PASS_RAW_AUDIT","errors":[],"seed":seed,"prefix":"exact","reconstructed_role_cells":6,"A_B_exact":True,"delta_C":delta},sort_keys=True))

