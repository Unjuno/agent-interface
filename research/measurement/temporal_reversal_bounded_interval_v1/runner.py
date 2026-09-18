from __future__ import annotations
import argparse, json, os, time
from collections import defaultdict
from common import *


def make_trace(age_ms: int, post_dir: int, phase_us: int, traj_id: str):
    ts = sample_times_us(phase_us)
    exact = [position_exact_u(t, age_ms, post_dir) for t in ts]
    jit = [jitter_u(traj_id, t) for t in ts]
    obs = [x+j for x,j in zip(exact,jit)]
    return ts, exact, jit, obs


def row(age_ms, post_dir, phase_us, estimator_name, traj_id):
    ts, exact, jit, obs = make_trace(age_ms, post_dir, phase_us, traj_id)
    if len(obs) < 3:
        raise RuntimeError("need >=3 samples")
    if estimator_name == "STRICT_EXACT":
        pred, ops = strict_exact_estimator(obs)
    elif estimator_name == "BOUNDED_INTERVAL":
        pred, ops = bounded_interval_estimator(obs)
    else:
        raise ValueError(estimator_name)
    d_new = obs[0]-obs[1]
    d_prev = obs[1]-obs[2]
    return {
        "trajectory_id": traj_id,
        "age_ms": age_ms,
        "post_dir": post_dir,
        "phase_us": phase_us,
        "estimator": estimator_name,
        "sample_times_us": ts,
        "exact_positions_u": exact,
        "jitter_u": jit,
        "observed_positions_u": obs,
        "d_new_u": d_new,
        "d_prev_u": d_prev,
        "prediction": pred,
        "oracle": post_dir,
        "correct": pred == post_dir,
        "unknown": pred == UNKNOWN,
        "wrong_direction": pred not in (UNKNOWN, post_dir),
        "ops": ops,
        "identifiability_ceiling": IDENT_CEILING.get(age_ms),
        "position_jitter_bound_u": POSITION_JITTER_BOUND,
        "displacement_error_bound_u": DISP_ERROR_BOUND,
    }


def summarize(rows):
    cells = defaultdict(lambda: {"n":0,"correct":0,"unknown":0,"wrong":0,"ops":0})
    for r in rows:
        k=(r["estimator"],r["age_ms"])
        c=cells[k]
        c["n"]+=1; c["correct"]+=int(r["correct"]); c["unknown"]+=int(r["unknown"]); c["wrong"]+=int(r["wrong_direction"]); c["ops"]+=r["ops"]
    out={}
    for (est,age),c in sorted(cells.items()):
        out.setdefault(est,{})[str(age)]={
            "n":c["n"],
            "accuracy":c["correct"]/c["n"],
            "unknown_rate":c["unknown"]/c["n"],
            "wrong_direction_rate":c["wrong"]/c["n"],
            "mean_ops":c["ops"]/c["n"],
        }
    return out


def run_formal(out_path):
    rows=[]
    for age in FORMAL_AGES_MS:
        for post_dir in (-1,1):
            for phase_ms in range(100):
                phase_us=phase_ms*1000
                traj_id=f"F|a={age}|d={post_dir}|p={phase_ms}"
                for est in ("STRICT_EXACT","BOUNDED_INTERVAL"):
                    rows.append(row(age,post_dir,phase_us,est,traj_id))
    payload={
        "task":"TEMPORAL-REVERSAL-BOUNDED-INTERVAL-R1-20260918-006",
        "mode":"formal",
        "formal_invocation":1,
        "reruns":0,
        "row_count":len(rows),
        "summary":summarize(rows),
        "rows":rows,
    }
    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(payload,f,separators=(",",":"),sort_keys=True)
    return payload


def run_construction(out_path):
    rows=[]
    for age in (40,110,175):
        for post_dir in (-1,1):
            for phase_us in (500, 33_500, 66_500, 99_500):
                traj_id=f"C|a={age}|d={post_dir}|p_us={phase_us}"
                for est in ("STRICT_EXACT","BOUNDED_INTERVAL"):
                    rows.append(row(age,post_dir,phase_us,est,traj_id))
    payload={"task":"TEMPORAL-REVERSAL-BOUNDED-INTERVAL-R1-20260918-006","mode":"construction","formal_invocation":0,"reruns":0,"row_count":len(rows),"summary":summarize(rows),"rows":rows}
    with open(out_path,"w",encoding="utf-8") as f: json.dump(payload,f,separators=(",",":"),sort_keys=True)
    return payload


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("mode",choices=["construction","formal"]); ap.add_argument("out")
    a=ap.parse_args()
    p=run_construction(a.out) if a.mode=="construction" else run_formal(a.out)
    print(json.dumps({"mode":p["mode"],"row_count":p["row_count"],"summary":p["summary"]},sort_keys=True))
if __name__=="__main__": main()
