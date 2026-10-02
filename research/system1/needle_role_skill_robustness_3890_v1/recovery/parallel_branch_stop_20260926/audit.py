"""Independent raw-evidence auditor for Issue #4479; imports neither runner nor loader."""
import hashlib
import json
import pathlib
import sys

import torch
from torch.nn import functional as F

ROLES=("A","B","C")
SEEDS=(100000,100100,100200,100300,100400,100500,100600,100700,100800,100900)
D,H,C,RANK=8,16,4,2
SCHEMA="unjuno.role-skill.numeric-json.v1"
ALLOCATION="needle-role-skill-robustness-3890-v1"
EXPECTED_CONTROLS={"tampered_digest":"YIELD","wrong_adapter_version":"YIELD","skipped_edge":"YIELD","wrong_scope":"YIELD","unverified_outcome":"YIELD","unknown_destination":"YIELD","truncated":"YIELD","unknown_schema":"YIELD","duplicate_receipt":"ADVANCE","duplicate_receipt_second":"YIELD"}
TENSOR_SHAPES={"enc.0.weight":[16,8],"enc.0.bias":[16],"head.weight":[4,16],"head.bias":[4],"core.enc.0.weight":[16,8],"core.enc.0.bias":[16],"core.head.weight":[4,16],"core.head.bias":[4],"a":[16,2],"b":[2,4]}
TENSOR_KEYS={"A":{"enc.0.weight","enc.0.bias","head.weight","head.bias"},"B":{"core.enc.0.weight","core.enc.0.bias","core.head.weight","core.head.bias","a","b"},"C":{"core.enc.0.weight","core.enc.0.bias","core.head.weight","core.head.bias","a","b"}}


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")


def labels(x,role):
    a=(x[:,0]>0).long(); b=(x[:,1]>0).long()
    if role=="B": a=1-a
    if role=="C": b=1-b
    return (a*2+b).tolist()


def expected_features(seed,role):
    offset={"A":4,"B":5,"C":6}[role]
    return torch.randn(4096,D,generator=torch.Generator(device="cpu").manual_seed(seed+offset))


def tensor(state,key):
    return torch.tensor(state[key],dtype=torch.float32)


def independent_predictions(role,state,rows):
    x=torch.tensor(rows,dtype=torch.float32)
    if role=="A":
        h=torch.tanh(F.linear(x,tensor(state,"enc.0.weight"),tensor(state,"enc.0.bias")))
        logits=F.linear(h,tensor(state,"head.weight"),tensor(state,"head.bias"))
    else:
        h=torch.tanh(F.linear(x,tensor(state,"core.enc.0.weight"),tensor(state,"core.enc.0.bias")))
        logits=F.linear(h,tensor(state,"core.head.weight"),tensor(state,"core.head.bias"))
        logits=logits+(h@tensor(state,"a")@tensor(state,"b"))/RANK
    return logits.argmax(-1).tolist()


def state_equal(a,b):
    return a==b


def source_checks(source,freeze,errors):
    required=freeze["source_sha256"]
    for name,digest in required.items():
        path=source/name
        if not path.is_file():
            errors.append("source_missing:"+name)
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            errors.append("source_hash:"+name)
    contract=(source/"ISSUE_CONTRACT.md").read_bytes()
    if hashlib.sha256(contract).hexdigest()!=freeze["issue_contract_sha256"]:
        errors.append("issue_contract_hash")
    if freeze.get("issue")!=4479 or freeze.get("base_main_sha")!="21dd6a26dbd9f5cb4a6e11b1060902799a76a733":
        errors.append("freeze_identity")
    if freeze.get("seeds")!=list(SEEDS):
        errors.append("seed_schedule")
    prior_seeds=(3781,3782,3783,3787,3788,3789,3790,3791)
    offsets=(*range(1,7),10,11,12)
    current_stream={s+o for s in SEEDS for o in offsets}
    prior_stream={s+o for s in prior_seeds for o in offsets}
    if current_stream&prior_stream:
        errors.append("prior_component_rng_reuse")


def audit(root):
    root=pathlib.Path(root); source=pathlib.Path(__file__).parent
    freeze=json.loads((source/"FREEZE.json").read_text(encoding="utf-8"))
    errors=[]; reports=[]
    source_checks(source,freeze,errors)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    for seed in SEEDS:
        d=root/f"seed-{seed}"
        try:
            raw=(d/"builder"/"skill.json").read_bytes()
            artifact=json.loads(raw)
            expected=json.loads((d/"builder"/"expected.json").read_text(encoding="utf-8"))
            meta=json.loads((d/"builder"/"builder_meta.json").read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{seed}:builder_evidence:{type(exc).__name__}")
            continue
        payload=artifact.get("payload_sha256")
        unhashed={k:v for k,v in artifact.items() if k!="payload_sha256"}
        if payload!=hashlib.sha256(canonical(unhashed)).hexdigest(): errors.append(f"{seed}:package_digest")
        if artifact.get("schema")!=SCHEMA or artifact.get("generation")!=seed: errors.append(f"{seed}:identity")
        if artifact.get("architecture")!={"input":D,"hidden":H,"classes":C,"rank":RANK,"roles":["A","B","C"]}: errors.append(f"{seed}:architecture")
        graph={"nodes":[{"id":r,"version":r+"-v1"} for r in ROLES],"edges":[["A","B"],["B","C"]],"scope":"synthetic-fixture-v1"}
        if artifact.get("graph")!=graph: errors.append(f"{seed}:graph_manifest")
        prov={"allocation":ALLOCATION,"predecessor_issue":3890,"seed":seed,"family":"synthetic-role-adapter-v1"}
        if artifact.get("provenance")!=prov: errors.append(f"{seed}:provenance")
        if set(artifact.get("tensors",{}))!=set(ROLES) or set(expected.get("roles",{}))!=set(ROLES): errors.append(f"{seed}:role_set")
        if expected.get("seed")!=seed or expected.get("base_immutable") is not True: errors.append(f"{seed}:builder_metadata")
        wanted_meta={"seed":seed,"allocation":ALLOCATION,"optimizer_steps":640,"base_steps":400,"adapter_steps_per_role":120,
                     "optimizer_seed_offsets":{"base":10,"B":11,"C":12},
                     "data_seed_offsets":{"base":1,"support_B":2,"support_C":3,"heldout_A":4,"heldout_B":5,"heldout_C":6},
                     "artifact_payload_sha256":payload,"artifact_file_sha256":hashlib.sha256(raw).hexdigest(),"artifact_bytes":len(raw)}
        if any(meta.get(k)!=v for k,v in wanted_meta.items()): errors.append(f"{seed}:builder_step_or_hash_metadata")
        seed_report={"seed":seed,"artifact_sha256":hashlib.sha256(raw).hexdigest(),"roles":{},"loaders":{}}
        for role in ROLES:
            try:
                rec=expected["roles"][role]; x=expected_features(seed,role)
                if rec.get("inputs")!=x.tolist(): errors.append(f"{seed}:{role}:heldout_features")
                gold=labels(x,role)
                if rec.get("expected")!=gold: errors.append(f"{seed}:{role}:labels")
                state=artifact["tensors"][role]
                if set(state)!=TENSOR_KEYS[role]: errors.append(f"{seed}:{role}:tensor_keys")
                for key,value in state.items():
                    t=torch.tensor(value,dtype=torch.float32)
                    if key not in TENSOR_SHAPES or list(t.shape)!=TENSOR_SHAPES[key] or not torch.isfinite(t).all():
                        errors.append(f"{seed}:{role}:tensor_shape_or_value:{key}")
                pred=independent_predictions(role,state,x.tolist())
                if rec.get("pred")!=pred: errors.append(f"{seed}:{role}:builder_prediction")
                accuracy=sum(p==y for p,y in zip(pred,gold))/4096
                if accuracy<.90: errors.append(f"{seed}:{role}:accuracy")
                if len(set(pred))<2: errors.append(f"{seed}:{role}:collapsed")
                seed_report["roles"][role]={"accuracy":accuracy,"rows":len(pred)}
            except Exception as exc:
                errors.append(f"{seed}:{role}:reconstruction:{type(exc).__name__}")
        # LoRA B/C must carry an exact immutable copy of the A core.
        a=artifact.get("tensors",{}).get("A",{})
        for role in ("B","C"):
            st=artifact.get("tensors",{}).get(role,{})
            for source_key,target_key in (("enc.0.weight","core.enc.0.weight"),("enc.0.bias","core.enc.0.bias"),("head.weight","core.head.weight"),("head.bias","core.head.bias")):
                if a.get(source_key)!=st.get(target_key): errors.append(f"{seed}:{role}:core_mutation:{source_key}")
        for run in ("load1","load2"):
            try:
                result=json.loads((d/run/"loader.json").read_text(encoding="utf-8"))
                actual_sha=hashlib.sha256(raw).hexdigest()
                if result.get("accepted") is not True: errors.append(f"{seed}:{run}:not_accepted")
                if result.get("artifact_sha256")!=actual_sha: errors.append(f"{seed}:{run}:artifact_bytes")
                expected_predictions={r:independent_predictions(r,artifact["tensors"][r],expected["roles"][r]["inputs"]) for r in ROLES}
                if result.get("predictions")!=expected_predictions: errors.append(f"{seed}:{run}:predictions")
                graphs=result.get("graphs",[])
                if len(graphs)!=2: errors.append(f"{seed}:{run}:generation_count")
                for g in graphs:
                    if g.get("flow")!=["ADVANCE","ADVANCE"] or g.get("cursor")!="C" or g.get("old_receipt")!="YIELD": errors.append(f"{seed}:{run}:graph_flow")
                    if g.get("controls")!=EXPECTED_CONTROLS: errors.append(f"{seed}:{run}:controls")
                    if g.get("fixture_emissions")!=2: errors.append(f"{seed}:{run}:emissions")
                seed_report["loaders"][run]={"accepted":result.get("accepted"),"graphs":len(graphs)}
            except Exception as exc:
                errors.append(f"{seed}:{run}:evidence:{type(exc).__name__}")
        reports.append(seed_report)
    quality=(len(reports)==len(SEEDS) and all(len(r["roles"])==3 and all(v["accuracy"]>=.90 for v in r["roles"].values()) and len(r["loaders"])==2 for r in reports))
    integrity=not errors
    disposition=("PASS_ROLE_SKILL_ROBUSTNESS_SCOPED" if integrity and quality else
                 "FAIL_ROLE_SKILL_ROBUSTNESS" if integrity else "HOLD_AUDIT_OR_INTEGRITY")
    return {"audit":"PASS" if integrity else "FAIL","disposition":disposition,"errors":errors,"seed_reports":reports,
            "minimum_role_accuracy":min((v["accuracy"] for r in reports for v in r["roles"].values()),default=None),
            "scope":"ten seeds from one synthetic family; data-only package and fixture receipt graph; no runtime authority"}


def main():
    out=pathlib.Path(sys.argv[1])
    try:
        result=audit(out)
    except Exception as exc:
        result={"audit":"STOP","disposition":"STOP_AUDIT_EXCEPTION","errors":[type(exc).__name__+":"+str(exc)],"seed_reports":[]}
    (out/"audit.json").write_text(json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False),encoding="utf-8")
    print(json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False))
    if result["audit"]!="PASS": raise SystemExit(2)


if __name__=="__main__": main()
