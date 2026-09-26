from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


REQUIRED = {
    "monotonic_useful_convergence", "monotonic_divergence", "high_decelerating_reversal",
    "low_confidence_accelerating_correct", "plateau", "overshoot", "oscillation",
    "transient_spike", "stale_previous_sample", "epoch_change", "missing_sample",
    "irregular_sample_intervals", "self_correcting_state", "uncertain_state",
    "action_required_state", "current_level_alias", "second_order_alias",
}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def calc(p, t):
    p0,p1,p2=p; t0,t1,t2=t
    d1,d2=t1-t0,t2-t1
    v=(p2-p1)/d2
    a=2*(v-(p1-p0)/d1)/(d1+d2)
    q0,q1,q2=p0,(p0+p1)/2,(p0+p1+p2)/3
    qv=(q2-q1)/d2
    qa=2*(qv-(q1-q0)/d1)/(d1+d2)
    return (p2,), (p2,v), (p2,v,a), (q2,qv,qa)


def noise_oracle():
    s=(-.01,0,.01); sums=[0.0,0.0,0.0]; n=0
    for x,y,z in itertools.product(s,repeat=3):
        v=z-y; a=z-2*y+x
        q0,q1,q2=x,(x+y)/2,(x+y+z)/3
        qa=q2-2*q1+q0
        sums[0]+=v*v; sums[1]+=a*a; sums[2]+=qa*qa; n+=1
    return {"noise_grid":list(s),"triples":n,"velocity_rms":math.sqrt(sums[0]/n),
            "raw_acceleration_rms":math.sqrt(sums[1]/n),
            "causally_smoothed_acceleration_rms":math.sqrt(sums[2]/n)}


def audit(result_path: Path, source_dir: Path):
    d=json.loads(result_path.read_text()); errors=[]; rows=d.get("rows",[])
    if d.get("schema")!="issue4588-confidence-trajectory-construction-v1": errors.append("schema")
    if d.get("allocation")!="issue-4588-trajectory-20260927-01": errors.append("allocation")
    if (d.get("formal_invocations"),d.get("reruns"),d.get("replacements"),d.get("tuning_after_freeze"))!=(1,0,0,0): errors.append("invocation_counts")
    if not isinstance(rows,list) or d.get("row_count")!=len(rows): return {"pass":False,"errors":errors+["row_count"]}
    if len({r.get("case_id") for r in rows})!=len(rows): errors.append("duplicate_case_id")
    families={r.get("family") for r in rows}
    if not REQUIRED.issubset(families): errors.append("required_transition_families")
    if d.get("transition_families")!=sorted(families): errors.append("family_manifest")
    if any(r.get("label") not in {"ACTION","NO_OP","YIELD"} for r in rows): errors.append("typed_label")
    invalid=[r for r in rows if r.get("validity")!="valid" or any(x is None for x in r.get("p",()))]
    if not invalid or any(r.get("label")!="YIELD" for r in invalid): errors.append("invalid_history_not_yield")
    by_id={r["case_id"]:r for r in rows}
    current_alias=second_alias=curvature_separated=0
    for i in range(1,5):
        tri=[by_id.get(f"level-{i}-{s}") for s in ("rise","fall","plateau")]
        if any(x is None for x in tri): errors.append("missing_level_alias"); continue
        if len({x["p"][2] for x in tri})==1 and len({x["label"] for x in tri})==3: current_alias+=1
        pair=[by_id.get(f"curvature-{i}-{s}") for s in ("flat","positive")]
        if any(x is None for x in pair): errors.append("missing_curvature_alias"); continue
        f=calc(pair[0]["p"],pair[0]["times"]); g=calc(pair[1]["p"],pair[1]["times"])
        if f[1]==g[1] and pair[0]["label"]!=pair[1]["label"]: second_alias+=1
        if f[2]!=g[2]: curvature_separated+=1
    alias={"current_level_alias_groups":current_alias,
           "same_level_velocity_different_label_pairs":second_alias,
           "acceleration_separates_second_order_pairs":curvature_separated}
    if d.get("alias_checks")!=alias or alias!={"current_level_alias_groups":4,"same_level_velocity_different_label_pairs":4,"acceleration_separates_second_order_pairs":4}: errors.append("alias_checks")
    noise=noise_oracle()
    if d.get("noise_stress")!=noise: errors.append("noise_oracle")
    if not (noise["raw_acceleration_rms"]>noise["velocity_rms"]>0 and noise["causally_smoothed_acceleration_rms"]<noise["raw_acceleration_rms"]): errors.append("noise_order")
    if d.get("no_op_yield_are_distinct") is not True: errors.append("noop_yield_collapse")
    expected={p.name:digest(p) for p in sorted(source_dir.iterdir()) if p.is_file() and p.suffix==".py"}
    if d.get("source_sha256")!=expected: errors.append("source_sha256")
    expected_dec="PASS_CONSTRUCTION_INFORMATION_AND_NOISE_BOUNDARY" if not errors else "FAIL_CONSTRUCTION_GATE"
    if d.get("decision")!=expected_dec: errors.append("decision")
    return {"pass":not errors,"errors":errors,"decision":d.get("decision"),
            "row_count":len(rows),"transition_families":len(families),"alias_checks":alias,
            "noise_stress":noise,"source_sha256":expected}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--result",type=Path,required=True); ap.add_argument("--source-dir",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); o=audit(a.result,a.source_dir); a.out.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    print(json.dumps(o,sort_keys=True)); raise SystemExit(0 if o["pass"] else 1)


if __name__=="__main__": main()
