"""CPU-only independent audit of #3851's immutable pre-rollback curves."""
import base64, gzip, hashlib, json, math, platform, sys
import torch

RAW_SHA256="F185E4DEAB4B19BA4B146C723CB03C1078DB53307DCBF1C2D856D9C5728C320E"
PAYLOAD_SHA256="7b2547439420aa991668cbffe29eb296a9fc4e921663e3d51053441522ce443b"
RUNNER_SHA256="1FE0A27E045085508478FCCEA1DAAF3096BA0F2775A6A9F8C1A693536579554F"
OLD_AUDIT_SHA256="82AD70186A9FAEB59350B8CA1C9E951101D40C1C99DBA6EBB6BE4519187F800F"
OLD_AUDIT_STDOUT_SHA256="012AE716296C96D33C4D8A570748E46ED12EC54263F18C27CC30AF439E096708"
SEEDS=(3451,3452,3453,3454,3455)
ARM_ORDER={3451:("legacy","shared"),3452:("shared","legacy"),3453:("legacy","shared"),3454:("shared","legacy"),3455:("legacy","shared")}

def data(n,seed):
    return torch.randn(n,8,generator=torch.Generator(device="cpu").manual_seed(seed))
def labels(x,flip=False):
    first=(x[:,0]>0).long()
    if flip:first=1-first
    return first*2+(x[:,1]>0).long()
def rows_sha(x):
    return hashlib.sha256(x.contiguous().numpy().tobytes()).hexdigest()
def matches_sha(actual,expected):
    return actual.lower()==expected.lower()
def accuracy(expected,predicted):
    if len(expected)!=len(predicted) or not expected:raise ValueError("row count mismatch/empty")
    return sum(a==b for a,b in zip(expected,predicted))/len(expected)
def main():
    root=__import__("pathlib").Path(__file__).resolve().parent
    raw_path=root/"predecessor_raw_stdout.txt"
    old_audit_path=root/"predecessor_audit_stdout.txt"
    runner_path=root/"predecessor_runner.py"
    old_audit_path_source=root/"predecessor_audit.py"
    errors=[]
    raw=raw_path.read_bytes(); raw_sha=hashlib.sha256(raw).hexdigest()
    if not matches_sha(raw_sha,RAW_SHA256):raise SystemExit("STOP_PREDECESSOR_STDOUT_SHA256")
    old_audit_bytes=old_audit_path.read_bytes()
    old_audit_stdout_sha=hashlib.sha256(old_audit_bytes).hexdigest()
    if not matches_sha(old_audit_stdout_sha,OLD_AUDIT_STDOUT_SHA256):raise SystemExit("STOP_PREDECESSOR_AUDIT_STDOUT_SHA256")
    runner_sha=hashlib.sha256(runner_path.read_bytes()).hexdigest()
    audit_sha=hashlib.sha256(old_audit_path_source.read_bytes()).hexdigest()
    if not matches_sha(runner_sha,RUNNER_SHA256) or not matches_sha(audit_sha,OLD_AUDIT_SHA256):raise SystemExit("STOP_PREDECESSOR_SOURCE_SHA256")
    envelope=json.loads(raw)
    payload=gzip.decompress(base64.b64decode(envelope["gzip_b64"],validate=True))
    payload_sha=hashlib.sha256(payload).hexdigest()
    if not matches_sha(payload_sha,PAYLOAD_SHA256) or not matches_sha(envelope.get("sha256",""),PAYLOAD_SHA256):raise SystemExit("STOP_CANONICAL_PAYLOAD_SHA256")
    result=json.loads(payload)
    if result.get("allocation")!="needle-lora-3441-rank4-minibatch-rng-paired-v1":errors.append("allocation")
    env=result.get("environment",{})
    if env.get("python")!="3.11.9" or env.get("torch")!="2.5.1+cu121" or env.get("cuda")!="12.1" or env.get("device")!="NVIDIA GeForce RTX 3080 Laptop GPU":errors.append("environment")
    records=result.get("seeds",[])
    if tuple(r.get("seed") for r in records)!=SEEDS:errors.append("seed_set")
    old_audit=json.loads(old_audit_bytes)
    expected_old_errors=sorted(f"{seed}:{arm}:curve_final_mismatch" for seed in SEEDS for arm in ("legacy","shared"))
    if old_audit.get("errors")!=expected_old_errors or old_audit.get("decision")!="FAIL_AUDIT_INTEGRITY":errors.append("predecessor_audit_error_set")
    by_seed=[]; input_hashes={}; curve_rows=0
    for rec in records:
        seed=rec["seed"]; per_seed_errors=[]
        xa=data(4096,seed+3); xb=data(4096,seed+4)
        expected_a=labels(xa).tolist(); expected_b=labels(xb,True).tolist()
        input_hashes[str(seed)]={"A_heldout":rows_sha(xa),"B_heldout":rows_sha(xb),"support":rows_sha(data(16,seed+2)),"base":rows_sha(data(512,seed+1))}
        if rec.get("feedback_order")!=torch.randperm(16,generator=torch.Generator(device="cpu").manual_seed(seed+30)).tolist():per_seed_errors.append("support_order")
        initial=rec.get("initial_adapter_sha256",{})
        if set(initial)!={"legacy","shared"} or len(set(initial.values()))!=1:per_seed_errors.append("initial_adapter_hash")
        if rec.get("base_immutable") is not True or rec.get("identical_adapter_starts") is not True:per_seed_errors.append("state_integrity")
        if any(v!="YIELD" for v in rec.get("invalid_routes",{}).values()):per_seed_errors.append("invalid_route_controls")
        m=rec.get("metrics",{})
        am=m.get("A",{})
        if am.get("expected")!=expected_a or accuracy(expected_a,am.get("predictions",[]))!=am.get("correct",-1)/4096:per_seed_errors.append("A_final_rows")
        arms={}
        for arm in ("legacy","shared"):
            a=m.get(arm,{})
            if a.get("expected_b")!=expected_b:per_seed_errors.append(f"{arm}:expected_B")
            curve=a.get("curve",[]); predictions=a.get("predictions_by_arrival",[])
            if len(curve)!=16 or len(predictions)!=16:per_seed_errors.append(f"{arm}:curve_count")
            values=[]
            for i,(point,row) in enumerate(zip(curve,predictions),1):
                if row.get("arrival")!=i or row.get("n")!=4096 or point.get("feedback_seen")!=i:per_seed_errors.append(f"{arm}:arrival_{i}")
                if row.get("expected")!=expected_b or len(row.get("predictions",[]))!=4096:per_seed_errors.append(f"{arm}:rows_{i}");continue
                pred=row["predictions"]
                if any(type(x)is not int or not 0<=x<4 for x in pred):per_seed_errors.append(f"{arm}:class_range_{i}")
                acc=accuracy(expected_b,pred)
                if row.get("correct")!=round(acc*4096) or point.get("correct")!=round(acc*4096) or point.get("n")!=4096 or point.get("accuracy")!=acc:per_seed_errors.append(f"{arm}:metric_{i}")
                values.append(acc);curve_rows+=1
            if len(values)==16:arms[arm]=values
            # Final fields were measured after the frozen runner's rollback and are deliberately excluded.
        by_seed.append({"seed":seed,"arms":{k:{"arrival16":v[-1],"all16":v} for k,v in arms.items()},"errors":per_seed_errors})
        errors.extend(f"{seed}:{e}" for e in per_seed_errors)
    if curve_rows!=160:errors.append("curve_row_total")
    legacy=[x["arms"].get("legacy",{}).get("arrival16",0) for x in by_seed]
    shared=[x["arms"].get("shared",{}).get("arrival16",0) for x in by_seed]
    deltas=[b-a for a,b in zip(legacy,shared)]
    legacy_mean=sum(legacy)/len(legacy) if legacy else None
    shared_mean=sum(shared)/len(shared) if shared else None
    paired_mean=sum(deltas)/len(deltas) if deltas else None
    if errors:disposition="FAIL_CURVE_AUDIT"
    else:disposition="PASS_CURVE_ONLY_AUDIT_SCOPED"
    print(json.dumps({"issue":3865,"disposition":disposition,"errors":errors,"mode":"CPU-only offline; no training/CUDA","python":platform.python_version(),"torch":torch.__version__,"raw_stdout_sha256":raw_sha,"canonical_payload_sha256":payload_sha,"source_sha256":{"runner":runner_sha,"predecessor_audit":audit_sha,"predecessor_audit_stdout":old_audit_stdout_sha},"records":by_seed,"heldout_input_sha256":input_hashes,"curve_rows_verified":curve_rows,"legacy_mean_arrival16":legacy_mean,"shared_mean_arrival16":shared_mean,"paired_mean_shared_minus_legacy":paired_mean,"paired_seed_deltas":deltas,"legacy_collapse_reproduced":legacy_mean is not None and legacy_mean<=0.10,"post_rollback_final_metrics_used":False},sort_keys=True,separators=(",",":")))
    if errors:raise SystemExit(2)
if __name__=="__main__":main()
