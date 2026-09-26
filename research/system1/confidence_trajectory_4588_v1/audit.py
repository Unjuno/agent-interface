"""Independent stdlib-only regeneration and audit; never imports runner.py."""
import argparse
import hashlib
import json
import math
import math
from pathlib import Path
import random

SEEDS = list(range(2026100100, 2026101001, 100))
FAMILIES = ["mono_a", "mono_b", "alias_accel", "plateau_noop", "self_correct_noop",
            "uncertain_yield", "stale_yield", "oscillation_yield", "spike_yield", "required_action"]
GROUP = {"mono_a": "action", "mono_b": "action", "alias_accel": "alias",
         "plateau_noop": "noop", "self_correct_noop": "noop", "uncertain_yield": "yield",
         "stale_yield": "invalid", "oscillation_yield": "noise", "spike_yield": "noise",
         "required_action": "required"}
ARMS = {"CURRENT_ONLY": [0, 1, 6, 7, 8], "LEVEL_VELOCITY": [0, 1, 2, 3, 6, 7, 8],
        "LEVEL_VELOCITY_ACCEL": list(range(9)), "CAUSAL_SMOOTHED": list(range(9))}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regen_example(rng, seed, split, family, index):
    noise = rng.uniform(-0.018, 0.018)
    irregular = rng.choice([0.5, 1.0, 1.5, 2.0])
    dt0 = rng.choice([0.5, 1.0, 1.5, 2.0]) if rng.random() < 0.35 else 1.0
    dt1 = irregular
    pA, pB, progress, valid, label = [0.4]*3, [0.4]*3, 0.0, 1.0, 3
    alias_id = None
    if family == "mono_a": pA, pB, label = [0.56,0.68,0.82], [0.36,0.31,0.25], 0
    elif family == "mono_b": pA, pB, label = [0.36,0.31,0.25], [0.56,0.68,0.82], 1
    elif family == "alias_accel":
        dt0 = dt1 = 1.0
        alias_id = f"{split}-{seed}-{index//2}"
        if index % 2 == 0: pA,pB,progress,label = [0.38,0.44,0.50],[0.30,0.34,0.38],0.15,0
        else: pA,pB,progress,label = [0.34,0.44,0.50],[0.30,0.34,0.38],0.15,2
        noise = 0.0
    elif family == "plateau_noop": pA,pB,progress,label = [0.63]*3,[0.51]*3,0.65,2
    elif family == "self_correct_noop": pA,pB,progress,label = [0.68,0.74,0.79],[0.30,0.27,0.23],0.92,2
    elif family == "uncertain_yield": pA,pB,progress,label = [0.31,0.34,0.35],[0.30,0.32,0.34],0.05,3
    elif family == "stale_yield": pA,pB,progress,valid,label = [0.42,0.58,0.79],[0.5,0.4,0.3],0.1,0.0,3
    elif family == "oscillation_yield": pA,pB,progress,label = [0.32,0.76,0.38],[0.70,0.28,0.66],0.05,3
    elif family == "spike_yield": pA,pB,progress,label = [0.36,0.48,0.88],[0.35,0.42,0.40],0.05,3
    elif family == "required_action": pA,pB,progress,label = [0.45,0.60,0.78],[0.31,0.29,0.27],0.03,0
    else: raise ValueError("unknown family")
    if noise:
        pA=[max(0.01,min(0.99,x+rng.uniform(-noise,noise))) for x in pA]
        pB=[max(0.01,min(0.99,x+rng.uniform(-noise,noise))) for x in pB]
    va=(pA[2]-pA[1])/dt1; va0=(pA[1]-pA[0])/dt0
    vb=(pB[2]-pB[1])/dt1; vb0=(pB[1]-pB[0])/dt0
    aa=(va-va0)/((dt0+dt1)/2); ab=(vb-vb0)/((dt0+dt1)/2)
    sa=0.5*va+0.5*va0; sb=0.5*vb+0.5*vb0
    features=[pA[2],pB[2],va,vb,aa,ab,progress,valid,dt1/2]
    smooth=[pA[2],pB[2],va,vb,sa,sb,progress,valid,dt1/2]
    if noise:
        features=[x+rng.uniform(-0.005,0.005) if i<6 else x for i,x in enumerate(features)]
        smooth=[x+rng.uniform(-0.005,0.005) if i<6 else x for i,x in enumerate(smooth)]
    status=rng.choice(["stale","missing","epoch_mismatch"]) if family=="stale_yield" else "current"
    stress=(family in ("oscillation_yield","spike_yield") or dt0!=1.0 or dt1!=1.0 or
            (family=="alias_accel" and index%2==1))
    return {"seed":seed,"split":split,"family":family,"group":GROUP[family],"index":index,
            "alias_id":alias_id,"history_A":pA,"history_B":pB,"dt":[dt0,dt1],
            "features":features,"smoothed_features":smooth,"history_status":status,"stress":stress,
            "label":label,"class_name":["ACTION_A","ACTION_B","NO_OP","YIELD"][label]}


def regen(seed, split):
    rng=random.Random(seed*1009+(13 if split=="train" else 29))
    regular=160 if split=="train" else 80
    rows=[]
    for family in FAMILIES:
        count=regular*2 if family=="alias_accel" else regular
        rows.extend(regen_example(rng,seed,split,family,i) for i in range(count))
    rng.shuffle(rows)
    return rows


def linear_logits(row, arm, state):
    source=row["smoothed_features"] if arm=="CAUSAL_SMOOTHED" else row["features"]
    allowed=set(ARMS[arm])
    values=[source[i] if i in allowed else 0.0 for i in range(9)]
    return [sum(values[j]*state["weight"][k][j] for j in range(9))+state["bias"][k] for k in range(4)]


def metric(rows, pred):
    labels=[r["label"] for r in rows]
    nonexec=[i for i,y in enumerate(labels) if y in (2,3)]
    noops=[i for i,y in enumerate(labels) if y==2]
    required=[i for i,y in enumerate(labels) if y in (0,1)]
    return {"accuracy":sum(a==b for a,b in zip(labels,pred))/len(rows),
            "false_executable_rate":sum(pred[i] in (0,1) for i in nonexec)/max(1,len(nonexec)),
            "unnecessary_action_rate":sum(pred[i] in (0,1) for i in noops)/max(1,len(noops)),
            "false_noop_required_rate":sum(pred[i]==2 for i in required)/max(1,len(required)),
            "rows":len(rows)}


def close(a,b,tol=2e-5):
    return abs(a-b)<=tol*max(1.0,abs(a),abs(b))


def audit(evidence, freeze, source_root):
    root=Path(evidence); errors=[]
    for name,expected in freeze["source_sha256"].items():
        data=(Path(source_root)/name).read_bytes()
        if sha(data)!=expected: errors.append("source_hash:"+name)
    run=json.loads((root/"RUN.json").read_text(encoding="utf-8"))
    if run.get("schema")!="confidence-trajectory-run-v1" or [x["seed"] for x in run.get("seeds",[])]!=SEEDS:
        errors.append("run_identity_or_seed_schedule")
    all_rows={arm:[] for arm in ARMS}; all_preds={arm:[] for arm in ARMS}
    seed_metrics=[]
    for seed,record in zip(SEEDS,run.get("seeds",[])):
        path=root/f"seed-{seed}"/"evidence.json"; raw=path.read_bytes()
        if sha(raw)!=record.get("evidence_sha256") or len(raw)!=record.get("evidence_bytes"):
            errors.append(f"{seed}:evidence_hash")
        doc=json.loads(raw)
        train=regen(seed,"train"); test=regen(seed,"test")
        if doc.get("train_rows")!=train: errors.append(f"{seed}:train_regeneration")
        if doc.get("test_rows")!=test: errors.append(f"{seed}:test_regeneration")
        if len(test)!=record.get("rows_test") or len(train)!=record.get("rows_train"):
            errors.append(f"{seed}:row_denominator")
        byarm={}
        for arm in ARMS:
            result=doc.get("arms",{}).get(arm,{})
            pred=result.get("predictions",[]); logits=result.get("logits",[])
            if len(pred)!=len(test) or len(logits)!=len(test):
                errors.append(f"{seed}:{arm}:prediction_denominator"); continue
            latencies=result.get("decision_latency_ms",[])
            if (len(latencies)!=len(test) or any(not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in latencies)
                    or result.get("state_bytes")!=len(canonical(result.get("state",{})))):
                errors.append(f"{seed}:{arm}:latency_or_state_size")
            elif latencies:
                ordered=sorted(latencies)
                if result.get("decision_latency_p50_ms")!=ordered[math.ceil(0.50*len(ordered))-1] or result.get("decision_latency_p95_ms")!=ordered[math.ceil(0.95*len(ordered))-1]:
                    errors.append(f"{seed}:{arm}:latency_quantile")
            expected_logits=[linear_logits(row,arm,result["state"]) for row in test]
            if any(len(got)!=4 or any(not close(got[j],want[j]) for j in range(4))
                   for got,want in zip(logits,expected_logits)):
                errors.append(f"{seed}:{arm}:logit_recompute")
            recomputed=[max(range(4),key=lambda c:logit[c]) for logit in expected_logits]
            for i,row in enumerate(test):
                if row["history_status"]!="current": recomputed[i]=3
            if pred!=recomputed: errors.append(f"{seed}:{arm}:prediction_or_fail_closed_gate")
            m=metric(test,pred); saved=result.get("metrics",{}).get("overall")
            if saved!=m: errors.append(f"{seed}:{arm}:metric_recompute")
            if record.get("metrics",{}).get(arm)!=result.get("metrics"):
                errors.append(f"{seed}:{arm}:run_summary_metrics")
            if record.get("decision_latency_p50_ms",{}).get(arm)!=result.get("decision_latency_p50_ms") or record.get("decision_latency_p95_ms",{}).get(arm)!=result.get("decision_latency_p95_ms") or record.get("state_bytes",{}).get(arm)!=result.get("state_bytes"):
                errors.append(f"{seed}:{arm}:run_summary_measurements")
            byarm[arm]={"overall":m,"alias":metric([r for r in test if r["group"]=="alias"],
                                                        [pred[i] for i,r in enumerate(test) if r["group"]=="alias"]),
                        "stress":metric([r for r in test if r["stress"]],
                                         [pred[i] for i,r in enumerate(test) if r["stress"]])}
            all_rows[arm].extend(test); all_preds[arm].extend(pred)
        if byarm: seed_metrics.append({"seed":seed,"arms":byarm})
    pooled={}
    for arm in ARMS:
        pred=all_preds[arm]; rows=all_rows[arm]
        pooled[arm]={"overall":metric(rows,pred),
                     "alias":metric([r for r in rows if r["group"]=="alias"],
                                    [pred[i] for i,r in enumerate(rows) if r["group"]=="alias"]),
                     "stress":metric([r for r in rows if r["stress"]],
                                     [pred[i] for i,r in enumerate(rows) if r["stress"]])}
    base=pooled["CURRENT_ONLY"]; accel=pooled["LEVEL_VELOCITY_ACCEL"]
    aliases_base=base["alias"]["false_executable_rate"]; aliases_accel=accel["alias"]["false_executable_rate"]
    gates={
        "alias_false_exec_relative_and_absolute_improvement": aliases_base-aliases_accel>=0.02 and aliases_accel<=0.8*aliases_base,
        "overall_accuracy_within_2pp": accel["overall"]["accuracy"]>=base["overall"]["accuracy"]-0.02,
        "overall_false_exec_not_higher": accel["overall"]["false_executable_rate"]<=base["overall"]["false_executable_rate"],
        "unnecessary_actions_down_10pp": accel["overall"]["unnecessary_action_rate"]<=base["overall"]["unnecessary_action_rate"]-0.10,
        "no_false_noop_on_required": accel["overall"]["false_noop_required_rate"]==0.0,
        "invalid_history_all_yield": all(p==3 for arm in ARMS for r,p in zip(all_rows[arm],all_preds[arm]) if r["history_status"]!="current"),
        "noisy_irregular_accuracy_within_2pp": accel["stress"]["accuracy"]>=base["stress"]["accuracy"]-0.02,
        "acceleration_beats_velocity_on_alias_by_5pp": (
            metric([r for r in all_rows["LEVEL_VELOCITY_ACCEL"] if r["group"]=="alias"],
                   [all_preds["LEVEL_VELOCITY_ACCEL"][i] for i,r in enumerate(all_rows["LEVEL_VELOCITY_ACCEL"]) if r["group"]=="alias"])["accuracy"]
            >= metric([r for r in all_rows["LEVEL_VELOCITY"] if r["group"]=="alias"],
                      [all_preds["LEVEL_VELOCITY"][i] for i,r in enumerate(all_rows["LEVEL_VELOCITY"]) if r["group"]=="alias"])["accuracy"]+0.05),
    }
    status="PASS_TRAJECTORY_SYSTEM1_SCOPED" if all(gates.values()) and not errors else "FAIL_OR_HOLD"
    result={"schema":"confidence-trajectory-audit-v1","status":status,"errors":errors,
            "gates":gates,"pooled":pooled,"per_seed":seed_metrics,"error_count":len(errors)}
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--evidence",required=True); p.add_argument("--freeze",required=True); p.add_argument("--output",required=True)
    p.add_argument("--source-root",required=True)
    a=p.parse_args(); freeze=json.loads(Path(a.freeze).read_text(encoding="utf-8")); result=audit(a.evidence,freeze,a.source_root)
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True); (out/"AUDIT.json").write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["status"],"error_count":result["error_count"],"gates":result["gates"]},sort_keys=True))
    raise SystemExit(0 if result["error_count"]==0 else 1)

