"""Corrected independent audit for Issue #3899; no runner import or training."""
import hashlib
import json
import math
import sys
from pathlib import Path

import torch
from torch.nn import functional as F

EXPECTED_SHA256 = "0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7"
EXPECTED_BLOB = "d6259323e86dba3ae12f76765aed62ab9d78dfa8"
SEEDS = (3467, 3468, 3469)
LABELS = ("CONTINUE", "CORRECT", "WATCH")
META = {"intent": "track_target", "scope": "local-servo", "epoch": 7}


def balanced(label, n, seed):
    g = torch.Generator().manual_seed(seed)
    if label == 0:
        xy = (torch.rand(n, 2, generator=g) - .5) * .08
        vel = (torch.rand(n, 2, generator=g) - .5) * .08
        conf, vis = .72 + .28 * torch.rand(n, 1, generator=g), torch.ones(n, 1)
    elif label == 1:
        sign = torch.where(torch.rand(n, 1, generator=g) > .5, 1., -1.)
        dx = sign * (.15 + .80 * torch.rand(n, 1, generator=g))
        dy = (torch.rand(n, 1, generator=g) - .5) * 1.6
        xy = torch.cat((dx, dy), 1)
        vel = (torch.rand(n, 2, generator=g) - .5) * .4
        conf, vis = .72 + .28 * torch.rand(n, 1, generator=g), torch.ones(n, 1)
    elif label == 2:
        xy = (torch.rand(n, 2, generator=g) - .5) * 2.
        vel = (torch.rand(n, 2, generator=g) - .5) * .8
        conf = .72 * torch.rand(n, 1, generator=g)
        vis = torch.randint(0, 2, (n, 1), generator=g).float()
    else:
        raise ValueError("unknown class")
    return torch.cat((xy, vel, conf, vis), 1)


def shifted(label, n, seed):
    if label != 1:
        return balanced(label, n, seed)
    g = torch.Generator().manual_seed(seed)
    sign = torch.where(torch.rand(n, 1, generator=g) > .5, 1., -1.)
    dx = sign * (.071 + .078 * torch.rand(n, 1, generator=g))
    dy = (torch.rand(n, 1, generator=g) - .5) * .20
    vel = (torch.rand(n, 2, generator=g) - .5) * .10
    conf, vis = .80 + .20 * torch.rand(n, 1, generator=g), torch.ones(n, 1)
    return torch.cat((dx, dy, vel, conf, vis), 1)


def teacher(rows):
    x = torch.as_tensor(rows, dtype=torch.float32)
    dx, dy, vx, vy, conf, vis = x.unbind(-1)
    watch = (conf < .72) | (vis < .5)
    settled = (dx.abs() < .06) & (dy.abs() < .06) & ((vx.abs() + vy.abs()) < .12)
    return torch.where(watch, 2, torch.where(settled, 0, 1)).long().tolist()


def vector_errors(actual, expected, tolerance=1e-6):
    if len(actual) != 6 or len(expected) != 6:
        return ["feature_width"]
    return [f"feature_{i}_mismatch" for i, (a, e) in enumerate(zip(actual, expected))
            if not math.isfinite(float(a)) or not math.isfinite(float(e)) or abs(float(a)-float(e)) > tolerance]


def blob_sha1(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def canonical(data):
    return data.replace(b"\r\n", b"\n")


def predictions(rows, model_state):
    state = {}
    for name, entry in model_state.items():
        tensor = torch.tensor(entry["values"], dtype=torch.float32)
        if tensor.numel() != math.prod(entry["shape"]):
            raise ValueError("bad model shape")
        state[name] = tensor.reshape(entry["shape"])
    x = torch.tensor(rows, dtype=torch.float32)
    for layer in (0, 2, 4):
        x = F.linear(x, state[f"net.{layer}.weight"], state[f"net.{layer}.bias"])
        if layer != 4:
            x = torch.tanh(x)
    return x.argmax(-1).tolist()


def reason(row):
    if not all(math.isfinite(float(v)) for v in row):
        return "YIELD_NONFINITE"
    dx, dy, vx, vy, conf, vis = map(float, row)
    if max(abs(dx), abs(dy)) > 1.25 or max(abs(vx), abs(vy)) > 1.0 or not 0 <= conf <= 1 or vis not in (0., 1.):
        return "YIELD_ENVELOPE"
    if (abs(conf-.72) < .03 or abs(abs(dx)-.06) < .01 or abs(abs(dy)-.06) < .01
            or abs(abs(vx)+abs(vy)-.12) < .02):
        return "YIELD_BOUNDARY"
    return "PROPOSAL"


def summary(rows):
    accepted = [r for r in rows if r["proposal"] is not None]
    correct = sum(r["proposal"] == LABELS[r["y"]] for r in accepted)
    false_correct = sum(r["proposal"] == "CORRECT" and r["y"] != 1 for r in rows)
    by_class = {}
    for c, name in enumerate(LABELS):
        subset = rows[c*1024:(c+1)*1024]
        ac = [r for r in subset if r["proposal"] is not None]
        by_class[name] = {"n": len(subset), "accepted": len(ac),
                          "coverage": len(ac)/1024,
                          "accepted_recall": sum(r["proposal"] == name for r in ac)/max(1,len(ac)),
                          "accepted_accuracy": sum(r["proposal"] == LABELS[r["y"]] for r in ac)/max(1,len(ac)),
                          "false_correct": sum(r["proposal"] == "CORRECT" and r["y"] != 1 for r in subset)}
    return {"accepted": len(accepted), "accuracy": correct/max(1,len(accepted)),
            "false_correct": false_correct, "false_correct_fraction_all_rows": false_correct/len(rows),
            "by_class": by_class}


def boundary_rows():
    rows=[]
    for i in range(256):
        d=.25+(i%17)*.001
        rows.extend([[d,.2,.01,.02,.719,1.],[d,.2,.01,.02,.721,1.]])
        rows.extend([[.059,0.,.02,.02,.9,1.],[.061,0.,.02,.02,.9,1.]])
        rows.extend([[0.,0.,.059,.06,.9,1.],[0.,0.,.061,.06,.9,1.]])
    return torch.tensor(rows,dtype=torch.float32).tolist()


def expected_suite(seed, use_shift):
    rows = []
    for cls in range(3):
        gen = shifted if use_shift else balanced
        rows.extend(gen(cls, 1024, seed + (100 if use_shift else 200) + cls).tolist())
    return rows


def audit(payload, raw):
    errors = []
    raw = canonical(raw)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256: errors.append("raw_sha256")
    if blob_sha1(raw) != EXPECTED_BLOB: errors.append("raw_git_blob")
    if payload.get("allocation") != "needle-intent-distill-3458-pilot-06-isolated-shift-audit": errors.append("allocation")
    records = payload.get("seeds", [])
    if [r.get("seed") for r in records] != list(SEEDS):
        return {"audit":"FAIL", "errors":errors+["seed_set"]}
    gates, reports = [], []
    for record, seed in zip(records, SEEDS):
        prefix=f"seed_{seed}"
        state_bytes=json.dumps(record["model_state"],sort_keys=True,separators=(",",":")).encode()
        if hashlib.sha256(state_bytes).hexdigest()!=record.get("model_state_sha256"): errors.append(prefix+":weight_digest")
        checked={}
        try:
            for suite_name, use_shift in (("iid_control",False),("near_boundary_shift",True)):
                suite=record[suite_name]
                exp=expected_suite(seed,use_shift)
                got=suite.get("rows",[])
                if suite.get("name")!=suite_name or len(got)!=len(exp):
                    errors.append(prefix+":"+suite_name+":row_count_or_name"); continue
                labels=teacher(exp)
                preds=predictions(exp,record["model_state"])
                derived=[]
                for i,(r,x,y,p) in enumerate(zip(got,exp,labels,preds)):
                    for fe in vector_errors(r.get("x",[]),x): errors.append(f"{prefix}:{suite_name}:{i}:{fe}")
                    if r.get("y")!=y: errors.append(f"{prefix}:{suite_name}:{i}:label")
                    why=reason(x)
                    proposal=LABELS[p] if why=="PROPOSAL" else None
                    if r.get("reason")!=why or r.get("proposal")!=proposal: errors.append(f"{prefix}:{suite_name}:{i}:decision")
                    derived.append({"proposal":proposal,"reason":why,"y":y})
                checked[suite_name]=summary(derived)
                if use_shift:
                    for i,x in enumerate(exp[1024:2048]):
                        dx,dy,vx,vy,conf,vis=x
                        if not .071-1e-6<=abs(dx)<=.149+1e-6: errors.append(f"{prefix}:shift_dx:{i}")
                        if abs(dy)>.10+1e-6: errors.append(f"{prefix}:shift_dy:{i}")
                        if abs(vx)>.05+1e-6 or abs(vy)>.05+1e-6: errors.append(f"{prefix}:shift_velocity:{i}")
                        if not .80-1e-6<=conf<=1+1e-6: errors.append(f"{prefix}:shift_confidence:{i}")
                        if vis!=1.: errors.append(f"{prefix}:shift_visibility:{i}")
                    s=checked[suite_name]
                    gates.append(s["accuracy"]>=.95 and all(s["by_class"][name]["coverage"]>=.75 and s["by_class"][name]["accepted_recall"]>=.95 for name in LABELS) and s["false_correct_fraction_all_rows"]<=.005)
            expected_boundary=boundary_rows()
            actual_boundary=record.get("boundary",[])
            if len(actual_boundary)!=len(expected_boundary): errors.append(prefix+":boundary_count")
            else:
                boundary_labels=teacher(expected_boundary)
                for i,(actual,features,label) in enumerate(zip(actual_boundary,expected_boundary,boundary_labels)):
                    if vector_errors(actual.get("x",[]),features): errors.append(f"{prefix}:boundary_features:{i}")
                    if actual.get("y")!=label or actual.get("reason")!="YIELD_BOUNDARY" or actual.get("proposal") is not None:
                        errors.append(f"{prefix}:boundary_decision:{i}")
            expected_invalid=[
                ("stale_epoch",META|{"epoch":8},[.2,.2,0.,0.,.9,1.],"YIELD_METADATA"),
                ("wrong_scope",META|{"scope":"other"},[.2,.2,0.,0.,.9,1.],"YIELD_METADATA"),
                ("wrong_intent",{"intent":"other","scope":META["scope"],"epoch":META["epoch"]},[.2,.2,0.,0.,.9,1.],"YIELD_METADATA"),
                ("out_of_envelope",META,[1.3,0.,0.,0.,.9,1.],"YIELD_ENVELOPE"),
                ("nonfinite",META,["NaN",0.,0.,0.,.9,1.],"YIELD_NONFINITE")]
            invalid=record.get("invalid_controls",[])
            if len(invalid)!=len(expected_invalid): errors.append(prefix+":invalid_count")
            else:
                for actual,(case,meta,features,why) in zip(invalid,expected_invalid):
                    if actual.get("case")!=case or actual.get("meta")!=meta or actual.get("reason")!=why or actual.get("proposal") is not None:
                        errors.append(prefix+":invalid_control:"+case)
                    if actual.get("x")!=features: errors.append(prefix+":invalid_features:"+case)
            latency=record.get("latency_ms",[])
            if len(latency)!=2000 or not all(math.isfinite(float(v)) and float(v)>=0 for v in latency):
                errors.append(prefix+":latency_samples")
            elif sorted(float(v) for v in latency)[int(.95*(len(latency)-1))]>=60:
                errors.append(prefix+":latency_gate")
            reports.append({"seed":seed,**checked})
        except (KeyError,TypeError,ValueError,RuntimeError,IndexError) as exc:
            errors.append(prefix+":malformed_payload:"+type(exc).__name__)
    decision="FAIL_NEAR_BOUNDARY_SHIFT" if len(gates)==3 and not all(gates) else "PASS_OR_INCOMPLETE"
    return {"audit":"PASS" if not errors else "FAIL","errors":errors,
            "formal_result_sha256":EXPECTED_SHA256,"formal_result_git_blob_sha1":EXPECTED_BLOB,
            "decision_recomputed":decision,"seed_numeric_gates":gates,"reports":reports,
            "feature_columns_reconstructed_per_suite_seed":18432,
            "cross_suite_covariate_equality_asserted":False}


def self_test():
    expected=[.10,-.05,.02,-.01,.90,1.]
    for col in range(6):
        changed=expected.copy(); changed[col]+=.01
        assert vector_errors(changed,expected)==[f"feature_{col}_mismatch"]
    # In the frozen treatment velocity and confidence are intentionally changed;
    # those suite-specific covariates must not be compared for equality.
    iid=balanced(1,1,123).tolist()[0]
    shifted_row=shifted(1,1,123).tolist()[0]
    assert iid[2:5] != shifted_row[2:5]
    assert vector_errors(shifted_row,shifted(1,1,123).tolist()[0])==[]
    print(json.dumps({"construction":"PASS","six_feature_corruptions_rejected":6,
                      "suite_specific_covariates_allowed":True},sort_keys=True))


if __name__=="__main__":
    if "--self-test" in sys.argv: self_test(); raise SystemExit(0)
    source=Path(sys.argv[1]); raw=source.read_bytes(); payload=json.loads(raw.decode("utf-8"))
    result=audit(payload,raw); encoded=(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n").encode()
    if "--output" in sys.argv:
        target=Path(sys.argv[sys.argv.index("--output")+1])
        with target.open("xb") as stream: stream.write(encoded)
    sys.stdout.buffer.write(encoded)
    if result["audit"]!="PASS": raise SystemExit(2)
