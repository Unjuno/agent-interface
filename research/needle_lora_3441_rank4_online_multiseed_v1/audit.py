"""Independent raw auditor; regenerates task labels and checks packed predictions without importing runner."""
import base64,gzip,hashlib,json,math,sys
import torch
e=json.load(open(sys.argv[1],encoding="utf-8"))
payload=gzip.decompress(base64.b64decode(e["result_gzip_b64"]))
if len(payload)!=e.get("result_bytes"): raise SystemExit("STOP_RAW_LENGTH")
if hashlib.sha256(payload).hexdigest()!=e.get("result_sha256"): raise SystemExit("STOP_RAW_SHA256")
r=json.loads(payload); errors=[]; rows=0; per_seed={}
def unpack2(data,n):
    out=[]
    for b in data: out.extend(((b>>6)&3,(b>>4)&3,(b>>2)&3,b&3))
    if n is not None: out=out[:n]
    return out
def pack2(xs):
    return bytes((xs[i]<<6)|(xs[i+1]<<4)|(xs[i+2]<<2)|xs[i+3] for i in range(0,len(xs),4))
design={"base_rows":512,"support_rows":16,"heldout_rows":4096,"base_steps":400,
        "updates_per_arrival":8,"total_adapter_steps":128,"ranks":[2,4],
        "arms":["rank2_online","rank2_batch","rank4_online","rank4_batch"]}
if r.get("allocation")!="needle-lora-3441-rank4-online-multiseed-v1": errors.append("allocation")
if r.get("seeds")!=[3451,3452,3453,3454,3455]: errors.append("seeds")
if r.get("frozen_design")!=design: errors.append("design")
env=r.get("environment",{})
if env.get("device")!="cpu" or env.get("threads")!=1 or env.get("deterministic") is not True: errors.append("environment")
records=r.get("records",[])
if [x.get("seed") for x in records]!=r.get("seeds"): errors.append("record_seed_set")
rank4_online=[]; rank2_online=[]; rank4_batch=[]; all_r4_ms=[]
for rec in records:
    seed=rec["seed"]
    # Recreate the two independently seeded held-out inputs and exact task labels.
    ea=torch.randn(4096,8,generator=torch.Generator(device="cpu").manual_seed(seed+3))
    eb=torch.randn(4096,8,generator=torch.Generator(device="cpu").manual_seed(seed+4))
    def labels(x,flip=False):
        a=(x[:,0]>0).long()
        if flip: a=1-a
        return (a*2+(x[:,1]>0).long()).tolist()
    expected_a=labels(ea); expected_b=labels(eb,True)
    packed_expected=base64.b64decode(rec.get("expected_labels_b64",""),validate=True)
    if packed_expected!=pack2(expected_b): errors.append(f"{seed}:expected_labels")
    if hashlib.sha256(packed_expected).hexdigest()!=rec.get("expected_labels_sha256"): errors.append(f"{seed}:expected_sha")
    expected_by_role={"A":expected_a,"B":expected_b}
    metrics=rec.get("metrics",{})
    if set(metrics)!={"A","B_R2_ONLINE","B_R2_BATCH","B_R4_ONLINE","B_R4_BATCH"}: errors.append(f"{seed}:arm_set")
    seed_acc={}
    for role,expected in expected_by_role.items():
        roles=[role] if role=="A" else ["B_R2_ONLINE","B_R2_BATCH","B_R4_ONLINE","B_R4_BATCH"]
        for arm in roles:
            m=metrics.get(arm,{})
            try: packed=base64.b64decode(m.get("predicted_b64",""),validate=True)
            except Exception: errors.append(f"{seed}:{arm}:decode"); continue
            if len(packed)!=1024: errors.append(f"{seed}:{arm}:length")
            if hashlib.sha256(packed).hexdigest()!=m.get("predicted_sha256"): errors.append(f"{seed}:{arm}:sha")
            pred=unpack2(packed,4096)
            if m.get("n")!=4096 or len(pred)!=4096: errors.append(f"{seed}:{arm}:rows")
            correct=sum(a==b for a,b in zip(expected,pred))
            if correct!=m.get("correct") or m.get("accuracy")!=correct/4096: errors.append(f"{seed}:{arm}:metric")
            if m.get("decision")!="PROPOSE" or m.get("requested_role")!=arm or m.get("epoch")!=16 or m.get("version")!=16 or m.get("selected_adapter")!=arm: errors.append(f"{seed}:{arm}:dispatch")
            seed_acc[arm]=correct/4096; rows+=len(pred)
    per_seed[str(seed)]=seed_acc
    rank2_online.append(seed_acc.get("B_R2_ONLINE",0))
    rank4_online.append(seed_acc.get("B_R4_ONLINE",0))
    rank4_batch.append(seed_acc.get("B_R4_BATCH",0))
    updates=rec.get("online_update_ms",{})
    r4=updates.get("rank4",[])
    if len(r4)!=16 or any(not isinstance(v,(int,float)) or v<0 for v in r4): errors.append(f"{seed}:rank4_update_vector")
    all_r4_ms.extend(r4)
    curves=rec.get("learning_curve",{})
    for k in ("rank2","rank4"):
        c=curves.get(k,[])
        if [x.get("feedback_seen") for x in c]!=[1,2,4,8,12,16]: errors.append(f"{seed}:{k}:curve_points")
        if any(x.get("n")!=4096 or not 0<=x.get("correct",-1)<=4096 or x.get("accuracy")!=x.get("correct",0)/4096 for x in c): errors.append(f"{seed}:{k}:curve_values")
    if rec.get("base_immutable") is not True: errors.append(f"{seed}:base_mutation")
    snap=rec.get("rank4_snapshot",{})
    if snap.get("roundtrip_exact") is not True or snap.get("rollback_exact") is not True: errors.append(f"{seed}:snapshot")
    if snap.get("bytes",0)<=0 or len(snap.get("initial_sha256",""))!=64 or len(snap.get("learned_sha256",""))!=64: errors.append(f"{seed}:snapshot_metadata")
    if rec.get("invalid_route_controls")!={"unknown_role":"YIELD","stale_epoch":"YIELD","wrong_version":"YIELD","missing_adapter":"YIELD"}: errors.append(f"{seed}:route_controls")
mean2=sum(rank2_online)/len(rank2_online) if rank2_online else 0
mean4=sum(rank4_online)/len(rank4_online) if rank4_online else 0
mean4b=sum(rank4_batch)/len(rank4_batch) if rank4_batch else 0
p95=sorted(all_r4_ms)[math.ceil(.95*len(all_r4_ms))-1] if all_r4_ms else None
gates={"all_A_ge_090":all(x.get("A",0)>=.90 for x in per_seed.values()),
       "all_rank4_online_ge_090":all(x>=.90 for x in rank4_online),
       "rank4_online_mean_gain_ge_003":mean4-mean2>=.03,
       "each_rank4_online_within_003_batch":all(abs(a-b)<=.03 for a,b in zip(rank4_online,rank4_batch)),
       "rank4_online_p95_ms_le_60":p95 is not None and p95<=60}
# Audit reports empirical gates separately from byte/contract integrity.
gate_failures=[k for k,v in gates.items() if not v]
out={"disposition":"PASS_AUDIT_V1" if not errors else "FAIL_AUDIT_V1",
     "errors":sorted(errors),"heldout_prediction_rows":rows,"per_seed":per_seed,
     "means":{"rank2_online":mean2,"rank4_online":mean4,"rank4_batch":mean4b},
     "rank4_online_p95_ms":p95,"gates":gates,"gate_failures":gate_failures,
     "scientific_disposition":"PASS_RANK4_ONLINE_RESCUE_SCOPED" if not errors and not gate_failures else ("FAIL_ONLINE_RANK_CAPACITY" if not errors else "HOLD_AUDIT_INTEGRITY")}
print(json.dumps(out,sort_keys=True,separators=(",",":")))
