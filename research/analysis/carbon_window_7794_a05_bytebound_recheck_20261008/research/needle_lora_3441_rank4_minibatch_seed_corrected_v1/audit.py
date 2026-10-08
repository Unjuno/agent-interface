"""Independent CPU auditor for Issue 3851 raw CUDA result; does not import runner."""
import base64,gzip,hashlib,json,math,sys
import torch

SEEDS=[3451,3452,3453,3454,3455]
ROLES=["rank4_legacy_seed35","rank4_shared_seed31"]
YIELDS={"unknown_role":"YIELD","stale_epoch":"YIELD","wrong_version":"YIELD","missing_adapter":"YIELD","missing_epoch":"YIELD"}

def pack2(xs):
    vals=[int(x) for x in xs]
    return bytes((vals[i]<<6)|(vals[i+1]<<4)|(vals[i+2]<<2)|vals[i+3] for i in range(0,len(vals),4))
def unpack2(b,n):
    out=[]
    for x in b:out.extend(((x>>6)&3,(x>>4)&3,(x>>2)&3,x&3))
    return out[:n]
def pct95(v):return sorted(v)[math.ceil(.95*len(v))-1]

e=json.load(open(sys.argv[1],encoding="utf-8"))
errors=[]
try:raw=gzip.decompress(base64.b64decode(e["result_gzip_b64"],validate=True))
except Exception as ex:raise SystemExit("STOP_RAW_DECODE:"+str(ex))
if len(raw)!=e.get("result_bytes"):errors.append("raw_length")
if hashlib.sha256(raw).hexdigest()!=e.get("result_sha256"):errors.append("raw_sha")
r=json.loads(raw)
if r.get("allocation")!="needle-lora-3441-rank4-minibatch-seed-corrected-index-v1":errors.append("allocation")
if r.get("seeds")!=SEEDS:errors.append("seed_list")
design=r.get("frozen_design",{})
if design!={"base_rows":512,"support_rows":16,"heldout_rows":4096,"base_steps":400,
 "updates_per_arrival":8,"total_updates":128,"arms":ROLES,"seeds":SEEDS}:errors.append("design")
env=r.get("environment",{})
if env.get("device")!="NVIDIA GeForce RTX 3080 Laptop GPU" or env.get("cuda")!="12.1" or env.get("torch")!="2.5.1+cu121":errors.append("device")
if env.get("threads")!=1 or env.get("deterministic") is not True or env.get("tf32") is not False or env.get("cublas_workspace_config")!=":4096:8":errors.append("determinism")
records=r.get("records",[])
if [x.get("seed") for x in records]!=SEEDS:errors.append("record_seed_set")
per_seed={}; legacy=[];shared=[];alltimings=[];curve_rows=0
for idx,rec in enumerate(records):
    seed=SEEDS[idx]
    order_expected=["rank4_legacy_seed35","rank4_shared_seed31"] if idx%2==0 else ["rank4_shared_seed31","rank4_legacy_seed35"]
    if rec.get("arm_order")!=order_expected:errors.append(f"{seed}:balanced_order")
    if rec.get("feedback_order")!=torch.randperm(16,generator=torch.Generator(device="cpu").manual_seed(seed+30)).tolist():errors.append(f"{seed}:feedback_order")
    eb=torch.randn(4096,8,generator=torch.Generator(device="cpu").manual_seed(seed+4))
    xa=torch.randn(512,8,generator=torch.Generator(device="cpu").manual_seed(seed+1))
    xb=torch.randn(16,8,generator=torch.Generator(device="cpu").manual_seed(seed+2))
    expected=(1-(eb[:,0]>0).long())*2+(eb[:,1]>0).long()
    expected_list=expected.tolist();packed_expected=pack2(expected_list)
    def tensor_hash(t):
        t=t.contiguous()
        h=hashlib.sha256();h.update(str(t.dtype).encode());h.update(str(tuple(t.shape)).encode());h.update(t.numpy().tobytes())
        return h.hexdigest()
    expected_hashes={"base_x":tensor_hash(xa),"base_y":tensor_hash((xa[:,0]>0).long()*2+(xa[:,1]>0).long()),
      "support_x":tensor_hash(xb),"support_y":tensor_hash((1-(xb[:,0]>0).long())*2+(xb[:,1]>0).long()),
      "heldout_A_x":tensor_hash(ea),"heldout_A_y":tensor_hash((ea[:,0]>0).long()*2+(ea[:,1]>0).long()),
      "heldout_B_x":tensor_hash(eb),"heldout_B_y":tensor_hash(expected)}
    if rec.get("data_sha256")!=expected_hashes:errors.append(f"{seed}:data_hashes")
    try:stored=base64.b64decode(rec.get("expected_B_labels_b64",""),validate=True)
    except Exception:stored=b""
    if stored!=packed_expected:errors.append(f"{seed}:expected_labels")
    if hashlib.sha256(stored).hexdigest()!=rec.get("expected_B_labels_sha256"):errors.append(f"{seed}:expected_sha")
    if rec.get("initial_adapter_sha256") is None:errors.append(f"{seed}:initial_state_hash")
    arms=rec.get("arms",{})
    if set(arms)!=set(ROLES):errors.append(f"{seed}:arm_keys")
    curve_acc={}
    for role in ROLES:
        arm=arms.get(role,{})
        if arm.get("initial_sha256")!=rec.get("initial_adapter_sha256"):errors.append(f"{seed}:{role}:initial_mismatch")
        if arm.get("initial_state_exact") is not True:errors.append(f"{seed}:{role}:initial_state_copy")
        if not isinstance(arm.get("adapter_setup_ms"),(int,float)) or arm["adapter_setup_ms"]<0:errors.append(f"{seed}:{role}:adapter_setup")
        if not isinstance(arm.get("optimizer_setup_ms"),(int,float)) or arm["optimizer_setup_ms"]<0:errors.append(f"{seed}:{role}:optimizer_setup")
        times=arm.get("feedback_ms",[])
        if len(times)!=16 or any(not isinstance(t,(int,float)) or t<0 for t in times):errors.append(f"{seed}:{role}:timings")
        alltimings.extend(times)
        offset=35 if role==ROLES[0] else 31
        rng=torch.Generator(device="cpu").manual_seed(seed+offset)
        seen=[];flat=[]
        for row_id in rec.get("feedback_order",[]):
            seen.append(row_id)
            for _ in range(8):
                flat.extend(seen[j] for j in torch.randint(len(seen),(32,),generator=rng).tolist())
        if hashlib.sha256(bytes(flat)).hexdigest()!=arm.get("sampler_schedule_sha256"):errors.append(f"{seed}:{role}:sampler_hash")
        curve=arm.get("curve",[])
        if [x.get("feedback_seen") for x in curve]!=list(range(1,17)):errors.append(f"{seed}:{role}:curve_counts")
        if len(curve)!=16:continue
        for count,row in enumerate(curve,start=1):
            m=row.get("metrics",{})
            if m.get("requested_role")!=role or m.get("selected_adapter")!=role or m.get("decision")!="PROPOSE" or m.get("epoch")!=1 or m.get("version")!=16:errors.append(f"{seed}:{role}:{count}:route")
            try:packed=base64.b64decode(m.get("predicted_b64",""),validate=True)
            except Exception:errors.append(f"{seed}:{role}:{count}:decode");continue
            if len(packed)!=1024:errors.append(f"{seed}:{role}:{count}:pred_length")
            if hashlib.sha256(packed).hexdigest()!=m.get("predicted_sha256") or row.get("predicted_sha256")!=m.get("predicted_sha256"):errors.append(f"{seed}:{role}:{count}:pred_sha")
            pred=unpack2(packed,4096);correct=sum(a==b for a,b in zip(expected_list,pred));curve_rows+=len(pred)
            if m.get("correct")!=correct or m.get("n")!=4096 or m.get("accuracy")!=correct/4096:errors.append(f"{seed}:{role}:{count}:curve_metric")
        curve_acc[role]=curve[-1]["metrics"].get("accuracy",0)
        final=rec.get("final",{}).get(role,{})
        if final.get("predicted_b64")!=curve[-1]["metrics"].get("predicted_b64") or final.get("accuracy")!=curve_acc[role]:errors.append(f"{seed}:{role}:final_curve_mismatch")
    legacy.append(curve_acc.get(ROLES[0],0));shared.append(curve_acc.get(ROLES[1],0))
    per_seed[str(seed)]={"legacy":curve_acc.get(ROLES[0],0),"shared":curve_acc.get(ROLES[1],0)}
    a=rec.get("base_A",{})
    if a.get("requested_role")!="A" or a.get("decision")!="PROPOSE" or a.get("epoch")!=1 or a.get("version")!=0:errors.append(f"{seed}:base_route")
    ea=torch.randn(4096,8,generator=torch.Generator(device="cpu").manual_seed(seed+3))
    expected_a=(ea[:,0]>0).long()*2+(ea[:,1]>0).long()
    try:preda=unpack2(base64.b64decode(a.get("predicted_b64",""),validate=True),4096)
    except Exception:preda=[]
    ac=sum(int(x)==int(y) for x,y in zip(expected_a.tolist(),preda))
    if len(preda)!=4096 or a.get("correct")!=ac or a.get("accuracy")!=ac/4096:errors.append(f"{seed}:base_metric")
    if rec.get("base_A",{}).get("predicted_sha256")!=hashlib.sha256(base64.b64decode(a.get("predicted_b64",""))).hexdigest():errors.append(f"{seed}:base_sha")
    if rec.get("base_immutable") is not True:errors.append(f"{seed}:base_mutable")
    if rec.get("invalid_routes")!=YIELDS:errors.append(f"{seed}:yield_controls")
    snap=rec.get("snapshot",{})
    if snap.get("roundtrip_exact") is not True or snap.get("rollback_exact") is not True:errors.append(f"{seed}:snapshot")
    if not all(isinstance(snap.get(k),str) and len(snap[k])==64 for k in ("initial_sha256","learned_sha256","serialized_sha256")):errors.append(f"{seed}:snapshot_hashes")
    if not isinstance(snap.get("bytes"),int) or snap["bytes"]<=0:errors.append(f"{seed}:snapshot_bytes")
mean_legacy=sum(legacy)/len(legacy) if legacy else 0
gain=(sum(shared)/len(shared)-mean_legacy) if shared else 0
p95=pct95(alltimings) if alltimings else None
integrity=not errors
if not integrity:decision="FAIL_ROUTE_OR_STATE_INTEGRITY"
elif mean_legacy>0.10:decision="HOLD_LEGACY_COLLAPSE_NOT_REPRODUCED"
elif all(x>=0.90 for x in shared) and gain>=0.50 and p95 is not None and p95<=60:decision="PASS_SAMPLER_SEED_EXPLAINS_COLLAPSE_SCOPED"
else:decision="FAIL_SAMPLER_SEED_NOT_SUFFICIENT"
out={"disposition":decision,"integrity":integrity,"errors":sorted(errors),"audited_curve_predictions":curve_rows,
 "curves_per_arm_per_seed":16,"regenerated_expected_labels":True,"per_seed":per_seed,
 "legacy_mean":mean_legacy,"shared_mean":sum(shared)/len(shared) if shared else 0,
 "paired_mean_gain":gain,"feedback_p95_ms":p95}
print(json.dumps(out,sort_keys=True,separators=(",",":")))



