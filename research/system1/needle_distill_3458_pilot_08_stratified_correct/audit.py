"""Independent audit for paired pilot-08; does not import runner.py."""
import hashlib
import json
import math
import statistics

import torch
from torch import nn
from torch.nn import functional as F

SEEDS=(3480,3481,3482); LABELS=("CONTINUE","CORRECT","WATCH")
META={"intent":"track_target","scope":"local-servo","epoch":7}
TOL=1e-6


def balanced_class(label,n,seed):
    g=torch.Generator().manual_seed(seed)
    if label==0:
        xy=(torch.rand(n,2,generator=g)-.5)*.08; vel=(torch.rand(n,2,generator=g)-.5)*.08
        conf=.72+.28*torch.rand(n,1,generator=g); vis=torch.ones(n,1)
    elif label==1:
        sign=torch.where(torch.rand(n,1,generator=g)>.5,1.,-1.)
        dx=sign*(.15+.80*torch.rand(n,1,generator=g)); dy=(torch.rand(n,1,generator=g)-.5)*1.6
        xy=torch.cat((dx,dy),1); vel=(torch.rand(n,2,generator=g)-.5)*.4
        conf=.72+.28*torch.rand(n,1,generator=g); vis=torch.ones(n,1)
    elif label==2:
        xy=(torch.rand(n,2,generator=g)-.5)*2.; vel=(torch.rand(n,2,generator=g)-.5)*.8
        conf=.72*torch.rand(n,1,generator=g); vis=torch.randint(0,2,(n,1),generator=g).float()
    else: raise ValueError("unknown class")
    return torch.cat((xy,vel,conf,vis),1)


def shifted_class(label,n,seed,band=None):
    if label!=1: return balanced_class(label,n,seed)
    g=torch.Generator().manual_seed(seed); sign=torch.where(torch.rand(n,1,generator=g)>.5,1.,-1.)
    if band is None: lo,span=.071,.078
    elif band==0: lo,span=.071,.039
    elif band==1: lo,span=.110,.039
    else: raise ValueError("unknown band")
    dx=sign*(lo+span*torch.rand(n,1,generator=g)); dy=(torch.rand(n,1,generator=g)-.5)*.20
    vel=(torch.rand(n,2,generator=g)-.5)*.10; conf=.80+.20*torch.rand(n,1,generator=g); vis=torch.ones(n,1)
    return torch.cat((dx,dy,vel,conf,vis),1)


def teacher(rows):
    x=torch.as_tensor(rows,dtype=torch.float32); dx,dy,vx,vy,conf,vis=x.unbind(-1)
    watch=(conf<.72)|(vis<.5); settled=(dx.abs()<.06)&(dy.abs()<.06)&((vx.abs()+vy.abs())<.12)
    return torch.where(watch,2,torch.where(settled,0,1)).long().tolist()


class AuditNeedle(nn.Module):
    def __init__(self):
        super().__init__(); self.net=nn.Sequential(nn.Linear(6,16),nn.Tanh(),nn.Linear(16,16),nn.Tanh(),nn.Linear(16,3))


def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def state_tensors(state):
    out={}
    for name,entry in state.items():
        t=torch.tensor(entry["values"],dtype=torch.float32)
        if t.numel()!=math.prod(entry["shape"]): raise ValueError("model_state_shape")
        if not torch.isfinite(t).all(): raise ValueError("nonfinite_weight")
        out[name]=t.reshape(entry["shape"])
    return out


def training_rows_expected(seed,augmented):
    classes=[balanced_class(c,2048,seed+10+c) for c in range(3)]
    if augmented: classes[1]=torch.cat((classes[1][:1024],shifted_class(1,512,seed+40,0),shifted_class(1,512,seed+41,1)),0)
    x=torch.cat(classes,0)
    return x,teacher(x)


def expected_batch_hash(seed):
    g=torch.Generator().manual_seed(seed+30)
    batches=[torch.randint(6144,(64,),generator=g).tolist() for _ in range(700)]
    return canonical_hash(batches)


def state_forward(rows,state):
    x=torch.tensor(rows,dtype=torch.float32)
    for layer in (0,2,4):
        x=F.linear(x,state[f"net.{layer}.weight"],state[f"net.{layer}.bias"])
        if layer!=4: x=torch.tanh(x)
    return x.argmax(-1).tolist()


def reason(meta,x):
    if meta!=META: return "YIELD_METADATA"
    if not all(math.isfinite(float(v)) for v in x): return "YIELD_NONFINITE"
    dx,dy,vx,vy,conf,vis=map(float,x)
    if max(abs(dx),abs(dy))>1.25 or max(abs(vx),abs(vy))>1.0 or not 0<=conf<=1 or vis not in (0.,1.): return "YIELD_ENVELOPE"
    if (abs(conf-.72)<.03 or abs(abs(dx)-.06)<.01 or abs(abs(dy)-.06)<.01 or abs(abs(vx)+abs(vy)-.12)<.02): return "YIELD_BOUNDARY"
    return "PROPOSAL"


def expected_suite(seed,shifted):
    rows=[]; labels=[]
    for c in range(3):
        gen=shifted_class if shifted else balanced_class
        x=gen(c,1024,seed+(100 if shifted else 200)+c)
        rows.extend(x.tolist()); labels.extend(teacher(x))
    return rows,labels


def boundary_rows():
    rows=[]
    for i in range(256):
        d=.25+(i%17)*.001
        rows.extend([[d,.2,.01,.02,.719,1.],[d,.2,.01,.02,.721,1.]])
        rows.extend([[.059,0.,.02,.02,.9,1.],[.061,0.,.02,.02,.9,1.]])
        rows.extend([[0.,0.,.059,.06,.9,1.],[0.,0.,.061,.06,.9,1.]])
    return torch.tensor(rows,dtype=torch.float32).tolist()


def invalid_expected():
    return [("stale_epoch",META|{"epoch":8},[.2,.2,0.,0.,.9,1.],"YIELD_METADATA"),
            ("wrong_scope",META|{"scope":"other"},[.2,.2,0.,0.,.9,1.],"YIELD_METADATA"),
            ("wrong_intent",{"intent":"other","scope":META["scope"],"epoch":META["epoch"]},[.2,.2,0.,0.,.9,1.],"YIELD_METADATA"),
            ("out_of_envelope",META,[1.3,0.,0.,0.,.9,1.],"YIELD_ENVELOPE"),
            ("nonfinite",META,["NaN",0.,0.,0.,.9,1.],"YIELD_NONFINITE")]


def summarize(rows):
    accepted=[r for r in rows if r["proposal"] is not None]
    correct=sum(r["proposal"]==LABELS[r["y"]] for r in accepted)
    false=sum(r["proposal"]=="CORRECT" and r["y"]!=1 for r in rows)
    by={}
    for c,name in enumerate(LABELS):
        sub=rows[c*1024:(c+1)*1024]; ac=[r for r in sub if r["proposal"] is not None]
        by[name]={"n":len(sub),"accepted":len(ac),"coverage":len(ac)/1024,
                  "accepted_recall":sum(r["proposal"]==name for r in ac)/max(1,len(ac)),
                  "accepted_accuracy":sum(r["proposal"]==LABELS[r["y"]] for r in ac)/max(1,len(ac)),
                  "false_correct":sum(r["proposal"]=="CORRECT" and r["y"]!=1 for r in sub)}
    return {"accepted":len(accepted),"accuracy":correct/max(1,len(accepted)),
            "false_correct":false,"false_correct_fraction_all_rows":false/len(rows),"by_class":by}


def quality_gate(metrics):
    return (metrics["accuracy"]>=.95
            and all(metrics["by_class"][n]["coverage"]>=.75 and metrics["by_class"][n]["accepted_recall"]>=.95 for n in LABELS)
            and metrics["false_correct_fraction_all_rows"]<=.005)


def near_bounds(x):
    dx,dy,vx,vy,conf,vis=map(float,x)
    return .071-TOL<=abs(dx)<=.149+TOL and abs(dy)<=.10+TOL and abs(vx)<=.05+TOL and abs(vy)<=.05+TOL and .80-TOL<=conf<=1+TOL and vis==1.


def audit(payload,raw):
    errors=[]; reports=[]; overall=[]
    raw_sha256=hashlib.sha256(raw).hexdigest()
    if payload.get("allocation")!="needle-intent-distill-3458-pilot-08-stratified-correct": errors.append("allocation")
    contract=payload.get("training_contract",{})
    required={"architecture":"6->16->16->3 tanh MLP","optimizer":"AdamW","lr":.008,"steps":700,
              "batch_size":64,"arms":["balanced_control","targeted_augmented"],"device":"CPU"}
    if contract!=required: errors.append("training_contract")
    records=payload.get("seeds",[]); shifted_correct_recalls=[]
    if [r.get("seed") for r in records]!=list(SEEDS): return {"audit":"FAIL","errors":errors+["seed_set"]}
    for rec,seed in zip(records,SEEDS):
        pref=f"seed_{seed}"; arm_states={}; arm_out={}; seed_errors_before=len(errors)
        arms=rec.get("arms",{})
        if set(arms)!={"balanced_control","targeted_augmented"}: errors.append(pref+":arm_set")
        torch.manual_seed(seed); init_model=AuditNeedle()
        init_record={k:{"shape":list(v.shape),"values":[float(x) for x in v.detach().cpu().reshape(-1)]} for k,v in init_model.state_dict().items()}
        init_hash=canonical_hash(init_record)
        batches_hash=expected_batch_hash(seed)
        for arm in ("balanced_control","targeted_augmented"):
            data=arms.get(arm,{})
            if data.get("optimizer_steps")!=700 or data.get("train_rows")!=6144: errors.append(pref+":"+arm+":protocol")
            if data.get("initial_state_sha256")!=init_hash: errors.append(pref+":"+arm+":initial_weights")
            if data.get("correct_near_boundary_rows")!=(1024 if arm=="targeted_augmented" else 0): errors.append(pref+":"+arm+":mixture_count")
            if data.get("minibatch_index_stream_sha256")!=batches_hash: errors.append(pref+":"+arm+":minibatch_stream")
            expected_x,expected_y=training_rows_expected(seed,arm=="targeted_augmented")
            x_hash=canonical_hash({"shape":list(expected_x.shape),"rows":expected_x.tolist()})
            y_hash=canonical_hash(expected_y)
            if data.get("train_features_sha256")!=x_hash: errors.append(pref+":"+arm+":training_features")
            if data.get("train_labels_sha256")!=y_hash: errors.append(pref+":"+arm+":training_labels")
            try:
                state=state_tensors(data["model_state"]); digest=canonical_hash(data["model_state"])
                if digest!=data.get("model_state_sha256"): errors.append(pref+":"+arm+":state_digest")
                expected_shapes={"net.0.weight":[16,6],"net.0.bias":[16],"net.2.weight":[16,16],"net.2.bias":[16],"net.4.weight":[3,16],"net.4.bias":[3]}
                if {k:list(v.shape) for k,v in state.items()}!=expected_shapes: errors.append(pref+":"+arm+":architecture_shape")
                arm_states[arm]=state; arm_out[arm]={"suites":{}}
            except (KeyError,TypeError,ValueError,RuntimeError): errors.append(pref+":"+arm+":state_invalid")
        per_arm={a:{"suites":{},"boundary_yield":0,"invalid_yield":0,"latency_p95_ms":None,"gates":{}} for a in arm_states}
        if len(arm_states)!=2: continue
        for suite_name,is_shift in (("iid_control",False),("near_boundary_shift",True)):
            try: expected,labels=expected_suite(seed,is_shift)
            except Exception: errors.append(pref+":"+suite_name+":generator"); continue
            got=rec.get("suites",{}).get(suite_name,{}).get("rows",[])
            if len(got)!=len(expected): errors.append(pref+":"+suite_name+":row_count"); continue
            derived={a:[] for a in arm_states}
            for i,(row,x,y) in enumerate(zip(got,expected,labels)):
                actual=row.get("x",[])
                if len(actual)!=6 or any(not math.isfinite(float(v)) or abs(float(v)-float(e))>TOL for v,e in zip(actual,x)):
                    errors.append(f"{pref}:{suite_name}:{i}:features")
                if row.get("y")!=y: errors.append(f"{pref}:{suite_name}:{i}:label")
                for arm,state in arm_states.items():
                    reason_expected=reason(META,x)
                    pred=state_forward([x],state)[0]
                    proposal=LABELS[pred] if reason_expected=="PROPOSAL" else None
                    stored=row.get(arm,{})
                    if stored.get("reason")!=reason_expected or stored.get("proposal")!=proposal:
                        errors.append(f"{pref}:{suite_name}:{i}:{arm}:decision")
                    derived[arm].append({"y":y,"proposal":proposal,"reason":reason_expected})
                if is_shift and 1024<=i<2048 and not near_bounds(x): errors.append(f"{pref}:shift_bounds:{i}")
            for arm in arm_states: per_arm[arm]["suites"][suite_name]=summarize(derived[arm])
        brow=rec.get("boundary",[]); expected_b=boundary_rows(); labels_b=teacher(expected_b)
        if len(brow)!=1536: errors.append(pref+":boundary_count")
        else:
            for i,(row,x,y) in enumerate(zip(brow,expected_b,labels_b)):
                if len(row.get("x",[]))!=6 or any(abs(float(a)-float(e))>TOL for a,e in zip(row["x"],x)): errors.append(f"{pref}:boundary_features:{i}")
                if row.get("y")!=y: errors.append(f"{pref}:boundary_label:{i}")
                for arm,state in arm_states.items():
                    rr=reason(META,x); proposal=LABELS[state_forward([x],state)[0]] if rr=="PROPOSAL" else None
                    v=row.get(arm,{})
                    if v.get("reason")!=rr or v.get("proposal")!=proposal: errors.append(f"{pref}:boundary_decision:{i}:{arm}")
                    if v.get("reason")=="YIELD_BOUNDARY" and v.get("proposal") is None: per_arm[arm]["boundary_yield"]+=1
        invalid=rec.get("invalid_controls",[]); expected_invalid=invalid_expected()
        if len(invalid)!=5: errors.append(pref+":invalid_count")
        else:
            for i,(row,(case,meta,x,want_reason)) in enumerate(zip(invalid,expected_invalid)):
                if row.get("case")!=case or row.get("meta")!=meta: errors.append(f"{pref}:invalid_identity:{case}")
                observed=row.get("x",[])
                if not isinstance(observed,list) or len(observed)!=6:
                    errors.append(f"{pref}:invalid_width:{case}"); observed=[]
                for k,(a,e) in enumerate(zip(observed,x)):
                    if e=="NaN":
                        if a!="NaN": errors.append(f"{pref}:invalid_nan:{case}")
                    elif not math.isfinite(float(a)) or abs(float(a)-float(e))>TOL: errors.append(f"{pref}:invalid_feature:{case}:{k}")
                for arm in arm_states:
                    out=row.get(arm,{})
                    if out.get("reason")!=want_reason or out.get("proposal") is not None: errors.append(f"{pref}:invalid_decision:{case}:{arm}")
                    else: per_arm[arm]["invalid_yield"]+=1
        for arm in arm_states:
            times=rec.get("latency_ms",{}).get(arm,[])
            if len(times)!=2000 or not all(math.isfinite(float(v)) and float(v)>=0 for v in times): errors.append(pref+":"+arm+":latency_samples")
            else:
                p95=sorted(map(float,times))[int(.95*(len(times)-1))]; per_arm[arm]["latency_p95_ms"]=p95
                if p95>=60: errors.append(pref+":"+arm+":latency_gate")
            suite=per_arm[arm]["suites"]
            shift=suite.get("near_boundary_shift",{}); iid=suite.get("iid_control",{})
            per_arm[arm]["gates"]={"shift_quality":quality_gate(shift),"iid_accuracy":iid.get("accuracy",0)>=.95,
              "boundary_yield":per_arm[arm]["boundary_yield"]==1536,
              "invalid_yield":per_arm[arm]["invalid_yield"]==5,
              "latency":per_arm[arm]["latency_p95_ms"] is not None and per_arm[arm]["latency_p95_ms"]<60}
        ctrl=per_arm.get("balanced_control",{}); treatment=per_arm.get("targeted_augmented",{})
        cs=ctrl.get("suites",{}); ts=treatment.get("suites",{})
        lift=ts.get("near_boundary_shift",{}).get("by_class",{}).get("CORRECT",{}).get("accepted_recall",0)-cs.get("near_boundary_shift",{}).get("by_class",{}).get("CORRECT",{}).get("accepted_recall",0)
        shifted_correct_recalls.append(ts.get("near_boundary_shift",{}).get("by_class",{}).get("CORRECT",{}).get("accepted_recall",0))
        iid_drop=cs.get("iid_control",{}).get("accuracy",0)-ts.get("iid_control",{}).get("accuracy",0)
        tgate=treatment.get("gates",{})
        treatment_pass=all(tgate.get(k,False) for k in ("shift_quality","iid_accuracy","boundary_yield","invalid_yield","latency")) and lift>=.10 and iid_drop<=.02
        overall.append(treatment_pass)
        reports.append({"seed":seed,"arms":per_arm,"paired_correct_recall_lift":lift,"iid_accuracy_drop_control_minus_treatment":iid_drop,"treatment_pass":treatment_pass})
        if len(errors)==seed_errors_before:
            pass
    recall_std=statistics.pstdev(shifted_correct_recalls) if len(shifted_correct_recalls)==3 else float("inf")
    scientific="PASS_STRATIFIED_CORRECT_AUGMENTATION_SCOPED" if len(overall)==3 and all(overall) and recall_std<=.05 else "FAIL_STRATIFIED_CORRECT_AUGMENTATION"
    return {"audit":"PASS" if not errors else "FAIL","errors":errors,"decision_recomputed":scientific,
            "treatment_seed_gates":overall,"shifted_correct_recall_std":recall_std,"reports":reports,"feature_tolerance":TOL,
            "cross_suite_feature_equality_asserted":False,"raw_result_sha256":raw_sha256}
