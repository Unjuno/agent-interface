"""Independent verifier for the paired rank-4 minibatch RNG experiment."""
import base64,gzip,hashlib,json,math,platform,sys
import torch

SEEDS=[3451,3452,3453,3454,3455]
ORDER={3451:["legacy","shared"],3452:["shared","legacy"],3453:["legacy","shared"],3454:["shared","legacy"],3455:["legacy","shared"]}
ALLOC="needle-lora-3441-rank4-minibatch-rng-paired-v1"
def main():
    envelope=json.load(sys.stdin)
    try:raw=gzip.decompress(base64.b64decode(envelope["gzip_b64"],validate=True))
    except Exception as e:raise SystemExit("STOP_GZIP:"+str(e))
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=envelope.get("sha256"):raise SystemExit("STOP_RESULT_SHA256")
    result=json.loads(raw); errors=[]; per_seed={}; all_times=[]
    if result.get("allocation")!=ALLOC:errors.append("allocation")
    env=result.get("environment",{})
    if env.get("python")!="3.11.9" or env.get("torch")!="2.5.1+cu121" or env.get("cuda")!="12.1":errors.append("environment_versions")
    if env.get("device")!="NVIDIA GeForce RTX 3080 Laptop GPU" or env.get("cublas_workspace_config")!=":4096:8":errors.append("device_or_cublas")
    if env.get("torch_threads")!=1 or env.get("deterministic") is not True:errors.append("determinism")
    records=result.get("seeds",[])
    if [r.get("seed") for r in records]!=SEEDS:errors.append("seed_set")
    legacy=[]; shared=[]
    for rec in records:
        seed=rec.get("seed"); seed_errors=[]
        if rec.get("feedback_order") is None or sorted(rec["feedback_order"])!=list(range(16)):seed_errors.append("feedback_order")
        expected_order=ORDER.get(seed)
        metrics=rec.get("metrics",{}); timings=rec.get("timing_ms",{}); snaps=rec.get("snapshots",{})
        if set(timings)!=set(expected_order or []):seed_errors.append("arm_timing_set")
        if set(snaps)!=set(expected_order or []):seed_errors.append("arm_snapshot_set")
        if rec.get("base_immutable") is not True or rec.get("identical_adapter_starts") is not True:seed_errors.append("state_integrity")
        if rec.get("invalid_routes")!={"unknown_role":"YIELD","stale_epoch":"YIELD","wrong_version":"YIELD","missing_adapter":"YIELD"}:seed_errors.append("invalid_routes")
        initial_hashes=rec.get("initial_adapter_sha256",{})
        if set(initial_hashes)!={"legacy","shared"} or any(len(v)!=64 for v in initial_hashes.values()) or len(set(initial_hashes.values()))!=1:seed_errors.append("initial_state_sha")
        seed_values={}
        for arm in ("legacy","shared"):
            metric=metrics.get(arm,{})
            x=torch.randn(4096,8,generator=torch.Generator(device="cpu").manual_seed(seed+4)); labels=1-(x[:,0]>0).long();labels=labels*2+(x[:,1]>0).long();expected=labels.tolist()
            if metric.get("expected_b")!=expected:seed_errors.append(arm+":expected_b")
            if metric.get("decision")!="PROPOSE" or metric.get("requested_role")!=arm or metric.get("epoch")!=1 or metric.get("version")!=16 or metric.get("selected_adapter")!=arm:seed_errors.append(arm+":route")
            curve=metric.get("curve",[])
            predictions=metric.get("predictions_by_arrival",[])
            if len(curve)!=16 or len(predictions)!=16:seed_errors.append(arm+":curve_length")
            if [x.get("feedback_seen") for x in curve]!=list(range(1,17)):seed_errors.append(arm+":curve_order")
            for i,row in enumerate(predictions,1):
                if row.get("arrival")!=i or row.get("n")!=4096 or len(row.get("expected",[]))!=4096 or len(row.get("predictions",[]))!=4096:seed_errors.append(f"{arm}:rows:{i}");continue
                pred=row["predictions"]
                correct=sum(a==b for a,b in zip(expected,pred))
                if row["expected"]!=expected or row.get("correct")!=correct:seed_errors.append(f"{arm}:prediction_metric:{i}")
                if curve[i-1].get("correct")!=correct or curve[i-1].get("n")!=4096 or curve[i-1].get("accuracy")!=correct/4096:seed_errors.append(f"{arm}:curve_metric:{i}")
            if len(metric.get("predictions",[]))!=4096:seed_errors.append(arm+":final_rows")
            else:
                pred=metric["predictions"]
                correct=sum(a==b for a,b in zip(expected,pred)); accuracy=correct/4096
                if metric.get("expected")!=expected or metric.get("correct")!=correct or metric.get("n")!=4096:seed_errors.append(arm+":final_metric")
                if curve and curve[-1].get("correct")!=correct:seed_errors.append(arm+":curve_final_mismatch")
                seed_values[arm]=accuracy
            lat=timings.get(arm,[])
            if len(lat)!=16 or any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in lat):seed_errors.append(arm+":latency")
            all_times.extend(lat)
            snap=snaps.get(arm,{})
            if snap.get("roundtrip_exact") is not True or snap.get("rollback_exact") is not True or len(snap.get("initial_sha256",""))!=64 or len(snap.get("learned_sha256",""))!=64:seed_errors.append(arm+":snapshot")
        if "legacy" in seed_values:legacy.append(seed_values["legacy"])
        if "shared" in seed_values:shared.append(seed_values["shared"])
        per_seed[str(seed)]={"accuracy":seed_values,"errors":seed_errors}
        errors.extend(f"{seed}:{x}" for x in seed_errors)
    legacy_mean=sum(legacy)/len(legacy) if legacy else None
    shared_mean=sum(shared)/len(shared) if shared else None
    improvement=[b-a for a,b in zip(legacy,shared)]
    paired_mean=sum(improvement)/len(improvement) if improvement else None
    p95=sorted(all_times)[math.ceil(.95*len(all_times))-1] if all_times else None
    if errors:decision="FAIL_AUDIT_INTEGRITY"
    elif legacy_mean>.10:decision="HOLD_LEGACY_COLLAPSE_NOT_REPRODUCED"
    elif all(x>=.90 for x in shared) and paired_mean>=.50 and p95<=60:decision="PASS_SAMPLER_SEED_EXPLAINS_COLLAPSE_SCOPED"
    else:decision="FAIL_SAMPLER_SEED_NOT_SUFFICIENT"
    print(json.dumps({"audit":"PASS" if not errors else "FAIL","errors":errors,"decision":decision,"per_seed":per_seed,"legacy_mean":legacy_mean,"shared_mean":shared_mean,"paired_mean_improvement":paired_mean,"p95_feedback_ms":p95,"formal_invocations":1,"retries":0},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
